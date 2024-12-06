#gsc_handler.py
from datetime import datetime, timedelta
from google.cloud import bigquery
from modules.gsc_fetcher import GSCConnector
from modules.date_initializer import get_date_range_for_fetch
from utils.logging_config import get_logger
from utils.environment import EnvironmentUtils

def process_gsc_data():
    """GSC データを取得し、BigQuery に保存するメイン処理"""
    # 取得する日付範囲を設定
    start_date, end_date = get_date_range_for_fetch("2024-11-17", "2023-01-01")
    get_logger.info(f"Processing GSC data for date range: {start_date} to {end_date}")

    gsc_connector = GSCConnector()  # config を渡さないように変更
    daily_api_limit = 25000
    processed_count = 0

    # 前回の処理位置を取得
    last_position = get_last_processed_position()
    current_date = last_position["date"] if last_position else start_date
    start_record = last_position["record"] if last_position else 0

    while current_date >= end_date and processed_count < daily_api_limit:
        try:
            remaining_quota = daily_api_limit - processed_count
            fetch_limit = min(25000, remaining_quota)  # GSC APIの制限に合わせる

            records, next_record = gsc_connector.fetch_records(
                date=str(current_date),
                start_record=start_record,
                limit=fetch_limit
            )

            if records:
                gsc_connector.insert_to_bigquery(records)
                processed_count += len(records)
                
                # 進捗保存
                save_processing_position({
                    "date": current_date,
                    "record": start_record + len(records),
                    "is_date_completed": len(records) < fetch_limit
                })

                if len(records) < fetch_limit:
                    # 日付完了、次の日付へ
                    current_date -= timedelta(days=1)
                    start_record = 0
                else:
                    # 同じ日の続きから
                    start_record += len(records)
            else:
                # データなし、次の日付へ
                current_date -= timedelta(days=1)
                start_record = 0

        except Exception as e:
            get_logger.error(f"Error at date {current_date}, record {start_record}: {e}")
            break

    get_logger.info(f"Processed {processed_count} records in total")

def save_processing_position(position):
    """処理位置を保存"""
    client = bigquery.Client()
    table_id = f"{EnvironmentUtils.get_config_value('BIGQUERY', 'PROJECT_ID')}." \
               f"{EnvironmentUtils.get_config_value('BIGQUERY', 'DATASET_ID')}." \
               f"{EnvironmentUtils.get_config_value('BIGQUERY', 'PROGRESS_TABLE_ID')}"

    rows_to_insert = [{
        "data_date": str(position["date"]),
        "record_position": position["record"],
        "is_date_completed": position["is_date_completed"],
        "updated_at": datetime.utcnow().isoformat()
    }]
    
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        raise RuntimeError(f"Failed to save processing position: {errors}")

def get_last_processed_position():
    """最後に処理したポジションを取得"""
    client = bigquery.Client()
    table_id = f"{EnvironmentUtils.get_config_value('BIGQUERY', 'PROJECT_ID')}." \
               f"{EnvironmentUtils.get_config_value('BIGQUERY', 'DATASET_ID')}." \
               f"{EnvironmentUtils.get_config_value('BIGQUERY', 'PROGRESS_TABLE_ID')}"
    
    query = f"""
        SELECT data_date, record_position
        FROM `{table_id}`
        WHERE is_date_completed = false
        ORDER BY updated_at DESC
        LIMIT 1
    """
    results = list(client.query(query).result())
    if results:
        return {
            "date": results[0].data_date,  # data_dateはすでにdatetime.date型
            "record": results[0].record_position
        }
    return None