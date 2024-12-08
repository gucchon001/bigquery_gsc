# src/modules/gsc_handler.py

from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account

from modules.gsc_fetcher import GSCConnector
from modules.date_initializer import initialize_date_range
from utils.environment import config
from utils.date_utils import get_current_jst_datetime, format_datetime_jst
from utils.retry import insert_rows_with_retry

from utils.logging_config import get_logger
logger = get_logger(__name__)

def process_gsc_data():
    """GSC データを取得し、BigQuery に保存するメイン処理"""
    logger.info("process_gsc_data が呼び出されました。")

    # 取得する日付範囲を設定（古い日付から開始し、さらに過去に向かって進む）
    start_date, end_date = initialize_date_range()
    logger.info(f"Processing GSC data for date range: {start_date} to {end_date}")

    # GSCConnector に Config を渡す
    gsc_connector = GSCConnector(config)
    logger.info("GSCConnector を初期化しました。")

    # GSC APIの1日あたりのクォータを設定
    daily_api_limit = config.gsc_settings['daily_api_limit']
    processed_count = 0

    # 前回の処理位置を取得
    last_position = get_last_processed_position(config)
    if last_position:
        logger.info(f"Last position: date={last_position['date']}, record={last_position['record']}")
    else:
        logger.info("No previous processing position found.")

    # 処理開始日を設定
    current_date = last_position["date"] if last_position else end_date
    start_record = last_position["record"] if last_position else 0

    while current_date >= start_date and processed_count < daily_api_limit:
        try:
            remaining_quota = daily_api_limit - processed_count
            fetch_limit = config.gsc_settings['batch_size']  # 既に int として取得

            logger.debug(f"fetch_limit type: {type(fetch_limit)}, value: {fetch_limit}")

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
                    current_date -= timedelta(days=1)
                    start_record = 0
                    logger.info(f"Moving to next date: {current_date}")
                else:
                    # 同じ日の続きから
                    start_record = next_record
                    logger.info(f"Continuing on the same date: {current_date}, new start_record={start_record}")
            else:
                # データなし、次の日付へ
                current_date -= timedelta(days=1)
                start_record = 0
                logger.info(f"No records fetched. Moving to next date: {current_date}")

        except Exception as e:
            logger.error(f"Error at date {current_date}, record {start_record}: {e}", exc_info=True)
            break

    logger.info(f"Processed {processed_count} API calls in total")

'''''
    # 初回実行後にフラグを更新
    initial_run = config.gsc_settings['initial_run']
    if initial_run and not last_position:
        # 初回実行が完了したらフラグをfalseに設定
        update_initial_run_flag(config, False)
        logger.info("初回実行が完了しました。INITIAL_RUNフラグをfalseに更新しました。")
'''''

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
    client = bigquery.Client(credentials=credentials, project=config.get_config_value('BIGQUERY', 'PROJECT_ID'))
    table_id = config.progress_table_id

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
    credentials_path = config.credentials_path
    credentials = service_account.Credentials.from_service_account_file(str(credentials_path))
    client = bigquery.Client(credentials=credentials, project=config.get_config_value('BIGQUERY', 'PROJECT_ID'))
    table_id = config.progress_table_id

    query = f"""
        SELECT data_date, record_position
        FROM `{table_id}`
        WHERE is_date_completed = FALSE
        ORDER BY updated_at DESC
        LIMIT 1
    """
    try:
        query_job = client.query(query)
        results = list(query_job.result())
        if results:
            return {
                "date": results[0].data_date,  # data_dateはすでにdatetime.date型
                "record": results[0].record_position
            }
        return None
    except Exception as e:
        logger.error(f"Error fetching last processed position: {e}", exc_info=True)
        return None
