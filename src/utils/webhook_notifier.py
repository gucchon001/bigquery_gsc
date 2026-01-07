"""
Google Chat Webhook通知ユーティリティ
エラー発生時および正常終了時にGoogle Chatに通知を送信します。
Google Chat APIを使用してメンション機能もサポートします。
"""
import os
import logging
import traceback
import requests
from typing import Optional, Dict, List
from datetime import datetime
from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# ユーザーID辞書（Webhookでのメンション用）
# 例: <users/111863040728288757718>
USER_IDS: Dict[str, str] = {
    "haraguchi": "111863040728288757718",
    # 他のメンバーも判明次第ここに追加
}

class WebhookNotifier:
    """Google Chat Webhook通知クラス"""
    
    def __init__(self, webhook_url: Optional[str] = None, space_id: Optional[str] = None):
        """
        WebhookNotifierを初期化します。
        
        Args:
            webhook_url: Google Chat Webhook URL。Noneの場合は環境変数から取得を試みます。
            space_id: Google Chat スペースID。設定されている場合はGoogle Chat APIを使用してメンション機能が有効になります。
        """
        self.webhook_url = webhook_url or os.getenv("Webhook_URL")
        self.space_id = space_id or os.getenv("CHAT_SPACE_ID")
        self.chat_service = None
        
        # Google Chat APIを使用する場合の初期化
        if self.space_id:
            try:
                credentials, _ = default(scopes=["https://www.googleapis.com/auth/chat.bot"])
                self.chat_service = build('chat', 'v1', credentials=credentials)
                logger.info("Google Chat API client initialized for mentions")
            except Exception as e:
                logger.warning(f"Google Chat APIの初期化に失敗しました。Webhook方式にフォールバックします: {e}")
                self.space_id = None
        
        if not self.webhook_url and not self.space_id:
            logger.warning("Webhook_URLまたはCHAT_SPACE_IDが設定されていません。通知は送信されません。")
        elif self.webhook_url:
            logger.info(f"WebhookNotifier initialized with URL: {self.webhook_url[:50]}...")
    
    def send_error_notification(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        traceback_str: Optional[str] = None,
        context: Optional[dict] = None,
        mentions: Optional[List[str]] = None,
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
        if not self.webhook_url and not self.space_id:
            logger.warning("Webhook URLまたはCHAT_SPACE_IDが設定されていないため、通知を送信できません。")
            return False
        
        try:
            # Google Chat APIを使用する場合（メンション機能付き）
            if self.space_id and self.chat_service:
                return self._send_error_notification_via_api(
                    error_message, error_type, traceback_str, context, mentions
                )
            
            # Webhook方式（従来の方法）
            if self.webhook_url:
                message = self._build_error_message(
                    error_message, error_type, traceback_str, context, mentions
                )
                
                response = requests.post(
                    self.webhook_url,
                    json=message,
                    timeout=10
                )
                response.raise_for_status()
                
                logger.info("エラー通知をGoogle Chatに送信しました（Webhook方式）。")
                return True
            else:
                logger.warning("通知を送信する方法がありません。")
                return False
            
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
        context: Optional[dict] = None,
        mentions: Optional[List[str]] = None,
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
        
        # メンション（Webhookでは <users/USER_ID> 形式で可能なケースあり）
        mention_line = ""
        if mentions:
            ids = [USER_IDS[m] for m in mentions if m in USER_IDS]
            if ids:
                mention_line = " ".join([f"<users/{uid}>" for uid in ids]) + "\n\n"

        # エラー情報部分
        error_info = f"{mention_line}**エラーメッセージ:**\n{error_message}"
        
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
    
    def _send_error_notification_via_api(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        traceback_str: Optional[str] = None,
        context: Optional[dict] = None,
        mentions: Optional[List[str]] = None
    ) -> bool:
        """
        Google Chat APIを使用してエラー通知を送信します（メンション機能付き）。
        
        Args:
            error_message: エラーメッセージ
            error_type: エラーの種類
            traceback_str: トレースバック文字列
            context: 追加のコンテキスト情報
        
        Returns:
            送信成功時True、失敗時False
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # メンション対象（ユーザーID優先）
            mention_ids = [USER_IDS[m] for m in (mentions or []) if m in USER_IDS]
            mention_text = ""
            if mention_ids:
                mention_text = " ".join([f"<users/{uid}>" for uid in mention_ids]) + " "
            
            # エラーメッセージの構築
            error_text = f"**エラーメッセージ:**\n{error_message}"
            
            if error_type:
                error_text += f"\n\n**エラータイプ:** {error_type}"
            
            error_text += f"\n\n**発生時刻:** {timestamp}"
            
            # コンテキスト情報
            if context:
                context_text = "\n\n**コンテキスト情報:**\n"
                for key, value in context.items():
                    context_text += f"- {key}: {value}\n"
                error_text += context_text
            
            # トレースバック（長すぎる場合は省略）
            if traceback_str:
                truncated_traceback = traceback_str[-500:] if len(traceback_str) > 500 else traceback_str
                error_text += f"\n\n**トレースバック（末尾）:**\n```\n{truncated_traceback}\n```"
            
            # Google Chat API形式のメッセージ（cardsV2形式でメンションを含む）
            message_body = {
                "text": f"{mention_text}エラーが発生しました",
                "cardsV2": [
                    {
                        "cardId": "error-notification",
                        "card": {
                            "header": {
                                "title": "GSC Scraper エラー",
                                "subtitle": error_type or "Unknown Error",
                                "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/error/default/48px.svg",
                                "imageType": "CIRCLE"
                            },
                            "sections": [
                                {
                                    "widgets": [
                                        {
                                            "decoratedText": {
                                                "topLabel": "エラー詳細",
                                                "text": error_text,
                                                "wrapText": True
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
            
            # Google Chat APIを使用してメッセージを送信
            result = self.chat_service.spaces().messages().create(
                parent=self.space_id,
                body=message_body
            ).execute()
            
            logger.info(f"エラー通知をGoogle Chat API経由で送信しました（メッセージID: {result.get('name', 'N/A')}）。")
            return True
            
        except HttpError as e:
            logger.error(f"Google Chat APIでの通知送信に失敗しました: {e}")
            # フォールバック: Webhook方式を試行
            if self.webhook_url:
                logger.info("Webhook方式にフォールバックします。")
                return self.send_error_notification(error_message, error_type, traceback_str, context)
            return False
        except Exception as e:
            logger.error(f"予期しないエラーがGoogle Chat API通知送信中に発生しました: {e}")
            return False
    
    def send_success_notification(
        self,
        message: str,
        daily_results: Optional[List[Dict[str, any]]] = None,
        daily_stats: Optional[List[Dict[str, any]]] = None,
        context: Optional[dict] = None
    ) -> bool:
        """
        成功通知をGoogle Chatに送信します。
        
        Args:
            message: 成功メッセージ
            daily_results: 日ごとの結果（取得件数またはスキップ）（例: [{"date": "2024-01-01", "records": 1000, "status": "取得"}, ...]）
            daily_stats: 日ごとの処理件数統計（後方互換性のため残す）
            context: 追加のコンテキスト情報（使用しない）
        
        Returns:
            送信成功時True、失敗時False
        """
        if not self.webhook_url:
            logger.warning("Webhook URLが設定されていないため、成功通知を送信できません。")
            return False
        
        logger.info("成功通知の送信を開始します。")
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # メッセージの構築
            success_text = f"✅ **GSC Scraper 実行成功**\n\n{message}\n\n**実行時刻:** {timestamp}"
            
            # 日ごとの結果を追加（daily_resultsを優先、なければdaily_statsを使用）
            results = daily_results if daily_results else daily_stats
            if results:
                success_text += "\n\n**日ごとの処理結果:**\n"
                total_records = 0
                for result in results:
                    date = result.get("date", "N/A")
                    records = result.get("records", 0)
                    status = result.get("status", "取得")
                    
                    if status == "スキップ":
                        success_text += f"- {date}: スキップ\n"
                    else:
                        success_text += f"- {date}: {records:,}件\n"
                        total_records += records
                
                if total_records > 0:
                    success_text += f"\n**合計:** {total_records:,}件"
            
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
    daily_results: Optional[List[Dict[str, any]]] = None,
    daily_stats: Optional[List[Dict[str, any]]] = None,
    context: Optional[dict] = None
) -> bool:
    """
    成功通知を送信する便利関数。
    
    Args:
        message: 成功メッセージ
        daily_results: 日ごとの結果（取得件数またはスキップ）
        daily_stats: 日ごとの処理件数統計（後方互換性のため残す）
        context: 追加のコンテキスト情報（使用しない）
    
    Returns:
        送信成功時True、失敗時False
    """
    # 通知が無効な場合は送信しない
    is_enabled = is_notification_enabled("success")
    logger.info(f"成功通知の有効性チェック: {is_enabled}")
    if not is_enabled:
        logger.warning("成功通知が無効化されているため、通知を送信しません。")
        return False
    
    logger.info("WebhookNotifierを初期化して成功通知を送信します。")
    notifier = WebhookNotifier()
    result = notifier.send_success_notification(
        message=message,
        daily_results=daily_results,
        daily_stats=daily_stats,
        context=context
    )
    logger.info(f"成功通知の送信結果: {result}")
    return result

