# src/modules/gsc_handler.py

from datetime import datetime, timedelta
from google.cloud import bigquery
from google.api_core.exceptions import BadRequest
from google.oauth2 import service_account

from modules.gsc_fetcher import GSCConnector
from utils.environment import config
from utils.date_utils import get_current_jst_datetime, format_datetime_jst
from utils.webhook_notifier import send_error_notification, send_success_notification

from utils.logging_config import get_logger
logger = get_logger(__name__)

def _get_bigquery_credentials(config):
    """BigQuery用の認証情報を取得（Cloud Run環境対応）"""
    credentials_path = config.credentials_path
    
    if credentials_path:
        # ファイルから読み込む（Secret Managerから取得した一時ファイルまたはローカルファイル）
        return service_account.Credentials.from_service_account_file(str(credentials_path))
    else:
        # Cloud Run環境など、ファイルパスが指定されていない場合はデフォルトの認証情報を使用
        from google.auth import default
        credentials, _ = default()
        logger.info("Using default Google credentials for BigQuery (e.g., Cloud Run service account)")
        return credentials

def cleanup_progress_table(config, retention_minutes: int = 90) -> None:
    """進捗テーブルの古い不要行を削除します。

    - ストリーミングバッファの制約を避けるため、JST現在時刻から retention_minutes 分より古い行のみ対象
    - `record_position = 0` の行を削除
    - 各 `data_date` で最新(`updated_at`最大)以外の履歴行を削除
    """
    credentials = _get_bigquery_credentials(config)
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')
    progress_table_id = config.get_config_value('BIGQUERY', 'PROGRESS_TABLE_ID')

    client = bigquery.Client(credentials=credentials, project=project_id)
    table_id = f"{project_id}.{dataset_id}.{progress_table_id}"

    # しきい値（JST）
    threshold_dt = get_current_jst_datetime() - timedelta(minutes=retention_minutes)
    threshold_str = format_datetime_jst(threshold_dt)

    # 1) record_position = 0 の古い行を削除
    delete_zero_pos = f"""
        DELETE FROM `{table_id}`
        WHERE record_position = 0
          AND updated_at < @threshold
    """

    # 2) 同一日で最新でない古い履歴行を削除（しきい値より古いもののみ）
    delete_non_latest = f"""
        DELETE FROM `{table_id}` AS t
        WHERE updated_at < @threshold
          AND NOT EXISTS (
            SELECT 1
            FROM (
              SELECT data_date, MAX(updated_at) AS max_updated_at
              FROM `{table_id}`
              WHERE updated_at < @threshold
              GROUP BY data_date
            ) AS latest
            WHERE latest.data_date = t.data_date
              AND latest.max_updated_at = t.updated_at
          )
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("threshold", "DATETIME", threshold_str)
        ]
    )

    try:
        logger.info("Cleaning progress table: deleting old zero-position rows…")
        client.query(delete_zero_pos, job_config=job_config).result()
        logger.info("Cleaning progress table: deleting old non-latest history rows…")
        client.query(delete_non_latest, job_config=job_config).result()
        logger.info("Progress table cleanup finished.")
    except BadRequest as e:
        message = str(e)
        if "would affect rows in the streaming buffer" in message:
            logger.info("Cleanup skipped due to streaming buffer: will retry on next run.")
            return
        logger.error(f"Progress table cleanup failed: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Progress table cleanup failed: {e}", exc_info=True)
        
def process_gsc_data():
    """GSC データを取得し、BigQuery に保存するメイン処理"""
    logger.info("process_gsc_data が呼び出されました。")

    # 初期実行フラグの取得
    initial_run = config.gsc_settings['initial_run']

    # GSCConnector の初期化
    gsc_connector = GSCConnector(config)
    logger.info("GSCConnector を初期化しました。")

    # GSC APIの1日あたりのクォータを設定
    daily_api_limit = config.gsc_settings['daily_api_limit']
    processed_count = 0

    # 新しい日付範囲を設定
    end_date = datetime.today().date() - timedelta(days=2)  # GSCの制限により2日前まで
    
    if initial_run:
        logger.info("INITIAL_RUN=true: 進捗テーブルを確認し、未処理の日付のデータを取得します。")
        start_date = end_date - timedelta(days=config.gsc_settings['initial_fetch_days'] - 1)
        # 取得対象の日付リストを作成
        date_list = [end_date - timedelta(days=i) for i in range(config.gsc_settings['initial_fetch_days'])]
        
        # 進捗テーブルから `is_date_completed=true` の日付を取得
        completed_dates = get_completed_dates(config, date_list)
        
        # 未完了の日付をフィルタリング
        date_list = [date for date in date_list if date not in completed_dates]
        logger.info(f"Fetching data for dates: {date_list}")
    else:
        logger.info("INITIAL_RUN=false: 最新のデータを取得します。")
        start_date = end_date - timedelta(days=config.gsc_settings['daily_fetch_days'] - 1)
        date_list = [end_date - timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        logger.info(f"Processing GSC data for date range: {start_date} to {end_date}")

    # 各日付に対してデータを取得・処理
    for current_date in date_list:
        # 完了済みの日付をスキップ
        is_completed = check_if_date_completed(config, current_date)
        if is_completed:
            logger.info(f"Date {current_date} is already completed. Skipping.")
            continue

        # 日付ごとのレコード数を初期化
        date_total_records = 0
        start_record = 0
        while processed_count < daily_api_limit:
            try:
                fetch_limit = config.gsc_settings['batch_size']
                logger.info(f"Fetching records from {current_date}, start_record={start_record}, limit={fetch_limit}")
                records, next_record = gsc_connector.fetch_records(
                    date=str(current_date),
                    start_record=start_record,
                    limit=fetch_limit
                )
                logger.info(f"Fetched {len(records)} records.")

                if records:
                    gsc_connector.insert_to_bigquery(records, str(current_date))
                    logger.info(f"Inserted {len(records)} records into BigQuery.")
                    processed_count += 1
                    date_total_records += len(records)  # 日付ごとのレコード数を累積

                    # 進捗保存（アップサート）
                    save_processing_position(config, {
                        "date": current_date,
                        "record": next_record,
                        "is_date_completed": len(records) < fetch_limit
                    })
                    logger.info(f"Progress saved for date {current_date}.")

                    if len(records) < fetch_limit:
                        # 日付完了、次の日付へ
                        logger.info(f"All records for date {current_date} have been processed.")
                        # 日付ごとのレコード数を記録
                        daily_record_counts[str(current_date)] = date_total_records
                        break
                    else:
                        # 同じ日の続きから
                        start_record = next_record
                        logger.info(f"Continuing on the same date: {current_date}, new start_record={start_record}")
                else:
                    # データなし、次の日付へ（0件でも完了としてマーク）
                    logger.info(f"No records fetched for date {current_date}. Marking as completed and moving to next date.")
                    save_processing_position(config, {
                        "date": current_date,
                        "record": 0,
                        "is_date_completed": True
                    })
                    logger.info(f"Progress saved for date {current_date} (0 records).")
                    break

            except Exception as e:
                logger.error(f"Error at date {current_date}, record {start_record}: {e}", exc_info=True)
                # エラー通知を送信
                send_error_notification(
                    error=e,
                    error_type="GSC Data Processing Error",
                    context={
                        "date": str(current_date),
                        "start_record": start_record,
                        "processed_count": processed_count
                    }
                )
                break

    logger.info(f"Processed {processed_count} API calls in total")

    # 初回実行後にフラグを更新
    if initial_run:
        update_initial_run_flag(config, False)
        logger.info("初回実行が完了しました。INITIAL_RUNフラグをfalseに更新しました。")
    
    # 正常終了時の通知を送信
    try:
        logger.info("正常終了時の通知送信処理を開始します。")
        # 日ごとの統計情報をリスト形式に変換
        daily_stats = [
            {"date": date, "records": count}
            for date, count in sorted(daily_record_counts.items())
        ]
        
        logger.info(f"通知送信: daily_stats={daily_stats}, processed_count={processed_count}")
        
        # 成功通知を送信
        result = send_success_notification(
            message=f"GSCデータの取得とBigQueryへの保存が正常に完了しました。",
            daily_stats=daily_stats if daily_stats else None,
            context={
                "processed_api_calls": processed_count,
                "daily_api_limit": daily_api_limit,
                "date_range": f"{start_date} to {end_date}",
                "initial_run": initial_run
            }
        )
        logger.info(f"成功通知の送信結果: {result}")
    except Exception as e:
        logger.error(f"成功通知の送信に失敗しました: {e}", exc_info=True)

def get_completed_dates(config, date_list):
    """進捗テーブルから `is_date_completed=true` の日付を取得します。

    Args:
        config: Config クラスのインスタンス
        date_list (list): チェック対象の日付リスト

    Returns:
        list: 完了済みの日付リスト
    """

    credentials = _get_bigquery_credentials(config)
    client = bigquery.Client(credentials=credentials, project=config.get_config_value('BIGQUERY', 'PROJECT_ID'))
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')      # 'bigquery-jukust'
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')      # 'past_gsc_202411'
    progress_table_id = config.get_config_value('BIGQUERY', 'PROGRESS_TABLE_ID')  # 'T_progress_tracking'
    
    table_id = f"{project_id}.{dataset_id}.{progress_table_id}"        # 'bigquery-jukust.past_gsc_202411.T_progress_tracking'

    query = f"""
        WITH ranked AS (
            SELECT
                data_date,
                is_date_completed,
                updated_at,
                ROW_NUMBER() OVER (
                    PARTITION BY data_date
                    ORDER BY is_date_completed DESC, updated_at DESC
                ) AS rn
            FROM `{table_id}`
            WHERE (record_position > 0 OR is_date_completed = TRUE)
              AND data_date IN UNNEST(@dates)
        )
        SELECT data_date
        FROM ranked
        WHERE rn = 1 AND is_date_completed = TRUE
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("dates", "DATE", date_list)
        ]
    )

    try:
        query_job = client.query(query, job_config=job_config)
        results = list(query_job.result())
        completed_dates = [row.data_date for row in results]
        logger.info(f"Completed dates: {completed_dates}")
        return completed_dates
    except Exception as e:
        logger.error(f"Error fetching completed dates: {e}", exc_info=True)
        return []

