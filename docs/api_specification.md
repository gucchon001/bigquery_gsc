# API仕様書

## 1. 概要

このドキュメントでは、GSC Data Scraperシステムで使用される外部APIと内部APIの仕様を定義します。

## 2. 外部API

### 2.1 Google Search Console API

#### 2.1.1 エンドポイント

```
POST https://www.googleapis.com/webmasters/v3/sites/{siteUrl}/searchAnalytics/query
```

#### 2.1.2 認証

- **方式**: OAuth 2.0 Service Account
- **スコープ**: `https://www.googleapis.com/auth/webmasters.readonly`

#### 2.1.3 リクエストパラメータ

```json
{
  "startDate": "2024-01-01",
  "endDate": "2024-01-01",
  "dimensions": ["query", "page"],
  "rowLimit": 25000,
  "startRow": 0
}
```

**パラメータ説明**:
- `startDate`: 開始日（YYYY-MM-DD形式）
- `endDate`: 終了日（YYYY-MM-DD形式）
- `dimensions`: 取得するディメンション（query, page）
- `rowLimit`: 取得する最大行数（最大25,000）
- `startRow`: 開始行位置（ページネーション用）

#### 2.1.4 レスポンス

```json
{
  "rows": [
    {
      "keys": ["query1", "https://example.com/page1"],
      "clicks": 100,
      "impressions": 1000,
      "position": 3.5
    }
  ]
}
```

**レスポンスフィールド**:
- `rows`: データ行の配列
  - `keys`: ディメンション値の配列 [query, page]
  - `clicks`: クリック数
  - `impressions`: インプレッション数
  - `position`: 平均順位

#### 2.1.5 エラーハンドリング

- **400 Bad Request**: 無効なリクエストパラメータ
- **401 Unauthorized**: 認証エラー
- **403 Forbidden**: アクセス権限なし
- **429 Too Many Requests**: レート制限超過
- **500 Internal Server Error**: サーバーエラー

#### 2.1.6 レート制限

- **1日あたり**: 2,000リクエスト（デフォルト）
- **1分あたり**: 600リクエスト
- **実装での制限**: 1日200回（設定可能）

### 2.2 Google Chat Webhook API

#### 2.2.1 エンドポイント

```
POST {Webhook_URL}
```

#### 2.2.2 認証

- **方式**: Webhook URL（Secret Managerから取得）
- **認証**: URLに含まれるトークンで認証

#### 2.2.3 リクエスト形式

