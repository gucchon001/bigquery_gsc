# -*- coding: utf-8 -*-
"""
GSC API 疎通確認スクリプト
"""
import sys
import io
from pathlib import Path
from datetime import datetime, timedelta

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

# Set UTF-8 encoding for stdout and stderr
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from utils.environment import EnvironmentUtils as env, config
from modules.gsc_fetcher import GSCConnector

def test_gsc_connection():
    """GSC APIへの接続をテストします"""
    try:
        print("=" * 60)
        print("GSC API 疎通確認テスト")
        print("=" * 60)
        
        # 環境変数のロード
        env.load_env()
        print(f"\n[INFO] 認証情報ファイル: {config.credentials_path}")
        
        # GSCConnectorの初期化
        print("\n[INFO] GSCConnectorを初期化しています...")
        gsc_connector = GSCConnector(config)
        print("[OK] GSCConnectorの初期化が完了しました")
        
        # サイトURLを取得
        site_url = config.gsc_settings['url']
        print(f"\n[INFO] 対象サイト: {site_url}")
        
        # テスト用の日付（2日前、GSCの制限により最新データは2日前まで）
        test_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        print(f"[INFO] テスト日付: {test_date}")
        
        # API呼び出し（少ない件数で試行）
        print(f"\n[INFO] GSC APIを呼び出しています...")
        print(f"       日付: {test_date}")
        print(f"       取得件数: 10件")
        
        records, next_record = gsc_connector.fetch_records(
            date=test_date,
            start_record=0,
            limit=10
        )
        
        print(f"\n[SUCCESS] GSC APIへの接続が成功しました！")
        print(f"          取得レコード数: {len(records)}件")
        print(f"          次の開始位置: {next_record}")
        
        if records:
            print(f"\n[INFO] 取得したデータのサンプル（最初の1件）:")
            print(f"       {records[0]}")
        
        print("\n" + "=" * 60)
        print("テスト完了: GSC APIへの接続は正常です")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] GSC APIへの接続に失敗しました")
        print(f"        エラー内容: {type(e).__name__}: {str(e)}")
        print("\n" + "=" * 60)
        print("テスト失敗: GSC APIへの接続に問題があります")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gsc_connection()
    sys.exit(0 if success else 1)