def check_if_date_completed(config, date):
    """指定された日付が進捗テーブルで完了しているかを確認します。"""
    credentials = _get_bigquery_credentials(config)
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')      # 'bigquery-jukust'
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')      # 'past_gsc_202411'
    progress_table_id = config.get_config_value('BIGQUERY', 'PROGRESS_TABLE_ID')  # 'T_progress_tracking'
    
    client = bigquery.Client(credentials=credentials, project=project_id)
    table_id = f"{project_id}.{dataset_id}.{progress_table_id}"        # 'bigquery-jukust.past_gsc_202411.T_progress_tracking'


    query = f"""
        WITH ranked AS (
            SELECT
                data_date,
                is_date_completed,
                updated_at,
                ROW_NUMBER() OVER (
                    PARTITION BY data_date
                    ORDER BY is_date_completed DESC, updated_at DESC
                ) AS rn
            FROM `{table_id}`
            WHERE (record_position > 0 OR is_date_completed = TRUE) AND data_date = @data_date
        )
        SELECT COUNTIF(is_date_completed = TRUE AND rn = 1) AS count
        FROM ranked
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("data_date", "DATE", date)
        ]
    )

    try:
        query_job = client.query(query, job_config=job_config)
        result = query_job.result().to_dataframe()
        count = result['count'][0]
        return count > 0
    except Exception as e:
        logger.error(f"Error checking if date {date} is completed: {e}", exc_info=True)
        return False

def update_initial_run_flag(config, flag: bool):
    """
    settings.iniのINITIAL_RUNフラグを更新します。

    Args:
        config: Config クラスのインスタンス
        flag (bool): フラグの新しい値
    """
    import configparser

    settings_path = config.get_config_file('settings.ini')
    parser = configparser.ConfigParser()
    parser.read(settings_path, encoding='utf-8')

    if 'GSC_INITIAL' not in parser.sections():
        parser.add_section('GSC_INITIAL')

    parser.set('GSC_INITIAL', 'INITIAL_RUN', str(flag).lower())

    with open(settings_path, 'w', encoding='utf-8') as configfile:
        parser.write(configfile)

    logger.info(f"settings.ini の INITIAL_RUN を {flag} に更新しました。")

def save_processing_position(config, position):
    """処理位置を保存（アップサート操作）"""
    credentials = _get_bigquery_credentials(config)
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')      # 'bigquery-jukust'
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')      # 'past_gsc_202411'
    progress_table_id = config.get_config_value('BIGQUERY', 'PROGRESS_TABLE_ID')  # 'T_progress_tracking'

    client = bigquery.Client(credentials=credentials, project=project_id)
    table_id = f"{project_id}.{dataset_id}.{progress_table_id}"        # 'bigquery-jukust.past_gsc_202411.T_progress_tracking'

    logger.debug(f"Constructed Table ID: {table_id}")  # デバッグログの追加

    updated_at_jst = format_datetime_jst(get_current_jst_datetime())

    data_date = str(position["date"])
    record_position = position["record"]
    is_date_completed = position["is_date_completed"]

    # UPDATE/MERGE はストリーミングバッファに阻害されるため、追記INSERTに変更
    insert_query = f"""
        INSERT INTO `{table_id}` (data_date, record_position, is_date_completed, updated_at)
        VALUES (@data_date, @record_position, @is_date_completed, @updated_at)
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("data_date", "DATE", data_date),
            bigquery.ScalarQueryParameter("record_position", "INT64", record_position),
            bigquery.ScalarQueryParameter("is_date_completed", "BOOL", is_date_completed),
            bigquery.ScalarQueryParameter("updated_at", "DATETIME", updated_at_jst)
        ]
    )

    try:
        query_job = client.query(insert_query, job_config=job_config)
        query_job.result()  # 完了まで待機
        logger.info(f"Progress updated for date {data_date}.")
    except Exception as e:
        logger.error(f"Failed to save processing position for {data_date}: {e}", exc_info=True)
        raise

def get_last_processed_position(config):
    """最後に処理したポジションを取得"""
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')      # 'bigquery-jukust'
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')      # 'past_gsc_202411'
    progress_table_id = config.get_config_value('BIGQUERY', 'PROGRESS_TABLE_ID')  # 'T_progress_tracking'
    
    table_id = f"{project_id}.{dataset_id}.{progress_table_id}"        # 'bigquery-jukust.past_gsc_202411.T_progress_tracking'

    credentials = _get_bigquery_credentials(config)
    client = bigquery.Client(credentials=credentials, project=project_id)

    query = f"""
        SELECT data_date, record_position, is_date_completed
        FROM `{table_id}`
        WHERE record_position > 0
        ORDER BY updated_at DESC
        LIMIT 1
    """
    try:
        query_job = client.query(query)
        results = list(query_job.result())
        if results:
            return {
                "date": results[0].data_date,  # data_dateはすでにdatetime.date型
                "record": results[0].record_position,
                "is_date_completed": results[0].is_date_completed
            }
        return None
    except Exception as e:
        logger.error(f"Error fetching last processed position: {e}", exc_info=True)
        return None