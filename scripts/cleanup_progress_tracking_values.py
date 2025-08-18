from datetime import timedelta
from google.api_core.exceptions import BadRequest
from google.cloud import bigquery
from google.oauth2 import service_account

from utils.date_utils import get_current_jst_datetime, format_datetime_jst
from utils.environment import config


def delete_records(client: bigquery.Client, table_fqn: str, threshold_dt_str: str, location: str) -> None:
    # パーティションフィルタと更新時刻しきい値で限定
    sql = f"""
    DELETE FROM `{table_fqn}`
    WHERE data_date BETWEEN DATE('1900-01-01') AND DATE('9999-12-31')
      AND updated_at < @threshold
      AND record_position IN (0, 25000)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("threshold", "DATETIME", threshold_dt_str)
        ]
    )
    client.query(sql, job_config=job_config, location=location).result()


def main() -> None:
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')
    location = config.get_config_value('BIGQUERY', 'LOCATION', 'asia-northeast1')
    table_fqn = f"{project_id}.{dataset_id}.T_progress_tracking"

    creds = service_account.Credentials.from_service_account_file(str(config.credentials_path))
    client = bigquery.Client(credentials=creds, project=project_id)

    threshold_dt = get_current_jst_datetime() - timedelta(minutes=90)
    threshold_dt_str = format_datetime_jst(threshold_dt)

    try:
        delete_records(client, table_fqn, threshold_dt_str, location)
        print("cleanup_done=True")
    except BadRequest as e:
        if "streaming buffer" in str(e).lower():
            print("cleanup_skipped_due_to_streaming_buffer=True")
        else:
            raise


if __name__ == '__main__':
    main()


