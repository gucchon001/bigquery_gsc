from google.cloud import bigquery
from google.oauth2 import service_account

from utils.environment import config


def create_progress_tracking_v2(client: bigquery.Client, project_id: str, dataset_id: str,
                                old_table: str, new_table: str, location: str) -> None:
    src = f"{project_id}.{dataset_id}.{old_table}"
    dst = f"{project_id}.{dataset_id}.{new_table}"

    # 1) 先に空テーブルをスキーマ指定で作成（必要なら）
    ddl_create = f"""
        CREATE TABLE IF NOT EXISTS `{dst}` (
            data_date DATE,
            record_position INT64,
            is_date_completed BOOL,
            updated_at DATETIME
        )
        PARTITION BY data_date
    """
    client.query(ddl_create, location=location).result()

    # 2) 既存テーブルから各日付の最新1行を投入（record_position>0 を優先）
    insert_sql = f"""
        INSERT INTO `{dst}` (data_date, record_position, is_date_completed, updated_at)
        WITH ranked AS (
            SELECT
                data_date,
                record_position,
                is_date_completed,
                updated_at,
                ROW_NUMBER() OVER (
                    PARTITION BY data_date
                    ORDER BY is_date_completed DESC, updated_at DESC
                ) AS rn
            FROM `{src}`
            WHERE record_position > 0 AND data_date IS NOT NULL
        )
        SELECT data_date, record_position, is_date_completed, updated_at
        FROM ranked
        WHERE rn = 1
    """
    client.query(insert_sql, location=location).result()


def count_rows(client: bigquery.Client, table_fqn: str, location: str) -> int:
    q = f"SELECT COUNT(*) AS cnt FROM `{table_fqn}`"
    return list(client.query(q, location=location).result())[0].cnt


def main() -> None:
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')
    old_table = config.get_config_value('BIGQUERY', 'PROGRESS_TABLE_ID')  # e.g., T_progress_tracking
    new_table = f"{old_table}_v2"
    location = config.get_config_value('BIGQUERY', 'LOCATION', 'asia-northeast1')

    credentials_path = config.credentials_path
    credentials = service_account.Credentials.from_service_account_file(str(credentials_path))
    client = bigquery.Client(credentials=credentials, project=project_id)

    create_progress_tracking_v2(client, project_id, dataset_id, old_table, new_table, location)

    dst = f"{project_id}.{dataset_id}.{new_table}"
    total = count_rows(client, dst, location)
    print(f"Created and backfilled: {dst}")
    print(f"Total rows (latest per date): {total}")


if __name__ == "__main__":
    main()


