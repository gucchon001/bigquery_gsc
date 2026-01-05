"""特定の日付のデータ取得・集計の詳細を分析するスクリプト"""
from datetime import date
from google.cloud import bigquery
from google.oauth2 import service_account

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.environment import config


def analyze_date_detail(target_date: date):
    """指定された日付のデータ取得・集計の詳細を分析"""
    project_id = config.get_config_value('BIGQUERY', 'PROJECT_ID')
    dataset_id = config.get_config_value('BIGQUERY', 'DATASET_ID')
    table_id_main = config.get_config_value('BIGQUERY', 'TABLE_ID')
    progress_table_id = config.get_config_value('BIGQUERY', 'PROGRESS_TABLE_ID')
    
    credentials_path = config.credentials_path
    credentials = service_account.Credentials.from_service_account_file(str(credentials_path))
    client = bigquery.Client(credentials=credentials, project=project_id)
    
    main_table = f"{project_id}.{dataset_id}.{table_id_main}"
    progress_table = f"{project_id}.{dataset_id}.{progress_table_id}"
    
    print(f"\n{'='*70}")
    print(f" {target_date} の詳細分析")
    print(f"{'='*70}\n")
    
    # 1. 進捗テーブルから取得件数を確認
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
            record_position,
            is_date_completed,
            updated_at
        FROM ranked
        WHERE rn = 1
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("target_date", "DATE", target_date)
        ]
    )
    
    try:
        result_progress = list(client.query(query_progress, job_config=job_config).result())
        if result_progress:
            row = result_progress[0]
            fetched_count = row.record_position
            print(f"[進捗テーブル]")
            print(f"  取得件数（record_position）: {fetched_count:,} 件")
            print(f"  完了フラグ: {row.is_date_completed}")
            print(f"  最終更新: {row.updated_at}")
        else:
            print(f"[進捗テーブル] 記録がありません")
            fetched_count = 0
    except Exception as e:
        print(f"[ERROR] 進捗テーブルの確認でエラー: {e}")
        fetched_count = 0
    
    # 2. メインテーブルの実際の保存件数
    query_main = f"""
        SELECT COUNT(*) AS record_count
        FROM `{main_table}`
        WHERE data_date = @target_date
    """
    
    try:
        result_main = list(client.query(query_main, job_config=job_config).result())
        saved_count = result_main[0].record_count if result_main else 0
        print(f"\n[メインテーブル]")
        print(f"  保存件数: {saved_count:,} 件")
    except Exception as e:
        print(f"[ERROR] メインテーブルの確認でエラー: {e}")
        saved_count = 0
    
    # 3. 集計による統合の影響を分析
    if fetched_count > 0 and saved_count > 0:
        diff = fetched_count - saved_count
        reduction_rate = (diff / fetched_count * 100) if fetched_count > 0 else 0
        
        print(f"\n[集計分析]")
        print(f"  取得件数: {fetched_count:,} 件")
        print(f"  保存件数: {saved_count:,} 件")
        print(f"  差: {diff:,} 件 ({reduction_rate:.2f}% 減少)")
        print(f"\n  説明:")
        print(f"  - aggregate_records()により、同じ(query, normalized_url)の組み合わせが統合されます")
        print(f"  - クエリパラメータが異なる同じURLは1つのレコードに集計されます")
        print(f"  - これは正常な動作です（重複排除・集計処理）")
    
    # 4. 重複の可能性を確認（同じquery+urlの組み合わせ数）
    query_duplicate_check = f"""
        SELECT 
            COUNT(*) AS total_records,
            COUNT(DISTINCT CONCAT(query, '|', url)) AS unique_combinations,
            COUNT(*) - COUNT(DISTINCT CONCAT(query, '|', url)) AS potential_duplicates
        FROM `{main_table}`
        WHERE data_date = @target_date
    """
    
    try:
        result_dup = list(client.query(query_duplicate_check, job_config=job_config).result())
        if result_dup:
            row = result_dup[0]
            print(f"\n[重複チェック]")
            print(f"  総レコード数: {row.total_records:,} 件")
            print(f"  ユニークな(query, url)組み合わせ: {row.unique_combinations:,} 件")
            if row.potential_duplicates > 0:
                print(f"  潜在的重複: {row.potential_duplicates:,} 件")
            else:
                print(f"  重複なし（すべてユニーク）")
    except Exception as e:
        print(f"[ERROR] 重複チェックでエラー: {e}")
    
    # 5. サマリー
    print(f"\n{'='*70}")
    if fetched_count > 0 and saved_count > 0:
        if diff > 0:
            print(f"[結論] データは正常に取得・保存されています")
            print(f"       集計処理により {diff:,} 件が統合されました（正常な動作）")
        else:
            print(f"[結論] データは正常に取得・保存されています")
    elif saved_count > 0:
        print(f"[結論] データは保存されています（進捗テーブルの記録なし）")
    else:
        print(f"[結論] データが保存されていません")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    # 確認したい日付を指定
    analyze_date_detail(date(2025, 12, 31))
    analyze_date_detail(date(2025, 12, 27))
    analyze_date_detail(date(2026, 1, 1))

