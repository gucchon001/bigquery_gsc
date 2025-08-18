import configparser
from datetime import datetime

from google.cloud import bigquery
from google.oauth2 import service_account

from utils.environment import config


def table_exists(client: bigquery.Client, table_fqn: str) -> bool:
    try:
        client.get_table(table_fqn)
        return True
    except Exception:
        return False


def copy_table(client: bigquery.Client, src: str, dst: str, location: str) -> None:
    job = client.copy_table(src, dst, location=location)
    job.result()


def delete_table(client: bigquery.Client, table_fqn: str) -> None:
    client.delete_table(table_fqn, not_found_ok=True)


def backup_table(client: bigquery.Client, table_fqn: str, location: str) -> str:
    ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    project, dataset, name = table_fqn.split('.')
    backup_fqn = f"{project}.{dataset}.{name}_backup_{ts}"
    copy_table(client, table_fqn, backup_fqn, location)
    return backup_fqn


def update_settings_ini(data_table: str, progress_table: str) -> None:
    settings_path = config.get_config_file('settings.ini')
    parser = configparser.ConfigParser()
    parser.read(settings_path, encoding='utf-8')
    parser.set('BIGQUERY', 'table_id', data_table)
    parser.set('BIGQUERY', 'progress_table_id', progress_table)
    with open(settings_path, 'w', encoding='utf-8') as f:
        parser.write(f)


def main() -> None:
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')
    location = config.get_config_value('BIGQUERY', 'LOCATION', 'asia-northeast1')

    # Sources (v2)
    src_data = f"{project_id}.{dataset_id}.T_searchdata_site_impression_v2"
    src_progress = f"{project_id}.{dataset_id}.T_progress_tracking_v2_rebuilt"

    # Dest (canonical)
    dst_data = f"{project_id}.{dataset_id}.T_searchdata_site_impression"
    dst_progress = f"{project_id}.{dataset_id}.T_progress_tracking"

    creds = service_account.Credentials.from_service_account_file(str(config.credentials_path))
    client = bigquery.Client(credentials=creds, project=project_id)

    # Backup existing canonical tables if present
    backups = {}
    if table_exists(client, dst_data):
        backups['data'] = backup_table(client, dst_data, location)
    if table_exists(client, dst_progress):
        backups['progress'] = backup_table(client, dst_progress, location)

    # Replace canonical with v2 (copy preserves schema/partitioning/cluster)
    delete_table(client, dst_data)
    copy_table(client, src_data, dst_data, location)

    delete_table(client, dst_progress)
    copy_table(client, src_progress, dst_progress, location)

    # Optionally delete old v2 sources after swap
    delete_table(client, src_data)
    delete_table(client, src_progress)

    # Update settings.ini to canonical names
    update_settings_ini('T_searchdata_site_impression', 'T_progress_tracking')

    print('swap_completed=True')
    print(f"backups={backups}")


if __name__ == '__main__':
    main()


