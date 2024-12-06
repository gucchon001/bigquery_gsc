#date_initializer.py
from datetime import datetime, timedelta
from google.cloud import bigquery

def initialize_date_range_past_year():
    """
    過去1年間の日付を新しい順にリストとして生成
    """
    today = datetime.now().date()
    one_year_ago = today - timedelta(days=1000)  # 過去1年分を対象
    return [today - timedelta(days=i) for i in range((today - one_year_ago).days + 1)]

def get_next_date_range(config):
    """
    BigQueryの進捗状況を元に、次のデータ範囲を決定する。
    """
    client = bigquery.Client()
    table_id = f"{config.config['BIGQUERY']['PROJECT_ID']}.{config.config['BIGQUERY']['DATASET_ID']}.T_progress_tracking"

    query = f"""
        SELECT data_date, last_processed_row
        FROM `{table_id}`
        WHERE batch_completed = FALSE
        ORDER BY data_date DESC
        LIMIT 1
    """
    query_job = client.query(query)
    result = list(query_job.result())

    if result:
        last_date = result[0]["data_date"]
        last_row = result[0]["last_processed_row"] or 0
        return last_date, last_row
    else:
        # 進捗がない場合、最新の日付から開始
        today = datetime.now().date()
        return today, 0


def get_date_range_for_fetch(start_date_str=None, end_date_str=None):
    """
    開始日と終了日を指定された日付で設定。
    指定がない場合はデフォルトで2日前のデータを取得対象とする。
    """
    today = datetime.now().date()

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    else:
        start_date = today - timedelta(days=2)

    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    else:
        end_date = start_date
    return start_date, end_date