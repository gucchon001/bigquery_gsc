from google.cloud import bigquery
from google.oauth2 import service_account

from utils.environment import config


def main() -> None:
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')
    progress_table_id = config.get_config_value('BIGQUERY', 'PROGRESS_TABLE_ID')
    table_id = f"{project_id}.{dataset_id}.{progress_table_id}"

    credentials_path = config.credentials_path
    credentials = service_account.Credentials.from_service_account_file(str(credentials_path))
    client = bigquery.Client(credentials=credentials, project=project_id)

    print(f"Inspecting table: {table_id}")

    # 1) 全体件数
    q_total = f"SELECT COUNT(*) AS total_rows FROM `{table_id}`"
    total_rows = list(client.query(q_total).result())[0].total_rows
    print(f"Total rows: {total_rows}")

    # 2) data_date ごとの件数と最新状態
    q_by_date = f"""
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
            FROM `{table_id}`
        )
        SELECT
            data_date,
            COUNT(*) AS rows_per_date,
            SUM(CASE WHEN record_position = 0 THEN 1 ELSE 0 END) AS zero_pos_rows,
            SUM(CASE WHEN is_date_completed THEN 1 ELSE 0 END) AS true_rows,
            SUM(CASE WHEN NOT is_date_completed THEN 1 ELSE 0 END) AS false_rows,
            MAX(IF(rn = 1, CAST(is_date_completed AS INT64), NULL)) AS latest_is_true,
            MAX(IF(rn = 1, record_position, NULL)) AS latest_record_position,
            MAX(IF(rn = 1, updated_at, NULL)) AS latest_updated_at
        FROM ranked
        GROUP BY data_date
        ORDER BY data_date DESC
    """
    print("\nPer-date summary (latest status included):")
    for row in client.query(q_by_date).result():
        print(
            f"{row.data_date} | rows={row.rows_per_date} (0pos={row.zero_pos_rows}, true={row.true_rows}, false={row.false_rows}) "
            f"| latest: is_true={bool(row.latest_is_true)} pos={row.latest_record_position} at={row.latest_updated_at}"
        )

    # 3) 直近の挿入50行
    q_recent = f"""
        SELECT data_date, record_position, is_date_completed, updated_at
        FROM `{table_id}`
        ORDER BY updated_at DESC
        LIMIT 50
    """
    print("\nMost recent 50 rows:")
    for row in client.query(q_recent).result():
        print(
            f"{row.updated_at} | {row.data_date} | pos={row.record_position} | completed={row.is_date_completed}"
        )


if __name__ == "__main__":
    main()


