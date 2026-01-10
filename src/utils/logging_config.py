# logging_config.py
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional
import os
from utils.date_utils import get_current_jst_datetime

# Cloud Loggingのインポート（オプション）
try:
    import google.cloud.logging
    CLOUD_LOGGING_AVAILABLE = True
except ImportError:
    CLOUD_LOGGING_AVAILABLE = False

class LoggingConfig:
    _initialized = False

    def __init__(self):
        """
        ログ設定を初期化します。
        """
        if LoggingConfig._initialized:
            return  # 再初期化を防止

        self.log_dir = Path("logs")
        self.log_level = logging.INFO
        # JSTタイムゾーンを使用するためのFormatterを作成
        self.log_format = "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
        self.date_format = "%Y-%m-%d %H:%M:%S"

        self.setup_logging()

        LoggingConfig._initialized = True  # 初期化済みフラグを設定

    def setup_logging(self) -> None:
        """
        ロギング設定をセットアップします。
        Cloud Loggingが利用可能な場合は追加します。
        """
        handlers = []

        # ローカルファイルログ（常に有効）
        if not self.log_dir.exists():
            self.log_dir.mkdir(parents=True, exist_ok=True)

        # JSTでログファイル名を生成
        jst_datetime = get_current_jst_datetime()
        log_file = self.log_dir / f"app_{jst_datetime.strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file, when="midnight", interval=1, backupCount=30, encoding="utf-8"
        )
        handlers.append(file_handler)

        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        handlers.append(console_handler)

        # Cloud Logging（GCE環境で利用可能な場合）
        if CLOUD_LOGGING_AVAILABLE:
            try:
                # GCE環境かどうかを確認
                if os.getenv("GOOGLE_CLOUD_PROJECT") or self._is_gce_environment():
                    client = google.cloud.logging.Client()
                    client.setup_logging()
                    cloud_handler = client.get_default_handler()
                    if cloud_handler:
                        handlers.append(cloud_handler)
                        logging.getLogger().info("Cloud Logging handler added")
            except Exception as e:
                # Cloud Loggingの初期化に失敗しても続行
                logging.getLogger().warning(f"Failed to setup Cloud Logging: {e}")

        # カスタムFormatterを使用してJSTタイムゾーンで時刻を表示
        date_format_for_formatter = self.date_format
        class JSTFormatter(logging.Formatter):
            def formatTime(self, record, datefmt=None):
                # JSTで時刻を取得してフォーマット
                jst_dt = get_current_jst_datetime()
                if datefmt:
                    return jst_dt.strftime(datefmt)
                return jst_dt.strftime(date_format_for_formatter)

        # 各ハンドラーにJSTFormatterを適用
        jst_formatter = JSTFormatter(self.log_format, self.date_format)
        for handler in handlers:
            handler.setFormatter(jst_formatter)

        logging.basicConfig(
            level=self.log_level,
            format=self.log_format,
            handlers=handlers,
        )

        logging.getLogger().info("Logging setup complete.")

    def _is_gce_environment(self) -> bool:
        """GCE環境かどうかを判定"""
        try:
            import requests
            response = requests.get(
                "http://metadata.google.internal/computeMetadata/v1/",
                headers={"Metadata-Flavor": "Google"},
                timeout=1
            )
            return response.status_code == 200
        except Exception:
            return False


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    名前付きロガーを取得します。

    Args:
        name (Optional[str]): ロガー名

    Returns:
        logging.Logger: 名前付きロガー
    """
    LoggingConfig()
    return logging.getLogger(name)