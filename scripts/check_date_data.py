"""特定の日付のデータ取得状況を確認するスクリプト"""
from datetime import date
from google.cloud import bigquery
from google.oauth2 import service_account

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.environment import config


def check_date_data(target_date: date):
    """指定された日付のデータ取得状況を確認"""
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')
    table_id_main = config.get_config_value('BIGQUERY', 'TABLE_ID')
    progress_table_id = config.get_config_value('BIGQUERY', 'PROGRESS_TABLE_ID')
    
    credentials_path = config.credentials_path
    credentials = service_account.Credentials.from_service_account_file(str(credentials_path))
    client = bigquery.Client(credentials=credentials, project=project_id)
    
    main_table = f"{project_id}.{dataset_id}.{table_id_main}"
    progress_table = f"{project_id}.{dataset_id}.{progress_table_id}"
    
    print(f"\n=== {target_date} のデータ取得状況 ===\n")
    
    # 1. メインテーブル（実際のデータ）の確認
    query_main = f"""
        SELECT COUNT(*) AS record_count
        FROM `{main_table}`
        WHERE data_date = @target_date
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("target_date", "DATE", target_date)
        ]
    )
    
    try:
        result_main = list(client.query(query_main, job_config=job_config).result())
        record_count = result_main[0].record_count if result_main else 0
        print(f"[メインテーブル] {main_table}")
        print(f"   レコード数: {record_count:,} 件")
    except Exception as e:
        print(f"[ERROR] メインテーブルの確認でエラー: {e}")
        record_count = 0
    
    # 2. 進捗テーブルの確認
    query_progress = f"""
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
            FROM `{progress_table}`
            WHERE data_date = @target_date
        )
        SELECT
            data_date,
            record_position,
            is_date_completed,
            updated_at
        FROM ranked
        WHERE rn = 1
    """
    
    try:
        result_progress = list(client.query(query_progress, job_config=job_config).result())
        if result_progress:
            row = result_progress[0]
            print(f"\n[進捗テーブル] {progress_table}")
            print(f"   最新状態:")
            print(f"   - record_position: {row.record_position:,}")
            print(f"   - is_date_completed: {row.is_date_completed}")
            print(f"   - updated_at: {row.updated_at}")
        else:
            print(f"\n[WARNING] 進捗テーブルに記録がありません")
    except Exception as e:
        print(f"[ERROR] 進捗テーブルの確認でエラー: {e}")
    
    # 3. まとめ
    print(f"\n{'='*50}")
    if record_count > 0:
        print(f"[OK] {target_date}: データあり ({record_count:,} 件)")
    else:
        print(f"[NG] {target_date}: データなし")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    # 確認したい日付を指定
    check_date_data(date(2025, 12, 31))
    check_date_data(date(2025, 12, 27))
    check_date_data(date(2026, 1, 1))
    check_date_data(date(2026, 1, 3))

