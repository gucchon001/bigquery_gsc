import configparser
from pathlib import Path

from google.cloud import bigquery
from google.oauth2 import service_account

from utils.environment import config


def create_partitioned_clustered_table(client: bigquery.Client, project_id: str, dataset_id: str,
                                       old_table: str, new_table: str, location: str) -> None:
    src = f"{project_id}.{dataset_id}.{old_table}"
    dst = f"{project_id}.{dataset_id}.{new_table}"

    # CREATE TABLE ... AS SELECT with partition+clustering
    ddl = f"""
        CREATE TABLE `{dst}`
        PARTITION BY data_date
        CLUSTER BY url, query
        OPTIONS (
          require_partition_filter = TRUE
        ) AS
        SELECT * FROM `{src}`
        WHERE data_date IS NOT NULL
    """
    job = client.query(ddl, location=location)
    job.result()


def backfill_diff(client: bigquery.Client, project_id: str, dataset_id: str,
                  old_table: str, new_table: str, location: str) -> None:
    src = f"{project_id}.{dataset_id}.{old_table}"
    dst = f"{project_id}.{dataset_id}.{new_table}"
    sql = f"""
        INSERT INTO `{dst}`
        SELECT *
        FROM `{src}`
        WHERE data_date > (
          SELECT IFNULL(MAX(data_date), DATE('1900-01-01'))
          FROM `{dst}`
          WHERE data_date BETWEEN DATE('1900-01-01') AND DATE('9999-12-31')
        )
    """
    job = client.query(sql, location=location)
    job.result()


def update_settings_ini_table_id(settings_path: Path, new_table: str) -> None:
    parser = configparser.ConfigParser()
    parser.read(settings_path, encoding='utf-8')
    if 'BIGQUERY' not in parser.sections():
        raise RuntimeError('BIGQUERY section missing in settings.ini')
    parser.set('BIGQUERY', 'table_id', new_table)
    with open(settings_path, 'w', encoding='utf-8') as f:
        parser.write(f)


def main() -> None:
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')
    old_table = config.get_config_value('BIGQUERY', 'TABLE_ID')
    location = config.get_config_value('BIGQUERY', 'LOCATION', 'asia-northeast1')
    new_table = f"{old_table}_v2"

    credentials_path = config.credentials_path
    credentials = service_account.Credentials.from_service_account_file(str(credentials_path))
    client = bigquery.Client(credentials=credentials, project=project_id)

    # 1) 作成（存在する場合はスキップ）
    dst_ref = client.dataset(dataset_id).table(new_table)
    try:
        client.get_table(dst_ref)
        created = False
    except Exception:
        create_partitioned_clustered_table(client, project_id, dataset_id, old_table, new_table, location)
        created = True

    # 2) 差分投入
    backfill_diff(client, project_id, dataset_id, old_table, new_table, location)

    # 3) 設定ファイルを書き換え（参照先切替）
    settings_path = config.get_config_file('settings.ini')
    update_settings_ini_table_id(settings_path, new_table)

    print(f"Migration completed. new_table={project_id}.{dataset_id}.{new_table}, created={created}")


if __name__ == '__main__':
    main()