**成功通知**:
```json
{
  "cards": [
    {
      "header": {
        "title": "GSC Scraper 実行成功",
        "subtitle": "実行時刻: 2026-01-06 11:00:00",
        "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/check_circle/default/48px.svg",
        "imageStyle": "IMAGE"
      },
      "sections": [
        {
          "widgets": [
            {
              "textParagraph": {
                "text": "✅ **GSC Scraper 実行成功**\n\nGSCデータの取得とBigQueryへの保存が正常に完了しました。\n\n**実行時刻:** 2026-01-06 11:00:00\n\n**日ごとの処理結果:**\n- 2026-01-04: 1,234件\n- 2026-01-03: スキップ\n- 2026-01-02: 567件\n\n**合計:** 1,801件"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

**エラー通知**:
```json
{
  "cards": [
    {
      "header": {
        "title": "GSC Scraper 実行エラー",
        "subtitle": "実行時刻: 2026-01-06 11:00:00",
        "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/error/default/48px.svg",
        "imageStyle": "IMAGE"
      },
      "sections": [
        {
          "widgets": [
            {
              "textParagraph": {
                "text": "❌ **GSC Scraper 実行エラー**\n\n**エラータイプ:** Main Process Error\n\n**エラーメッセージ:** ValueError: Invalid date format\n\n**実行環境:** development\n\n**詳細:**\n```\nTraceback (most recent call last):\n  File \"src/main.py\", line 68, in main\n    process_gsc_data()\n  ...\n```"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

#### 2.2.4 レスポンス

- **成功**: HTTP 200 OK
- **エラー**: HTTP 4xx/5xx

### 2.3 BigQuery API

#### 2.3.1 認証

- **方式**: Service Account認証
- **スコープ**: `https://www.googleapis.com/auth/bigquery`

#### 2.3.2 データ挿入

**メソッド**: `insert_rows_json()`

**パラメータ**:
- `table_id`: テーブルID（`project.dataset.table`形式）
- `rows`: 挿入する行データのリスト

**データ形式**:
```python
[
  {
    "data_date": "2024-01-01",
    "url": "https://example.com/page1",
    "query": "query1",
    "impressions": 1000,
    "clicks": 100,
    "avg_position": 3.5,
    "insert_time_japan": "2024-01-01 12:00:00"
  }
]
```

#### 2.3.3 クエリ実行

**進捗情報取得**:
```sql
SELECT data_date, record_position, is_date_completed
FROM `project.dataset.T_progress_tracking`
ORDER BY data_date DESC, updated_at DESC
LIMIT 1
```

**完了日付取得**:
```sql
SELECT data_date
FROM `project.dataset.T_progress_tracking`
WHERE is_date_completed = TRUE
  AND data_date IN UNNEST(@dates)
```

**進捗保存（MERGE）**:
```sql
MERGE `project.dataset.T_progress_tracking` T
USING (SELECT @data_date AS data_date) S
ON T.data_date = S.data_date
WHEN MATCHED THEN
    UPDATE SET 
        record_position = @record_position,
        is_date_completed = @is_date_completed,
        updated_at = @updated_at
WHEN NOT MATCHED THEN
    INSERT (data_date, record_position, is_date_completed, updated_at)
    VALUES (@data_date, @record_position, @is_date_completed, @updated_at)
```

## 3. 内部API（関数・クラス）

### 3.1 GSCConnector

#### 3.1.1 クラス定義

```python
class GSCConnector:
    def __init__(self, config: Config)
    def fetch_records(self, date: str, start_record: int, limit: int) -> Tuple[List[Dict], int]
    def insert_to_bigquery(self, records: List[Dict], date: str) -> None
    def _get_bigquery_credentials(self) -> Credentials
```

#### 3.1.2 fetch_records()

**シグネチャ**:
```python
def fetch_records(self, date: str, start_record: int, limit: int) -> Tuple[List[Dict], int]
```

**パラメータ**:
- `date`: データ取得日（YYYY-MM-DD形式）
- `start_record`: 開始レコード位置
- `limit`: 取得する最大レコード数

**戻り値**:
- `Tuple[List[Dict], int]`: (取得したレコードリスト, 次の開始位置)

**例外**:
- `HttpError`: GSC API呼び出しエラー
- `Exception`: その他のエラー

#### 3.1.3 insert_to_bigquery()

**シグネチャ**:
```python
def insert_to_bigquery(self, records: List[Dict], date: str) -> None
```

**パラメータ**:
- `records`: GSCから取得したレコードリスト
- `date`: データ取得日（YYYY-MM-DD形式）

**処理**:
1. レコードをURLごとに集計
2. BigQueryに挿入
3. リトライロジックで確実に保存

**例外**:
- `Exception`: BigQuery挿入エラー

### 3.2 process_gsc_data()

#### 3.2.1 関数定義

```python
def process_gsc_data() -> None
```

**処理フロー**:
1. 初期実行フラグの確認
2. 進捗情報の取得
3. 日付リストの生成
4. 各日付に対してデータ取得・保存
5. 成功通知の送信

**例外**:
- `Exception`: 処理中のエラー（通知送信後、再発生）

### 3.3 WebhookNotifier

#### 3.3.1 クラス定義

```python
class WebhookNotifier:
    def __init__(self, webhook_url: Optional[str] = None)
    def send_success_notification(
        self,
        message: str,
        daily_results: Optional[List[Dict]] = None,
        context: Optional[dict] = None
    ) -> bool
    def send_error_notification(
        self,
        error: Exception,
        error_type: str,
        context: Optional[dict] = None
    ) -> bool
```

#### 3.3.2 send_success_notification()

**シグネチャ**:
```python
def send_success_notification(
    self,
    message: str,
    daily_results: Optional[List[Dict]] = None,
    context: Optional[dict] = None
) -> bool
```

**パラメータ**:
- `message`: 通知メッセージ
- `daily_results`: 日付ごとの処理結果
  - `date`: 日付（文字列）
  - `records`: 取得件数
  - `status`: ステータス（"取得" or "スキップ"）
- `context`: 追加コンテキスト（現在は使用しない）

**戻り値**:
- `bool`: 送信成功時True、失敗時False

#### 3.3.3 send_error_notification()

**シグネチャ**:
```python
def send_error_notification(
    self,
    error: Exception,
    error_type: str,
    context: Optional[dict] = None
) -> bool
```

**パラメータ**:
- `error`: 発生したエラー
- `error_type`: エラーの種類
- `context`: 追加コンテキスト（実行環境など）

**戻り値**:
- `bool`: 送信成功時True、失敗時False

### 3.4 ユーティリティ関数

#### 3.4.1 aggregate_records()

**シグネチャ**:
```python
def aggregate_records(records: List[Dict]) -> List[Dict]
```

**処理**:
- URLとクエリの組み合わせごとに集計
- クリック数、インプレッション数を合計
- 平均順位を計算

**戻り値**:
- `List[Dict]`: 集計後のレコードリスト

#### 3.4.2 normalize_url()

**シグネチャ**:
```python
def normalize_url(url: str) -> str
```

**処理**:
- クエリパラメータを除去
- フラグメント識別子を除去

**戻り値**:
- `str`: 正規化されたURL

#### 3.4.3 insert_rows_with_retry()

**シグネチャ**:
```python
def insert_rows_with_retry(
    client: bigquery.Client,
    table_id: str,
    rows_to_insert: list,
    logger: logging.Logger,
    max_retries: int = 5,
    retry_delay: int = 10
) -> None
```

**処理**:
- BigQueryへのデータ挿入をリトライロジックで実行
- 最大5回までリトライ
- 10秒間隔でリトライ

**例外**:
- `Exception`: 最大リトライ回数に達した場合

## 4. データ形式

### 4.1 GSC APIレスポンス

```python
{
    "rows": [
        {
            "keys": ["query", "url"],
            "clicks": 100,
            "impressions": 1000,
            "position": 3.5
        }
    ]
}
```

### 4.2 集計後データ

```python
[
    {
        "query": "query",
        "url": "https://example.com/page",
        "clicks": 100,
        "impressions": 1000,
        "avg_position": 3.5
    }
]
```

### 4.3 BigQuery挿入データ

```python
[
    {
        "data_date": "2024-01-01",
        "url": "https://example.com/page",
        "query": "query",
        "impressions": 1000,
        "clicks": 100,
        "avg_position": 3.5,
        "insert_time_japan": "2024-01-01 12:00:00"
    }
]
```

## 5. エラーハンドリング

### 5.1 エラー分類

1. **認証エラー**: 認証情報の取得・検証失敗
2. **APIエラー**: 外部API呼び出し失敗
3. **データエラー**: データ形式不正、バリデーションエラー
4. **システムエラー**: 予期しないエラー

### 5.2 エラー処理フロー

```
エラー発生
    │
    ├─ ログ記録（Cloud Logging）
    │
    ├─ エラー通知（Google Chat）
    │
    └─ 例外再発生（ジョブ終了）
```

### 5.3 リトライ戦略

- **GSC API**: 最大3回、5秒間隔
- **BigQuery**: 最大5回、10秒間隔
- **通知**: リトライなし（失敗時はログのみ）

## 6. パフォーマンス

### 6.1 API呼び出し制限

- **1日あたり**: 200回（設定可能）
- **バッチサイズ**: 25,000件（設定可能）
- **並列処理**: 現在はシーケンシャル処理

### 6.2 データ処理速度

- **URL正規化**: メモリ内処理、高速
- **データ集計**: pandas使用、効率的
- **BigQuery挿入**: バッチ処理、最適化済み

### 6.3 最適化ポイント

- 完了済み日付のスキップ
- 進捗情報のキャッシュ（将来実装）
- 並列処理の実装（将来実装）

