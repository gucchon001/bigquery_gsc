import configparser
from google.cloud import bigquery
from google.oauth2 import service_account

from utils.environment import config


def drop_table_if_exists(client: bigquery.Client, table_fqn: str, location: str) -> None:
    try:
        client.get_table(table_fqn)
    except Exception:
        return
    client.delete_table(table_fqn, not_found_ok=True)


def create_empty_nonpartitioned(client: bigquery.Client, table_fqn: str, location: str) -> None:
    ddl = f"""
        CREATE TABLE `{table_fqn}` (
            data_date DATE,
            record_position INT64,
            is_date_completed BOOL,
            updated_at DATETIME
        )
    """
    client.query(ddl, location=location).result()


def backfill_latest_per_date(client: bigquery.Client, src_fqn: str, dst_fqn: str, location: str) -> None:
    sql = f"""
        INSERT INTO `{dst_fqn}` (data_date, record_position, is_date_completed, updated_at)
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
            FROM `{src_fqn}`
            WHERE record_position > 0 AND data_date IS NOT NULL
        )
        SELECT data_date, record_position, is_date_completed, updated_at
        FROM ranked
        WHERE rn = 1
    """
    client.query(sql, location=location).result()


def count_rows(client: bigquery.Client, table_fqn: str, location: str) -> int:
    q = f"SELECT COUNT(*) AS cnt FROM `{table_fqn}`"
    return list(client.query(q, location=location).result())[0].cnt


def update_settings_ini(new_table: str) -> None:
    settings_path = config.get_config_file('settings.ini')
    parser = configparser.ConfigParser()
    parser.read(settings_path, encoding='utf-8')
    parser.set('BIGQUERY', 'progress_table_id', new_table)
    with open(settings_path, 'w', encoding='utf-8') as f:
        parser.write(f)


def main() -> None:
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')
    location = config.get_config_value('BIGQUERY', 'LOCATION', 'asia-northeast1')
    src_table = f"{project_id}.{dataset_id}.T_progress_tracking"
    dst_name = "T_progress_tracking_v2_rebuilt"
    dst_table = f"{project_id}.{dataset_id}.{dst_name}"

    credentials_path = config.credentials_path
    credentials = service_account.Credentials.from_service_account_file(str(credentials_path))
    client = bigquery.Client(credentials=credentials, project=project_id)

    # Rebuild
    drop_table_if_exists(client, dst_table, location)
    create_empty_nonpartitioned(client, dst_table, location)
    backfill_latest_per_date(client, src_table, dst_table, location)

    # Counts
    # Old latest-per-date count
    q_old = f"""
    WITH ranked AS (
      SELECT data_date, is_date_completed, updated_at,
             ROW_NUMBER() OVER (PARTITION BY data_date ORDER BY is_date_completed DESC, updated_at DESC) rn
      FROM `{src_table}`
      WHERE record_position > 0 AND data_date IS NOT NULL
    )
    SELECT COUNTIF(rn=1) AS cnt FROM ranked
    """
    old_cnt = list(client.query(q_old, location=location).result())[0].cnt
    new_cnt = count_rows(client, dst_table, location)

    # Switch settings.ini
    update_settings_ini(dst_name)

    print(f"rebuilt_table={dst_table}")
    print(f"old_latest_per_date={old_cnt}")
    print(f"new_v2_rows={new_cnt}")
    print("match=" + str(old_cnt == new_cnt))


if __name__ == "__main__":
    main()


