"""
Google Chat Webhook通知ユーティリティ
エラー発生時および正常終了時にGoogle Chatに通知を送信します。
"""
import os
import logging
import traceback
import requests
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class WebhookNotifier:
    """Google Chat Webhook通知クラス"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        WebhookNotifierを初期化します。
        
        Args:
            webhook_url: Google Chat Webhook URL。Noneの場合は環境変数から取得を試みます。
        """
        self.webhook_url = webhook_url or os.getenv("Webhook_URL")
        if not self.webhook_url:
            logger.warning("Webhook_URLが設定されていません。通知は送信されません。")
    
    def send_error_notification(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        traceback_str: Optional[str] = None,
        context: Optional[dict] = None
    ) -> bool:
        """
        エラー通知をGoogle Chatに送信します。
        
        Args:
            error_message: エラーメッセージ
            error_type: エラーの種類（例: "GSC API Error", "BigQuery Error"）
            traceback_str: トレースバック文字列
            context: 追加のコンテキスト情報（辞書形式）
        
        Returns:
            送信成功時True、失敗時False
        """
        if not self.webhook_url:
            logger.warning("Webhook URLが設定されていないため、通知を送信できません。")
            return False
        
        try:
            # メッセージの構築
            message = self._build_error_message(
                error_message, error_type, traceback_str, context
            )
            
            # Webhookに送信
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info("エラー通知をGoogle Chatに送信しました。")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Webhook通知の送信に失敗しました: {e}")
            return False
        except Exception as e:
            logger.error(f"予期しないエラーが通知送信中に発生しました: {e}")
            return False
    
    def _build_error_message(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        traceback_str: Optional[str] = None,
        context: Optional[dict] = None
    ) -> dict:
        """
        Google Chat用のメッセージを構築します。
        
        Args:
            error_message: エラーメッセージ
            error_type: エラーの種類
            traceback_str: トレースバック文字列
            context: 追加のコンテキスト情報
        
        Returns:
            Google Chat API形式のメッセージ辞書
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ヘッダー部分
        header_text = f"🚨 **GSC Scraper エラー通知**"
        
        # エラー情報部分
        error_info = f"**エラーメッセージ:**\n{error_message}"
        
        if error_type:
            error_info += f"\n\n**エラータイプ:** {error_type}"
        
        error_info += f"\n\n**発生時刻:** {timestamp}"
        
        # コンテキスト情報
        if context:
            context_text = "\n\n**コンテキスト情報:**\n"
            for key, value in context.items():
                context_text += f"- {key}: {value}\n"
            error_info += context_text
        
        # トレースバック（長すぎる場合は省略）
        if traceback_str:
            # トレースバックは最後の500文字のみ表示
            truncated_traceback = traceback_str[-500:] if len(traceback_str) > 500 else traceback_str
            error_info += f"\n\n**トレースバック（末尾）:**\n```\n{truncated_traceback}\n```"
        
        # Google Chat Card形式のメッセージ
        message = {
            "cards": [
                {
                    "header": {
                        "title": "GSC Scraper エラー",
                        "subtitle": error_type or "Unknown Error",
                        "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/error/default/48px.svg",
                        "imageStyle": "IMAGE"
                    },
                    "sections": [
                        {
                            "widgets": [
                                {
                                    "textParagraph": {
                                        "text": error_info
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        return message
    
    def send_success_notification(
        self,
        message: str,
        daily_stats: Optional[List[Dict[str, any]]] = None,
        context: Optional[dict] = None
    ) -> bool:
        """
        成功通知をGoogle Chatに送信します。
        
        Args:
            message: 成功メッセージ
            daily_stats: 日ごとの処理件数統計（例: [{"date": "2024-01-01", "records": 1000}, ...]）
            context: 追加のコンテキスト情報
        
        Returns:
            送信成功時True、失敗時False
        """
        if not self.webhook_url:
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # メッセージの構築
            success_text = f"✅ **GSC Scraper 実行成功**\n\n{message}\n\n**実行時刻:** {timestamp}"
            
            # 日ごとの統計情報を追加
            if daily_stats:
                success_text += "\n\n**日ごとの処理件数:**\n"
                total_records = 0
                for stat in daily_stats:
                    date = stat.get("date", "N/A")
                    records = stat.get("records", 0)
                    total_records += records
                    success_text += f"- {date}: {records:,}件\n"
                success_text += f"\n**合計:** {total_records:,}件"
            
            # コンテキスト情報
            if context:
                success_text += "\n\n**実行情報:**\n"
                for key, value in context.items():
                    success_text += f"- {key}: {value}\n"
            
            # Google Chat Card形式のメッセージ
            message_data = {
                "cards": [
                    {
                        "header": {
                            "title": "GSC Scraper 実行成功",
                            "subtitle": f"実行時刻: {timestamp}",
                            "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/check_circle/default/48px.svg",
                            "imageStyle": "IMAGE"
                        },
                        "sections": [
                            {
                                "widgets": [
                                    {
                                        "textParagraph": {
                                            "text": success_text
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                json=message_data,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info("成功通知をGoogle Chatに送信しました。")
            return True
        except Exception as e:
            logger.error(f"成功通知の送信に失敗しました: {e}")
            return False


def is_notification_enabled(notification_type: str = "error") -> bool:
    """
    通知が有効かどうかを確認します。
    
    Args:
        notification_type: 通知タイプ ("error" または "success")
    
    Returns:
        通知が有効な場合True、無効な場合False
    """
    try:
        from utils.environment import config
        if notification_type == "error":
            value = config.get_config_value("NOTIFICATION", "enable_error_notification", default="true")
            return str(value).lower() == "true"
        elif notification_type == "success":
            value = config.get_config_value("NOTIFICATION", "enable_success_notification", default="true")
            return str(value).lower() == "true"
        return False
    except Exception as e:
        logger.warning(f"通知設定の取得に失敗しました。デフォルトで有効にします: {e}")
        return True  # デフォルトで有効


def send_error_notification(
    error: Exception,
    error_type: Optional[str] = None,
    context: Optional[dict] = None
) -> bool:
    """
    エラー通知を送信する便利関数。
    
    Args:
        error: 例外オブジェクト
        error_type: エラーの種類
        context: 追加のコンテキスト情報
    
    Returns:
        送信成功時True、失敗時False
    """
    # 通知が無効な場合は送信しない
    if not is_notification_enabled("error"):
        logger.debug("エラー通知が無効化されているため、通知を送信しません。")
        return False
    
    notifier = WebhookNotifier()
    traceback_str = traceback.format_exc()
    error_message = str(error)
    
    return notifier.send_error_notification(
        error_message=error_message,
        error_type=error_type or type(error).__name__,
        traceback_str=traceback_str,
        context=context
    )


def send_success_notification(
    message: str,
    daily_stats: Optional[List[Dict[str, any]]] = None,
    context: Optional[dict] = None
) -> bool:
    """
    成功通知を送信する便利関数。
    
    Args:
        message: 成功メッセージ
        daily_stats: 日ごとの処理件数統計
        context: 追加のコンテキスト情報
    
    Returns:
        送信成功時True、失敗時False
    """
    # 通知が無効な場合は送信しない
    if not is_notification_enabled("success"):
        logger.debug("成功通知が無効化されているため、通知を送信しません。")
        return False
    
    notifier = WebhookNotifier()
    return notifier.send_success_notification(
        message=message,
        daily_stats=daily_stats,
        context=context
    )

