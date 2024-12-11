# src/modules/gsc_handler.py

from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account

from modules.gsc_fetcher import GSCConnector
from utils.environment import config
from utils.date_utils import get_current_jst_datetime, format_datetime_jst

from utils.logging_config import get_logger
logger = get_logger(__name__)

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

    if initial_run:
        logger.info("INITIAL_RUN=true: 進捗テーブルを確認し、未処理の日付のデータを取得します。")
        # 最新100日分のデータを取得対象
        end_date = datetime.today().date() - timedelta(days=2)  # GSCの制限により2日前まで
        start_date = end_date - timedelta(days=config.gsc_settings['initial_fetch_days'] - 1)

        # 取得対象の日付リストを作成
        date_list = [end_date - timedelta(days=i) for i in range(config.gsc_settings['initial_fetch_days'])]
        
        # 進捗テーブルから `is_date_completed=true` の日付を取得
        completed_dates = get_completed_dates(config, date_list)
        
        # 未完了の日付をフィルタリング
        date_list = [date for date in date_list if date not in completed_dates]
        logger.info(f"Fetching data for dates: {date_list}")

        # 各日付に対してデータを取得・処理
        for current_date in date_list:
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
                        processed_count += 1  # API呼び出し回数をカウント

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
                            break
                        else:
                            # 同じ日の続きから
                            start_record = next_record
                            logger.info(f"Continuing on the same date: {current_date}, new start_record={start_record}")
                    else:
                        # データなし、次の日付へ
                        logger.info(f"No records fetched for date {current_date}. Moving to next date.")
                        break

                except Exception as e:
                    logger.error(f"Error at date {current_date}, record {start_record}: {e}", exc_info=True)
                    break

    else:
        logger.info("INITIAL_RUN=false: 進捗テーブルから最後の処理位置を取得し、データを継続的に取得します。")
        # 前回の処理位置を取得
        last_position = get_last_processed_position(config)
        if last_position:
            current_date = last_position["date"]
            start_record = last_position["record"]
            logger.info(f"Last position: date={current_date}, record={start_record}, is_completed={last_position['is_date_completed']}")
        else:
            logger.info("No previous processing position found. Fetching latest 100 days of data.")
            # 処理開始日を設定
            end_date = datetime.today().date() - timedelta(days=2)  # GSCの制限により2日前まで
            start_date = end_date - timedelta(days=config.gsc_settings['daily_fetch_days'] - 1)
            current_date = end_date
            start_record = 0

        # 処理対象の日付範囲を設定
        if last_position and not last_position["is_date_completed"]:
            # 未完了のデータがある場合、その日付から再開
            start_date = current_date
        else:
            # 新しい日付範囲を設定
            end_date = datetime.today().date() - timedelta(days=2)
            start_date = end_date - timedelta(days=config.gsc_settings['daily_fetch_days'] - 1)

        logger.info(f"Processing GSC data for date range: {start_date} to {current_date}")

        # 取得対象の日付リストを作成
        date_list = [current_date - timedelta(days=i) for i in range((current_date - start_date).days + 1)]

        # 各日付に対してデータを取得・処理
        for current_date in date_list:
            # `is_date_completed=true` の日付はスキップ
            is_completed = check_if_date_completed(config, current_date)
            if is_completed:
                logger.info(f"Date {current_date} is already completed. Skipping.")
                continue

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
                        processed_count += 1  # API呼び出し回数をカウント

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
                            break
                        else:
                            # 同じ日の続きから
                            start_record = next_record
                            logger.info(f"Continuing on the same date: {current_date}, new start_record={start_record}")
                    else:
                        # データなし、次の日付へ
                        logger.info(f"No records fetched for date {current_date}. Moving to next date.")
                        break

                except Exception as e:
                    logger.error(f"Error at date {current_date}, record {start_record}: {e}", exc_info=True)
                    break

    logger.info(f"Processed {processed_count} API calls in total")

    # 初回実行後にフラグを更新
    if initial_run:
        update_initial_run_flag(config, False)
        logger.info("初回実行が完了しました。INITIAL_RUNフラグをfalseに更新しました。")

def get_completed_dates(config, date_list):
    """進捗テーブルから `is_date_completed=true` の日付を取得します。

    Args:
        config: Config クラスのインスタンス
        date_list (list): チェック対象の日付リスト

    Returns:
        list: 完了済みの日付リスト
    """

    credentials_path = config.credentials_path
    credentials = service_account.Credentials.from_service_account_file(str(credentials_path))
    client = bigquery.Client(credentials=credentials, project=config.get_config_value('BIGQUERY', 'PROJECT_ID'))
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')      # 'bigquery-jukust'
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')      # 'past_gsc_202411'
    progress_table_id = config.get_config_value('BIGQUERY', 'PROGRESS_TABLE_ID')  # 'T_progress_tracking'
    
    table_id = f"{project_id}.{dataset_id}.{progress_table_id}"        # 'bigquery-jukust.past_gsc_202411.T_progress_tracking'

    query = f"""
        SELECT data_date
        FROM `{table_id}`
        WHERE is_date_completed = TRUE
          AND data_date IN UNNEST(@dates)
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
    credentials_path = config.credentials_path
    credentials = service_account.Credentials.from_service_account_file(str(credentials_path))
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')      # 'bigquery-jukust'
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')      # 'past_gsc_202411'
    progress_table_id = config.get_config_value('BIGQUERY', 'PROGRESS_TABLE_ID')  # 'T_progress_tracking'
    
    client = bigquery.Client(credentials=credentials, project=project_id)
    table_id = f"{project_id}.{dataset_id}.{progress_table_id}"        # 'bigquery-jukust.past_gsc_202411.T_progress_tracking'


    query = f"""
        SELECT COUNT(*) as count
        FROM `{table_id}`
        WHERE data_date = @data_date
          AND is_date_completed = TRUE
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
    credentials_path = config.credentials_path
    credentials = service_account.Credentials.from_service_account_file(str(credentials_path))
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

    # MERGE ステートメントを使用してアップサートを実行
    merge_query = f"""
        MERGE `{table_id}` T
        USING (SELECT @data_date AS data_date) S
        ON T.data_date = S.data_date
        WHEN MATCHED THEN
            UPDATE SET 
                record_position = @record_position,
                is_date_completed = @is_date_completed,
                updated_at = @updated_at
        WHEN NOT MATCHED THEN
            INSERT (data_date, record_position, is_date_completed, updated_at)
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
        query_job = client.query(merge_query, job_config=job_config)
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

    credentials_path = config.credentials_path
    credentials = service_account.Credentials.from_service_account_file(str(credentials_path))
    client = bigquery.Client(credentials=credentials, project=project_id)

    query = f"""
        SELECT data_date, record_position, is_date_completed
        FROM `{table_id}`
        ORDER BY data_date DESC, updated_at DESC
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