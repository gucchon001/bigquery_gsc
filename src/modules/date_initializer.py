# date_initializer.py
from datetime import datetime, timedelta
from google.cloud import bigquery
from utils.date_utils import get_current_jst_datetime  # ユーティリティ関数のインポート

# src/modules/date_initializer.py

from datetime import datetime, timedelta
from google.cloud import bigquery
from utils.date_utils import get_current_jst_datetime
from utils.environment import config

from utils.logging_config import get_logger
logger = get_logger(__name__)

def initialize_date_range():
    """
    初回実行か毎日の実行かに応じて日付範囲を生成します。
    """
    initial_run = config.get_config_value('GSC_INITIAL', 'INITIAL_RUN', default='true').lower() == 'true'
    if initial_run:
        days = int(config.get_config_value('GSC_DAILY', 'INITIAL_FETCH_DAYS', default=365))
        logger.info(f"初回実行: 過去{days}日分のデータを取得します。")
    else:
        days = int(config.get_config_value('GSC_DAILY', 'DAILY_FETCH_DAYS', default=3))
        logger.info(f"毎日実行: 過去{days}日分のデータを取得します。")
    
    today = get_current_jst_datetime().date()
    start_date = today - timedelta(days=days)
    end_date = today - timedelta(days=2)  # GSCの制限により2日前まで
    
    return start_date, end_date

def get_next_date_range(config):
    """
    BigQueryの進捗状況を元に、次のデータ範囲を決定する。
    """
    client = bigquery.Client()
    table_id = f"{config.config['BIGQUERY']['PROJECT_ID']}.{config.config['BIGQUERY']['DATASET_ID']}.T_progress_tracking"

    query = f"""
        SELECT data_date, record_position
        FROM `{table_id}`
        WHERE is_date_completed = FALSE
        ORDER BY data_date DESC
        LIMIT 1
    """
    query_job = client.query(query)
    result = list(query_job.result())

    if result:
        last_date = result[0]["data_date"]
        last_row = result[0]["record_position"] or 0
        return last_date, last_row
    else:
        # 進捗がない場合、最新の日付から開始
        today = get_current_jst_datetime().date()  # 現在の日本時間を使用
        return today, 0

def get_date_range_for_fetch(start_date_str=None, end_date_str=None):
    """
    開始日と終了日を指定された日付で設定。
    指定がない場合はデフォルトで2日前のデータを取得対象とする。
    """
    today = get_current_jst_datetime().date()  # 現在の日本時間を使用

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    else:
        start_date = today - timedelta(days=2)

    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    else:
        end_date = start_date
    return start_date, end_date
