# アーキテクチャドキュメント

## 1. システムアーキテクチャ概要

### 1.1 全体構成

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                     │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │Cloud Scheduler│─────▶│Cloud Run Jobs│                    │
│  └──────────────┘      └──────┬───────┘                    │
│                                │                             │
│         ┌──────────────────────┼──────────────────────┐    │
│         │                      │                      │    │
│         ▼                      ▼                      ▼    │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────┐│
│  │Secret Manager│      │   BigQuery    │      │GSC API  ││
│  └──────────────┘      └──────────────┘      └─────────┘│
│         │                      │                      │    │
│         └──────────────────────┼──────────────────────┘    │
│                                │                             │
│                                ▼                             │
│                         ┌──────────────┐                    │
│                         │Google Chat   │                    │
│                         │(通知)        │                    │
│                         └──────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 コンポーネント構成

```
src/
├── main.py                    # エントリーポイント
├── modules/
│   ├── gsc_handler.py        # メイン処理ロジック
│   ├── gsc_fetcher.py        # GSC API通信
│   └── date_initializer.py   # 日付範囲初期化
└── utils/
    ├── environment.py        # 環境設定・認証
    ├── webhook_notifier.py   # 通知機能
    ├── logging_config.py     # ログ設定
    ├── date_utils.py         # 日付ユーティリティ
    ├── url_utils.py          # URL処理
    └── retry.py              # リトライロジック
```

## 2. コンポーネント詳細

### 2.1 main.py

**役割**: アプリケーションのエントリーポイント

**主要処理**:
1. 環境設定の読み込み
2. 進捗テーブルのクリーンアップ
3. GSCデータ処理の実行
4. エラーハンドリングと通知

**依存関係**:
- `modules.gsc_handler`: メイン処理
- `utils.webhook_notifier`: 通知機能
- `utils.environment`: 環境設定

### 2.2 gsc_handler.py

**役割**: GSCデータ取得とBigQuery保存のメイン処理

**主要機能**:
- `process_gsc_data()`: メイン処理ロジック
- `cleanup_progress_table()`: 進捗テーブルのクリーンアップ
- `get_completed_dates()`: 完了済み日付の取得
- `check_if_date_completed()`: 日付完了チェック
- `save_processing_position()`: 進捗保存
- `get_last_processed_position()`: 前回処理位置の取得

**データフロー**:
```
1. 進捗情報取得
2. 日付リスト生成
3. 各日付に対して:
   a. 完了チェック
   b. データ取得
   c. BigQuery保存
   d. 進捗更新
4. 通知送信
```

### 2.3 gsc_fetcher.py

**役割**: Google Search Console APIとの通信

**主要クラス**:
- `GSCConnector`: GSC API接続クラス

**主要メソッド**:
- `fetch_records()`: レコード取得
- `insert_to_bigquery()`: BigQueryへの挿入
- `_get_bigquery_credentials()`: BigQuery認証情報取得

**認証**:
- サービスアカウント認証
- Cloud Run環境ではSecret Managerから取得

### 2.4 environment.py

**役割**: 環境設定と認証情報の管理

**主要クラス**:
- `EnvironmentUtils`: 環境変数・設定ファイル操作
- `Config`: 設定管理クラス

**主要機能**:
- `_load_secrets()`: Secret Managerまたはファイルから環境変数読み込み
- `_setup_credentials()`: 認証情報の設定
- `_load_gsc_settings()`: GSC設定の読み込み

**認証情報の取得順序**:
1. Secret Manager（Cloud Run環境）
2. 環境変数 `GOOGLE_APPLICATION_CREDENTIALS`
3. デフォルトサービスアカウント（Cloud Run）

### 2.5 webhook_notifier.py

**役割**: Google Chatへの通知送信

**主要クラス**:
- `WebhookNotifier`: 通知送信クラス

**主要メソッド**:
- `send_success_notification()`: 成功通知
- `send_error_notification()`: エラー通知
- `_build_success_message()`: 成功メッセージ構築
- `_build_error_message()`: エラーメッセージ構築

**通知形式**:
- Google Chat Card形式
- 成功時: 日付ごとの取得件数、スキップ情報
- エラー時: エラーメッセージ、トレースバック

## 3. データフロー

### 3.1 正常処理フロー

```
┌─────────────┐
│main.py起動  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│環境設定読み込み │
│(environment.py) │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│進捗テーブル     │
│クリーンアップ   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│進捗情報取得     │
│(BigQuery)       │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│日付リスト生成   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│各日付処理       │
│  ├─完了チェック │
│  ├─データ取得   │
│  │  (GSC API)   │
│  ├─データ集計   │
│  ├─BigQuery保存 │
│  └─進捗更新     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│成功通知送信     │
│(Google Chat)    │
└─────────────────┘
```

