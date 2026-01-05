# src/modules/gsc_fetcher.py

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import bigquery
from utils.date_utils import get_current_jst_datetime, format_datetime_jst
from utils.url_utils import aggregate_records
from datetime import datetime
from utils.retry import insert_rows_with_retry

from utils.logging_config import get_logger
from utils.webhook_notifier import send_error_notification

logger = get_logger(__name__)

class GSCConnector:
    """Google Search Console データを取得するクラス"""

    def __init__(self, config):
        """
        コンストラクタ

        Args:
            config (Config): Config クラスのインスタンス
        """
        self.config = config
        self.logger = get_logger(__name__)  # ロガーを初期化

        # 認証情報ファイルのパスを Config から取得
        credentials_path = self.config.credentials_path

        if not credentials_path:
            raise ValueError("Credentials path not set in config.")

        # サービスアカウント認証を設定
        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
        )

        # GSC API クライアントを構築
        self.service = build('searchconsole', 'v1', credentials=credentials)
        self.logger.info("Google Search Console API クライアントを初期化しました。")

    def fetch_records(self, date: str, start_record: int, limit: int):
        """
        指定された日付のGSCデータをフェッチします。

        Args:
            date (str): データ取得対象の日付（YYYY-MM-DD）
            start_record (int): 取得開始位置
            limit (int): 取得するレコード数

        Returns:
            tuple: (取得したレコードリスト, 次のレコード位置)
        """
        property_name = self.config.gsc_settings['url']  # 'site_url' を 'url' に変更

        request = {
            'startDate': date,
            'endDate': date,
            'dimensions': ['query', 'page'],  # 必要に応じて調整
            'rowLimit': limit,
            'startRow': start_record
        }

        try:
            response = self.service.searchanalytics().query(
                siteUrl=property_name,
                body=request
            ).execute()

            records = response.get('rows', [])
            next_record = start_record + len(records)

            self.logger.info(f"日付 {date} のレコードを {len(records)} 件取得しました。次の開始位置: {next_record}")

            return records, next_record

        except HttpError as e:
            self.logger.error(f"GSC API HTTP エラー: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"GSC データの取得中にエラーが発生しました: {e}", exc_info=True)
            raise

    def insert_to_bigquery(self, records, date: str):
        """
        取得したGSCデータをBigQueryに挿入します。

        Args:
            records (list): GSCから取得したレコードのリスト
            date (str): データ取得対象の日付（YYYY-MM-DD）
        """
        # データの集計
        aggregated_records = aggregate_records(records)

        if not aggregated_records:
            self.logger.info("集計後のレコードがありません。")
            return

        # BigQuery クライアントを初期化
        client = bigquery.Client(
            credentials=self._get_bigquery_credentials(),
            project=self.config.get_config_value('BIGQUERY', 'PROJECT_ID')
        )

        # 挿入先のテーブルIDを取得
        table_id = f"{self.config.get_config_value('BIGQUERY', 'PROJECT_ID')}." \
                   f"{self.config.get_config_value('BIGQUERY', 'DATASET_ID')}." \
                   f"{self.config.get_config_value('BIGQUERY', 'TABLE_ID')}"

        # データの整形
        rows_to_insert = []
        for record in aggregated_records:
            row_data = {
                "data_date": date,
                "url": record['url'],
                "query": record['query'],
                "impressions": record['impressions'],
                "clicks": record['clicks'],
                "avg_position": record['avg_position'],  # フィールド名を統一
                "insert_time_japan": format_datetime_jst(get_current_jst_datetime())  # DATETIME 型
            }
            rows_to_insert.append(row_data)

        # リトライロジック付きで挿入
        try:
            insert_rows_with_retry(client, table_id, rows_to_insert, self.logger)
        except Exception as e:
            self.logger.error(f"BigQueryへの挿入が失敗しました: {e}", exc_info=True)
            # エラー通知を送信
            send_error_notification(
                error=e,
                error_type="BigQuery Insertion Error",
                context={
                    "date": date,
                    "record_count": len(rows_to_insert)
                }
            )
            raise

    def fetch_and_insert_gsc_data(self, start_date=None, end_date=None):
        """
        指定された期間のGSCデータを取得し、BigQueryに挿入します。

        Args:
            start_date (str, optional): 開始日付（YYYY-MM-DD）
            end_date (str, optional): 終了日付（YYYY-MM-DD）
        """
        start_date = start_date or self.config.gsc_settings['start_date']
        end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        batch_size = self.config.gsc_settings['batch_size']

        try:
            records, _ = self.fetch_records(start_date, 0, batch_size)
            if records:
                self.insert_to_bigquery(records, start_date)
        except Exception as e:
            self._handle_error(e)

    def _handle_error(self, exception):
        """Unified error handling."""
        error_message = "GSC API error" if isinstance(exception, HttpError) else f"Unexpected error: {exception}"
        self.logger.error(error_message, exc_info=True)

    def _get_bigquery_credentials(self):
        """BigQuery 用の認証情報を取得します。"""
        credentials_path = self.config.credentials_path
        return service_account.Credentials.from_service_account_file(str(credentials_path))

    def _bq_schema(self):
        """Define and return the BigQuery table schema."""
        return [
            bigquery.SchemaField('data_date', 'DATE'),
            bigquery.SchemaField('url', 'STRING'),
            bigquery.SchemaField('query', 'STRING'),
            bigquery.SchemaField('impressions', 'INTEGER'),
            bigquery.SchemaField('clicks', 'INTEGER'),
            bigquery.SchemaField('avg_position', 'FLOAT'),  # フィールド名を統一
            bigquery.SchemaField('insert_time_japan', 'DATETIME')  # DATETIME 型
        ]