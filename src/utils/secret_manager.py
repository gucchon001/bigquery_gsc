# src/utils/secret_manager.py

import os
import json
import configparser
from typing import Optional, Dict, Any
from google.cloud import secretmanager
from google.auth.exceptions import DefaultCredentialsError
import logging

logger = logging.getLogger(__name__)


class SecretManagerUtils:
    """Secret Managerから設定を取得するユーティリティクラス"""

    _client: Optional[secretmanager.SecretManagerServiceClient] = None
    _project_id: Optional[str] = None
    _cache: Dict[str, str] = {}

    @classmethod
    def _get_client(cls) -> secretmanager.SecretManagerServiceClient:
        """Secret Managerクライアントを取得（シングルトン）"""
        if cls._client is None:
            try:
                cls._client = secretmanager.SecretManagerServiceClient()
                logger.info("Secret Manager client initialized")
            except DefaultCredentialsError:
                logger.warning(
                    "Secret Manager client initialization failed. "
                    "Falling back to local files. "
                    "This is expected in local development."
                )
                raise
        return cls._client

    @classmethod
    def _get_project_id(cls) -> str:
        """プロジェクトIDを取得"""
        if cls._project_id is None:
            # 環境変数から取得を試みる
            cls._project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
            if not cls._project_id:
                # GCE環境ではメタデータサーバーから取得
                try:
                    import requests
                    response = requests.get(
                        "http://metadata.google.internal/computeMetadata/v1/project/project-id",
                        headers={"Metadata-Flavor": "Google"},
                        timeout=2
                    )
                    cls._project_id = response.text
                except Exception:
                    logger.warning("Could not determine project ID. Secret Manager may not work.")
                    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
        return cls._project_id

    @classmethod
    def get_secret(cls, secret_id: str, version: str = "latest") -> Optional[str]:
        """
        Secret Managerからシークレットを取得します。

        Args:
            secret_id: シークレットID
            version: バージョン（デフォルト: "latest"）

        Returns:
            シークレットの値、取得できない場合はNone
        """
        # キャッシュをチェック
        cache_key = f"{secret_id}:{version}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        try:
            client = cls._get_client()
            project_id = cls._get_project_id()
            name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"

            response = client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")
            
            # キャッシュに保存
            cls._cache[cache_key] = secret_value
            logger.debug(f"Secret '{secret_id}' retrieved from Secret Manager")
            return secret_value

        except DefaultCredentialsError:
            logger.debug(f"Secret Manager not available, falling back to local files for '{secret_id}'")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve secret '{secret_id}': {e}")
            return None

    @classmethod
    def get_settings_ini(cls) -> Optional[configparser.ConfigParser]:
        """
        Secret Managerからsettings.iniの内容を取得してConfigParserオブジェクトを返します。

        Returns:
            ConfigParserオブジェクト、取得できない場合はNone
        """
        secret_value = cls.get_secret("settings-ini")
        if not secret_value:
            return None

        try:
            config = configparser.ConfigParser()
            config.read_string(secret_value)
            logger.info("Settings loaded from Secret Manager")
            return config
        except Exception as e:
            logger.error(f"Failed to parse settings.ini from Secret Manager: {e}")
            return None

    @classmethod
    def get_secrets_env(cls) -> Dict[str, str]:
        """
        Secret Managerからsecrets.envの内容を取得して辞書を返します。

        Returns:
            環境変数の辞書
        """
        secret_value = cls.get_secret("secrets-env")
        if not secret_value:
            return {}

        env_dict = {}
        for line in secret_value.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env_dict[key.strip()] = value.strip()
        
        logger.info(f"Loaded {len(env_dict)} environment variables from Secret Manager")
        return env_dict

    @classmethod
    def load_secrets_to_environment(cls) -> None:
        """
        Secret Managerから取得した環境変数をos.environに設定します。
        """
        env_dict = cls.get_secrets_env()
        for key, value in env_dict.items():
            if key not in os.environ:  # 既存の環境変数は上書きしない
                os.environ[key] = value
                logger.debug(f"Set environment variable: {key}")

    @classmethod
    def is_available(cls) -> bool:
        """
        Secret Managerが利用可能かどうかを確認します。

        Returns:
            Secret Managerが利用可能な場合True
        """
        try:
            cls._get_client()
            cls._get_project_id()
            return True
        except Exception:
            return False