### 3.2 エラー処理フロー

```
┌─────────────┐
│エラー発生   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│エラーログ記録   │
│(Cloud Logging)  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│エラー通知送信   │
│(Google Chat)    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ジョブ終了       │
│(エラーコード)   │
└─────────────────┘
```

## 4. データモデル

### 4.1 BigQueryテーブル構造

#### T_searchdata_site_impression

```sql
CREATE TABLE `past_gsc_202411.T_searchdata_site_impression` (
  data_date DATE,
  url STRING,
  query STRING,
  impressions INTEGER,
  clicks INTEGER,
  avg_position FLOAT,
  insert_time_japan DATETIME
)
```

#### T_progress_tracking

```sql
CREATE TABLE `past_gsc_202411.T_progress_tracking` (
  data_date DATE,
  record_position INTEGER,
  is_date_completed BOOL,
  updated_at DATETIME
)
```

### 4.2 データ関係

```
T_progress_tracking (進捗管理)
    │
    ├─ data_date → T_searchdata_site_impression.data_date
    │
    └─ is_date_completed: 日付の処理完了フラグ
```

## 5. 認証・認可

### 5.1 認証フロー

```
┌─────────────────┐
│Cloud Run Jobs   │
│起動             │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│環境判定         │
│(Cloud Run?)     │
└──────┬──────────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌─────┐ ┌──────────────┐
│Yes  │ │No            │
└──┬──┘ └──┬───────────┘
   │       │
   ▼       ▼
┌──────────────┐ ┌──────────────┐
│Secret Manager│ │secrets.env  │
│認証情報取得  │ │ファイル読み │
└──────┬───────┘ └──────┬───────┘
       │                │
       └───────┬────────┘
               │
               ▼
       ┌──────────────┐
       │認証情報設定   │
       │(環境変数)    │
       └──────┬───────┘
              │
              ▼
       ┌──────────────┐
       │API呼び出し    │
       └──────────────┘
```

### 5.2 権限管理

**サービスアカウント**: `jukust-gcs@bigquery-jukust.iam.gserviceaccount.com`

**必要な権限**:
- `roles/bigquery.dataEditor`: BigQueryデータ編集
- `roles/secretmanager.secretAccessor`: Secret Manager読み取り
- `roles/logging.logWriter`: Cloud Logging書き込み
- Google Search Console API読み取り権限

## 6. エラーハンドリング

### 6.1 エラー分類

1. **認証エラー**: Secret Managerアクセス失敗、認証情報不正
2. **APIエラー**: GSC API呼び出し失敗、レート制限
3. **BigQueryエラー**: データ挿入失敗、クエリエラー
4. **ネットワークエラー**: タイムアウト、接続失敗

### 6.2 リトライ戦略

- **API呼び出し**: 最大3回、5秒間隔
- **BigQuery挿入**: 最大5回、10秒間隔
- **指数バックオフ**: 実装予定

### 6.3 エラー通知

- すべてのエラーをGoogle Chatに通知
- スタックトレースを含む詳細情報
- 実行環境情報を含む

## 7. パフォーマンス最適化

### 7.1 バッチ処理

- **バッチサイズ**: 25,000件
- **API呼び出し制限**: 1日200回
- **並列処理**: 将来実装予定

### 7.2 データ処理

- **URL正規化**: メモリ内で処理
- **データ集計**: pandasを使用
- **BigQuery挿入**: バッチ挿入で効率化

### 7.3 進捗管理

- **クリーンアップ**: 90分より古いデータのみ削除
- **ストリーミングバッファ**: 制約を考慮した設計

## 8. セキュリティ

### 8.1 認証情報管理

- **Secret Manager**: Cloud Run環境で使用
- **環境変数**: ローカル環境で使用
- **コード内埋め込み**: 禁止

### 8.2 アクセス制御

- **最小権限の原則**: 必要最小限の権限のみ付与
- **サービスアカウント**: 専用アカウントを使用
- **IAM**: 適切なロールバインディング

### 8.3 データ保護

- **暗号化**: GCPのデフォルト暗号化
- **ログ**: 機密情報を含まない
- **通知**: エラーメッセージのみ送信

## 9. 拡張性

### 9.1 水平スケーリング

- Cloud Run Jobsは自動スケーリング
- 同時実行数の制御可能

### 9.2 機能拡張

- **複数サイト対応**: 設定ファイルで複数サイト定義
- **カスタムメトリクス**: 設定で追加可能
- **通知チャネル**: 複数チャネル対応可能

### 9.3 データ拡張

- **追加ディメンション**: GSC APIで取得可能な項目を追加
- **集計ロジック**: カスタム集計関数の追加
- **データ変換**: ETLパイプラインの拡張

