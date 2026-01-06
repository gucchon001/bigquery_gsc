# src/utils/environment.py

import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Any
import configparser
import logging

# Secret Managerのインポート（オプション）
try:
    from .secret_manager import SecretManagerUtils
    SECRET_MANAGER_AVAILABLE = True
except ImportError:
    SECRET_MANAGER_AVAILABLE = False

class EnvironmentUtils:
    """プロジェクト全体で使用する環境関連のユーティリティクラス"""

    # プロジェクトルートのデフォルト値
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    @staticmethod
    def set_project_root(path: Path) -> None:
        """
        プロジェクトのルートディレクトリを設定します。

        Args:
            path (Path): 新しいプロジェクトルート
        """
        EnvironmentUtils.BASE_DIR = path

    @staticmethod
    def get_project_root() -> Path:
        """
        プロジェクトのルートディレクトリを取得します。

        Returns:
            Path: プロジェクトのルートディレクトリ
        """
        return EnvironmentUtils.BASE_DIR

    @staticmethod
    def load_env(env_file: Optional[Path] = None) -> None:
        """
        環境変数を .env ファイルまたはSecret Managerからロードします。

        Args:
            env_file (Optional[Path]): .env ファイルのパス
        """
        # Secret Managerが利用可能な場合は優先
        if SECRET_MANAGER_AVAILABLE and SecretManagerUtils.is_available():
            try:
                SecretManagerUtils.load_secrets_to_environment()
                _logger = logging.getLogger(__name__)
                _logger.info("Environment variables loaded from Secret Manager")
                return
            except Exception as e:
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Failed to load from Secret Manager, falling back to file: {e}")

        # ファイルから読み込む（フォールバック）
        env_file = env_file or (EnvironmentUtils.BASE_DIR / "config" / "secrets.env")

        if not env_file.exists():
            raise FileNotFoundError(f"{env_file} が見つかりません。正しいパスを指定してください。")

        load_dotenv(env_file)

    @staticmethod
    def get_env_var(key: str, default: Optional[Any] = None) -> Any:
        """
        環境変数を取得します。

        Args:
            key (str): 環境変数のキー
            default (Optional[Any]): デフォルト値

        Returns:
            Any: 環境変数の値またはデフォルト値
        """
        return os.getenv(key, default)

    @staticmethod
    def get_config_file(file_name: str = "settings.ini") -> Path:
        """
        設定ファイルのパスを取得します。

        Args:
            file_name (str): 設定ファイル名

        Returns:
            Path: 設定ファイルのパス

        Raises:
            FileNotFoundError: 指定された設定ファイルが見つからない場合
        """
        config_path = EnvironmentUtils.BASE_DIR / "config" / file_name
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        return config_path

    @staticmethod
    def get_config_value(section: str, key: str, default: Optional[Any] = None) -> Any:
        """
        設定ファイルから指定のセクションとキーの値を取得します。

        Args:
            section (str): セクション名
            key (str): キー名
            default (Optional[Any]): デフォルト値

        Returns:
            Any: 設定値
        """
        config_path = EnvironmentUtils.get_config_file()
        config = configparser.ConfigParser()

        # utf-8 エンコーディングで読み込む
        config.read(config_path, encoding='utf-8')

        if not config.has_section(section):
            return default
        if not config.has_option(section, key):
            return default

        value = config.get(section, key, fallback=default)

        # 型変換
        if isinstance(default, bool):
            return config.getboolean(section, key, fallback=default)
        if isinstance(default, int):
            try:
                return int(value)
            except ValueError:
                return default
        if isinstance(default, float):
            try:
                return float(value)
            except ValueError:
                return default
        return value

    @staticmethod
    def resolve_path(path: str) -> Path:
        """
        指定されたパスをプロジェクトルートに基づいて絶対パスに変換します。

        Args:
            path (str): 相対パスまたは絶対パス

        Returns:
            Path: 解決された絶対パス
        """
        resolved_path = Path(path)
        if not resolved_path.is_absolute():
            resolved_path = EnvironmentUtils.get_project_root() / resolved_path

        if not resolved_path.exists():
            raise FileNotFoundError(f"Resolved path does not exist: {resolved_path}")

        return resolved_path

    @staticmethod
    def get_service_account_file() -> Path:
        """
        サービスアカウントファイルのパスを取得します。

        Returns:
            Path: サービスアカウントファイルの絶対パス

        Raises:
            FileNotFoundError: ファイルが存在しない場合
        """
        service_account_file = EnvironmentUtils.get_env_var(
            "SERVICE_ACCOUNT_FILE",
            default=EnvironmentUtils.get_config_value("GOOGLE", "service_account_file", default="config/service_account.json")
        )

        return EnvironmentUtils.resolve_path(service_account_file)

    @staticmethod
    def get_environment() -> str:
        """
        環境変数 APP_ENV を取得します。
        デフォルト値は 'development' です。

        Returns:
            str: 現在の環境（例: 'development', 'production'）
        """
        return EnvironmentUtils.get_env_var("APP_ENV", "development")

    @staticmethod
    def get_openai_api_key():
        """
        Get the OpenAI API key from the environment variables.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY が設定されていません。環境変数を確認してください。")
        return api_key

    @staticmethod
    def get_openai_model():
        """
        OpenAI モデル名を settings.ini ファイルから取得します。
        設定がない場合はデフォルト値 'gpt-4o' を返します。
        """
        return EnvironmentUtils.get_config_value("OPENAI", "model", default="gpt-4o")

class Config:
    def __init__(self, env='development'):
        self.env = env
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.config = self._load_config()
        self._load_secrets()
        self._setup_credentials()

        # GSC設定を初期化時にロード
        self._gsc_settings = self._load_gsc_settings()

    def _load_gsc_settings(self):
        """GSC関連の設定を初期化時に1度だけ読み込む"""
        try:
            settings = {
                'url': self.config['GSC']['SITE_URL'],
                'start_date': self.config['GSC'].get('START_DATE', '2024-11-01'),
                'batch_size': int(self.config['GSC']['BATCH_SIZE']),
                'metrics': self.config['GSC']['METRICS'].split(','),
                'dimensions': self.config['GSC']['DIMENSIONS'].split(','),
                'retry_count': int(self.config['GSC']['RETRY_COUNT']),
                'retry_delay': int(self.config['GSC']['RETRY_DELAY']),
                'daily_api_limit': int(self.config['GSC']['DAILY_API_LIMIT']),
                'initial_run': self.config['GSC_INITIAL'].getboolean('INITIAL_RUN', fallback=True),
                'initial_fetch_days': int(self.config['GSC_DAILY']['INITIAL_FETCH_DAYS']),
                'daily_fetch_days': int(self.config['GSC_DAILY']['DAILY_FETCH_DAYS']),
                'project_id': self.config['BIGQUERY']['PROJECT_ID'],
            }
            self.logger.info(f"GSC settings loaded: {settings}")  # 初回のみログ出力
            return settings
        except KeyError as e:
            self.logger.error(f"Missing key in GSC configuration: {e}")
            raise
        except ValueError as e:
            self.logger.error(f"Invalid value in GSC configuration: {e}")
            raise

    @property
    def gsc_settings(self):
        """初期化済みの GSC 設定を返す"""
        return self._gsc_settings

    def _load_config(self):
        """設定ファイルの読み込み（Secret Manager優先、ファイルはフォールバック）"""
        config = configparser.ConfigParser()
        
        # Secret Managerが利用可能な場合は優先
        if SECRET_MANAGER_AVAILABLE and SecretManagerUtils.is_available():
            try:
                secret_config = SecretManagerUtils.get_settings_ini()
                if secret_config:
                    self.logger.info("Loaded configuration from Secret Manager")
                    return secret_config
            except Exception as e:
                self.logger.warning(f"Failed to load from Secret Manager, falling back to file: {e}")

        # ファイルから読み込む（フォールバック）
        config_path = self.base_path / 'config' / 'settings.ini'

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                config.read_file(f)
            self.logger.info(f"Loaded configuration from: {config_path}")
        except UnicodeDecodeError:
            try:
                with open(config_path, 'r', encoding='cp932') as f:
                    config.read_file(f)
                self.logger.warning(f"Loaded configuration using fallback encoding: {config_path}")
            except Exception as e:
                self.logger.error(f"Failed to load configuration file: {e}")
                raise

        return config

    def _load_secrets(self):
        """環境変数ファイルの読み込み（Secret Manager優先、ファイルはフォールバック）"""
        # Secret Managerが利用可能な場合は優先
        if SECRET_MANAGER_AVAILABLE and SecretManagerUtils.is_available():
            try:
                SecretManagerUtils.load_secrets_to_environment()
                self.logger.info("Environment variables loaded from Secret Manager")
                return
            except Exception as e:
                self.logger.warning(f"Failed to load from Secret Manager, falling back to file: {e}")

        # ファイルから読み込む（フォールバック）
        env_path = self.base_path / 'config' / 'secrets.env'
        if not env_path.exists():
            raise FileNotFoundError(f"Secrets file not found: {env_path}")

        try:
            load_dotenv(env_path, encoding='utf-8')
            self.logger.info(f"Loaded environment variables from: {env_path}")
        except Exception as e:
            self.logger.error(f"Failed to load secrets file: {e}")
            raise

    def _setup_credentials(self):
        """認証情報ファイルのパスを設定（Secret Manager優先、ファイルはフォールバック）"""
        # Cloud Run環境の判定: K_SERVICE, K_REVISION, またはメタデータサーバーが利用可能
        is_cloud_run = (
            os.getenv('K_SERVICE') or 
            os.getenv('K_REVISION') or
            os.getenv('GOOGLE_CLOUD_PROJECT') or
            os.getenv('GCP_PROJECT')
        )
        
        # メタデータサーバーが利用可能か確認（Cloud Run環境の指標）
        if not is_cloud_run:
            try:
                import requests
                response = requests.get(
                    "http://metadata.google.internal/computeMetadata/v1/instance",
                    headers={"Metadata-Flavor": "Google"},
                    timeout=1
                )
                if response.status_code == 200:
                    is_cloud_run = True
            except:
                pass
        
        # Secret Managerから認証情報を取得を試みる（Cloud Run環境でも優先）
        if SECRET_MANAGER_AVAILABLE and SecretManagerUtils.is_available():
            try:
                # Secret Managerから認証情報JSONを取得
                credential_secret = SecretManagerUtils.get_secret("bigquery-credentials-json")
                if credential_secret:
                    # 一時ファイルに保存
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        f.write(credential_secret)
                        temp_cred_path = f.name
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_cred_path
                    if is_cloud_run:
                        self.logger.info("Google credentials loaded from Secret Manager in Cloud Run environment")
                    else:
                        self.logger.info("Google credentials loaded from Secret Manager")
                    return
            except Exception as e:
                if is_cloud_run:
                    # Cloud Run環境でSecret Managerから取得できない場合はエラー
                    self.logger.error(f"Failed to load credentials from Secret Manager in Cloud Run environment: {e}")
                    raise ValueError(
                        f"Failed to load credentials from Secret Manager in Cloud Run environment: {e}. "
                        "Please ensure the Secret Manager secret 'bigquery-credentials-json' exists and the service account has permission to access it."
                    )
                else:
                    self.logger.warning(f"Failed to load credentials from Secret Manager, falling back to file: {e}")
        
        # Cloud Run環境でSecret Managerから取得できない場合はエラー
        if is_cloud_run:
            raise ValueError(
                "Secret Manager is not available in Cloud Run environment. "
                "Please ensure Secret Manager is configured and the service account has permission to access secrets."
            )
        
        # ローカル環境: ファイルから読み込む（フォールバック）
        credentials_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_file:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set in secrets.env")

        credentials_path = self.base_path / 'config' / credentials_file
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {credentials_path}\n"
                f"Expected file: {credentials_file}\n"
                f"Looking in: {self.base_path / 'config'}"
            )

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_path.absolute())
        self.logger.info(f"Google credentials set: {credentials_path}")
        # 確認のために環境変数を追加で出力
        self.logger.debug(f"GOOGLE_APPLICATION_CREDENTIALS is set to: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

    @property
    def log_dir(self):
        """ログディレクトリのパスを取得"""
        log_dir = self.base_path / 'logs'
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    @property
    def credentials_path(self):
        """認証情報ファイルのパスを取得（Secret Managerから取得した一時ファイルまたはローカルファイル）"""
        # 環境変数から取得（Secret Managerから取得した一時ファイルまたはローカルファイル）
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if credentials_path:
            # 絶対パスの場合はそのまま返す（Secret Managerから取得した一時ファイル）
            if Path(credentials_path).is_absolute():
                return credentials_path
            
            # 相対パスの場合は config ディレクトリを追加
            full_path = self.base_path / 'config' / credentials_path
            if full_path.exists():
                return str(full_path.absolute())
            else:
                # ファイルが存在しない場合は警告を出してNoneを返す
                self.logger.warning(f"Credentials file not found: {full_path}")
                return None
        
        return None

    @property
    def debug_mode(self):
        """デバッグモードの有効化"""
        try:
            return self.config[self.env].getboolean('DEBUG')
        except KeyError:
            self.logger.warning("DEBUG setting not found; defaulting to False.")
            return False

    @property
    def log_level(self):
        """ログレベルの取得"""
        try:
            return self.config[self.env]['LOG_LEVEL']
        except KeyError:
            self.logger.warning("LOG_LEVEL setting not found; defaulting to INFO.")
            return 'INFO'

    @property
    def progress_table_id(self):
        """BigQuery進行状況トラッキングテーブルのIDを取得"""
        try:
            return (
                f"{self.config['BIGQUERY']['PROJECT_ID']}."
                f"{self.config['BIGQUERY']['DATASET_ID']}."
                f"{self.config['BIGQUERY']['PROGRESS_TABLE_ID']}"
            )
        except KeyError as e:
            self.logger.error(f"Missing BigQuery tracking table setting: {e}")
            raise

    def get_config_value(self, section, key, default=None):
        """指定されたセクションとキーの設定値を取得"""
        try:
            return self.config.get(section, key, fallback=default)
        except KeyError as e:
            self.logger.error(f"Missing configuration for {section}.{key}: {e}")
            raise

    def get_config_file(self, file_name: str = "settings.ini") -> Path:
        """
        設定ファイルのパスを取得します。

        Args:
            file_name (str): 設定ファイル名

        Returns:
            Path: 設定ファイルのパス

        Raises:
            FileNotFoundError: 指定された設定ファイルが見つからない場合
        """
        return EnvironmentUtils.get_config_file(file_name)

    def __str__(self):
        return f"Config(env={self.env}, base_path={self.base_path})"

# グローバルインスタンスの作成
config = Config()
