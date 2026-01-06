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

def main() -> None:
    """メイン処理"""
    # Webhook通知用のインスタンスを作成
    webhook_notifier = WebhookNotifier()
    
    try:
        # 環境変数のロード
        env.load_env()
        logger.info(f"現在の環境: {env.get_environment()}")

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
