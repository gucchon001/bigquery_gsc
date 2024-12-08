# src/utils.py

import time
from google.auth.exceptions import RefreshError
from google.cloud import bigquery
import logging

def insert_rows_with_retry(client: bigquery.Client, table_id: str, rows_to_insert: list, logger: logging.Logger,
                           max_retries: int = 5, retry_delay: int = 10) -> None:
    """
    BigQueryへのデータ挿入をリトライロジック付きで実行します。

    Args:
        client (bigquery.Client): BigQuery クライアント
        table_id (str): 挿入先のテーブルID
        rows_to_insert (list): 挿入する行データのリスト
        logger (logging.Logger): ロガー
        max_retries (int): 最大リトライ回数
        retry_delay (int): リトライ間の待機時間（秒）

    Raises:
        Exception: 最大リトライ回数に達した場合
    """
    for attempt in range(1, max_retries + 1):
        try:
            errors = client.insert_rows_json(table_id, rows_to_insert)
            if not errors:
                logger.info(f"Successfully inserted {len(rows_to_insert)} rows into {table_id}.")
                return
            else:
                logger.error(f"BigQuery insertion errors (Attempt {attempt}): {errors}")
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        except RefreshError as e:
            logger.error(f"Authentication error occurred (Attempt {attempt}): {e}")
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Unexpected error during BigQuery insertion (Attempt {attempt}): {e}")
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    else:
        logger.critical(f"Failed to insert rows into {table_id} after {max_retries} attempts.")
        raise Exception("BigQuery insertion failed after maximum retries.")
