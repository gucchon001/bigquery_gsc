# gsc_fetcher.py
import logging
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import bigquery
from utils.environment import EnvironmentUtils

logger = logging.getLogger(__name__)

class GSCConnector:
    """Google Search Console データを取得するクラス"""

    def __init__(self):
        # サービスアカウントファイルのパスを EnvironmentUtils から取得
        service_account_file = EnvironmentUtils.get_service_account_file()

        # サービスアカウント認証を設定
        credentials = service_account.Credentials.from_service_account_file(
            str(service_account_file),
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
        )

        # GSC API クライアントを構築
        self.service = build('searchconsole', 'v1', credentials=credentials)
        logger.info("Google Search Console API クライアントを初期化しました。")

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
        # プロパティ名を EnvironmentUtils から取得
        property_name = EnvironmentUtils.get_config_value("GSC", "property_name")

        request = {
            'startDate': date,
            'endDate': date,
            'dimensions': ['query', 'page'],
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

            logger.info(f"日付 {date} のレコードを {len(records)} 件取得しました。次の開始位置: {next_record}")

            return records, next_record

        except Exception as e:
            logger.error(f"GSC データの取得中にエラーが発生しました: {e}")
            raise

    def _initialize_gsc_service(self):
        """Initialize and return the GSC API service."""
        credentials = service_account.Credentials.from_service_account_file(
            self.config.credentials_path,
            scopes=['https://www.googleapis.com/auth/webmasters.readonly']
        )
        return build('searchconsole', 'v1', credentials=credentials, cache_discovery=False)

    def _create_table_id(self) -> str:
        """Create and return BigQuery Table ID."""
        return (
            f"{self.config.config['BIGQUERY']['PROJECT_ID']}."
            f"{self.config.config['BIGQUERY']['DATASET_ID']}."
            f"{self.config.config['BIGQUERY']['TABLE_ID']}"
        )

    def fetch_and_log_specific_query(self, start_date: str, query_contains=None, page_url=None):
        """Fetch all data from GSC for a specific date with pagination."""
        request_body = self._build_request_body(start_date, start_date, 25000, query_contains, page_url)
        all_rows = []
        start_row = 0
        
        while True:
            try:
                request_body["startRow"] = start_row
                response = self._fetch_gsc_data(request_body)
                rows = response.get('rows', [])
                
                if not rows:
                    break
                    
                transformed_rows = self._transform_response({"rows": rows}, start_date)
                all_rows.extend(transformed_rows)
                
                # 次のページがあるかチェック
                rows_count = len(rows)
                if rows_count < request_body["rowLimit"]:
                    break
                    
                start_row += rows_count
                self.logger.debug(f"Fetched {len(all_rows)} total rows so far...")
                
            except Exception as e:
                self.logger.error(f"Error fetching data: {e}", exc_info=True)
                break

        if all_rows:
            self.logger.debug(f"Fetched total of {len(all_rows)} rows from GSC")
        return all_rows

    def _build_request_body(self, start_date, end_date, row_limit=25000, query_contains=None, page_url=None):
        """Build request body with increased row limit."""
        filters = []
        if query_contains:
            filters.append({
                "dimension": "query",
                "operator": "contains",
                "expression": query_contains
            })
        if page_url:
            filters.append({
                "dimension": "page",
                "operator": "equals",
                "expression": page_url
            })
        return {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["page", "query", "device", "date"],
            "dimensionFilterGroups": [{"filters": filters}] if filters else [],
            "rowLimit": row_limit,
            "startRow": 0
        }

    def _fetch_gsc_data(self, request_body):
        """Query data from GSC API and return the response."""
        try:
            return self.service.searchanalytics().query(
                siteUrl=self.config.gsc_settings['site_url'],
                body=request_body
            ).execute()
        except HttpError as e:
            self.logger.error(f"HTTP error: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            raise

    def _transform_response(self, response, start_date):
        """Transform API response into a format suitable for BigQuery."""
        return [
            {
                'data_date': start_date,
                'site_url': row['keys'][0],
                'query': row['keys'][1],
                'device': row['keys'][2],
                'impressions': int(row.get('impressions', 0)),
                'clicks': int(row.get('clicks', 0)),
                'sum_top_position': float(row.get('position', 0)),
            } for row in response.get('rows', [])
        ]

    def insert_to_bigquery(self, records, date: str):
        """
        取得したGSCデータをBigQueryに挿入します。

        Args:
            records (list): GSCから取得したレコードのリスト
            date (str): データ取得対象の日付（YYYY-MM-DD）
        """
        from google.cloud import bigquery

        # BigQuery クライアントを初期化
        client = bigquery.Client()

        # 挿入先のテーブルを EnvironmentUtils から取得
        table_id = f"{EnvironmentUtils.get_config_value('BIGQUERY', 'PROJECT_ID')}." \
                   f"{EnvironmentUtils.get_config_value('BIGQUERY', 'DATASET_ID')}." \
                   f"{EnvironmentUtils.get_config_value('BIGQUERY', 'PROGRESS_TABLE_ID')}"

        # データの整形
        rows_to_insert = []
        for row in records:
            row_data = {
                "query": row['keys'][0],
                "page": row['keys'][1],
                "clicks": row.get('clicks', 0),
                "impressions": row.get('impressions', 0),
                "ctr": row.get('ctr', 0.0),
                "position": row.get('position', 0.0),
                "date": date  # 必要に応じて date を渡す
            }
            rows_to_insert.append(row_data)

        # データを挿入
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            logger.error(f"BigQuery へのデータ挿入中にエラーが発生しました: {errors}")
            raise RuntimeError(f"BigQuery insertion errors: {errors}")
        else:
            logger.info(f"BigQuery に {len(rows_to_insert)} 件のデータを挿入しました。")

    def _bq_schema(self):
        """Define and return the BigQuery table schema."""
        return [
            bigquery.SchemaField('data_date', 'DATE'),
            bigquery.SchemaField('site_url', 'STRING'),
            bigquery.SchemaField('query', 'STRING'),
            bigquery.SchemaField('device', 'STRING'),
            bigquery.SchemaField('impressions', 'INTEGER'),
            bigquery.SchemaField('clicks', 'INTEGER'),
            bigquery.SchemaField('sum_top_position', 'FLOAT')
        ]

    def fetch_and_insert_gsc_data(self, start_date=None, end_date=None):
        """Fetch GSC data for the given period and insert into BigQuery."""
        start_date = start_date or self.config.gsc_settings['start_date']
        end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        request_body = self._build_request_body(
            start_date, end_date,
            self.config.gsc_settings['batch_size']
        )
        try:
            response = self._fetch_gsc_data(request_body)
            rows = self._transform_response(response, start_date)
            if rows:
                self.insert_to_bigquery(rows)
        except Exception as e:
            self._handle_error(e)

    def _handle_error(self, exception):
        """Unified error handling."""
        error_message = "GSC API error" if isinstance(exception, HttpError) else f"Unexpected error: {exception}"
        self.logger.error(error_message, exc_info=True)

    def update_progress_tracking(self, date, completed, last_row=None):
        """
        進捗追跡テーブルを更新
        Args:
            date: 対象日付
            completed: 完了ステータス
            last_row: 最後に取得した行番号
        """
        client = bigquery.Client()
        table_id = f"{self.config.config['BIGQUERY']['PROJECT_ID']}.{self.config.config['BIGQUERY']['DATASET_ID']}.T_progress_tracking"
        
        rows_to_insert = [{
            "data_date": str(date),
            "batch_completed": completed,
            "last_processed_row": last_row,
            "updated_at": datetime.utcnow().isoformat()
        }]
        
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            raise RuntimeError(f"Failed to update progress tracking for {date}: {errors}")
        self.logger.info(f"Progress updated for {date} with status: {completed}, last row: {last_row}")

    def fetch_records(self, date: str, start_record: int, limit: int):
            """指定位置からレコードを取得"""
            request_body = self._build_request_body(date, date, limit)
            request_body["startRow"] = start_record
            
            try:
                response = self._fetch_gsc_data(request_body)
                rows = response.get('rows', [])
                
                if not rows:
                    return [], start_record
                    
                transformed_rows = self._transform_response({"rows": rows}, date)
                return transformed_rows, start_record + len(transformed_rows)
                
            except Exception as e:
                self.logger.error(f"Error fetching records: {e}", exc_info=True)
                raise