#main.py
# -*- coding: utf-8 -*-
import sys
import io

# Set UTF-8 encoding for stdout and stderr
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from utils.environment import EnvironmentUtils as env, config
from utils.logging_config import get_logger
from modules.gsc_handler import process_gsc_data, cleanup_progress_table
from utils.webhook_notifier import WebhookNotifier, send_error_notification

# 名前付きロガーを取得
logger = get_logger(__name__)

def setup_configurations():
    """
    設定ファイルと機密情報をロードしてデータを取得します。
    """
    # 環境変数のロード
    env.load_env()

    # settings.ini の値を取得
    temp_value = env.get_config_value("demo", "temp", default="N/A")
    logger.info(f"取得した設定値: demo.temp = {temp_value}")

    # secrets.env の値を取得
    secrets_demo = env.get_env_var("secrets_demo", default="N/A")
    logger.info(f"取得した秘密情報: secrets_demo = {secrets_demo}")

    # 現在の環境
    environment = env.get_environment()
    logger.info(f"現在の環境: {environment}")

    return temp_value, secrets_demo, environment

def main() -> None:
    """メイン処理"""
    # Webhook通知用のインスタンスを作成
    webhook_notifier = WebhookNotifier()
    
    try:
        # 実行時のメッセージ
        print("Hello, newProject!!")
        logger.info("Hello, newProject!!")

        # 設定値と秘密情報のロード
        temp, secrets_demo, environment = setup_configurations()

        # 設定完了メッセージの表示
        print(f'設定ファイルの設定完了{{"demo": "{temp}"}}')
        print(f'機密情報ファイルの設定完了{{"demo": "{secrets_demo}"}}')
        print('ログ設定完了')

        # テスト用: エラー通知をテストする場合は環境変数 TEST_ERROR_NOTIFICATION を設定
        import os
        if os.getenv('TEST_ERROR_NOTIFICATION') == 'true':
            logger.info("テストモード: エラー通知をテストするために意図的にエラーを発生させます。")
            raise ValueError("これはエラー通知のテストです。実際のエラーではありません。")

        # 進捗テーブルの不要行を軽くクリーンアップ（ストリーミングバッファが乗る前の早期段階で実施）
        try:
            cleanup_progress_table(config, retention_minutes=90)
        except Exception as e:
            logger.warning(f"進捗テーブルのクリーンアップ中にエラーが発生しました: {e}")
            # クリーンアップのエラーは致命的ではないため、通知は送信しない

        # GSC データ取得処理を実行
        logger.info("process_gsc_data を呼び出します。")
        process_gsc_data()
        logger.info("process_gsc_data の呼び出しが完了しました。")
        
    except Exception as e:
        # メイン処理でエラーが発生した場合、ログに記録し、Webhook通知を送信
        logger.error(f"メイン処理でエラーが発生しました: {e}", exc_info=True)
        
        # Webhook通知を送信
        send_error_notification(
            error=e,
            error_type="Main Process Error",
            context={
                "environment": env.get_environment() if hasattr(env, 'get_environment') else "unknown"
            }
        )
        
        # エラーを再発生させて、VMの起動スクリプトがエラーを検知できるようにする
        raise

if __name__ == "__main__":
    main()
