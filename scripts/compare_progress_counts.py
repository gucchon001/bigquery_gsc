from google.cloud import bigquery
from google.oauth2 import service_account

from utils.environment import config


def main() -> None:
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')
    location = config.get_config_value('BIGQUERY', 'LOCATION', 'asia-northeast1')
    old_tbl = f"{project_id}.{dataset_id}.T_progress_tracking"
    v2_tbl = f"{project_id}.{dataset_id}.T_progress_tracking_v2"

    creds = service_account.Credentials.from_service_account_file(str(config.credentials_path))
    client = bigquery.Client(credentials=creds, project=project_id)

    q_old = f"""
    WITH ranked AS (
      SELECT data_date, is_date_completed, updated_at,
             ROW_NUMBER() OVER (PARTITION BY data_date ORDER BY is_date_completed DESC, updated_at DESC) rn
      FROM `{old_tbl}`
      WHERE record_position > 0 AND data_date IS NOT NULL
    )
    SELECT COUNTIF(rn=1) AS cnt FROM ranked
    """
    old_cnt = list(client.query(q_old, location=location).result())[0].cnt

    q_v2 = f"SELECT COUNT(*) AS cnt FROM `{v2_tbl}`"
    v2_cnt = list(client.query(q_v2, location=location).result())[0].cnt

    print(f"old_latest_per_date={old_cnt}")
    print(f"v2_total={v2_cnt}")
    print("match=" + str(old_cnt == v2_cnt))


if __name__ == '__main__':
    main()


