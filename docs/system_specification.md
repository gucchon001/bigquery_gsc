# システム仕様書

## 1. システム概要

### 1.1 目的

Google Search Console（GSC）から検索パフォーマンスデータを取得し、BigQueryに保存する自動化システムです。Cloud Run Jobsで定期実行され、データの継続的な収集を実現します。

### 1.2 対象ユーザー

- **データアナリスト**: SEOデータを分析し、ビジネスインテリジェンスツールで活用
- **マーケティング担当者**: 検索パフォーマンスの推移を監視
- **開発者**: データ収集プロセスの自動化と運用

### 1.3 システムの特徴

- **サーバーレス**: Cloud Run Jobsで実行、VM管理不要
- **自動進捗管理**: 中断後も前回の位置から再開可能
- **通知機能**: Google Chatに成功・エラー通知を送信
- **セキュア**: Secret Managerで認証情報を管理
- **スケーラブル**: 大量データの処理に対応

## 2. 機能要件

### 2.1 GSCデータ取得機能

#### 2.1.1 データ取得範囲

- **初回実行時**: 過去365日分のデータを取得（設定可能）
- **定期実行時**: 過去3日分のデータを取得（設定可能）
- **制限**: GSC APIの制限により、2日前までのデータのみ取得可能

#### 2.1.2 取得データ項目

- **クエリ**: 検索クエリ文字列
- **ページ**: URL
- **クリック数**: クリックされた回数
- **インプレッション数**: 検索結果に表示された回数
- **平均順位**: 検索結果での平均表示位置

#### 2.1.3 API呼び出し制限

- **1日あたりの上限**: 200回（設定可能）
- **バッチサイズ**: 25,000件（設定可能）
- **リトライ**: 最大3回、5秒間隔（設定可能）

### 2.2 データ処理機能

#### 2.2.1 URL正規化

- クエリパラメータを除去
- フラグメント識別子を除去
- 同一URLとして扱う

#### 2.2.2 データ集計

- URLとクエリの組み合わせごとに集計
- クリック数、インプレッション数を合計
- 平均順位を計算

### 2.3 BigQuery保存機能

#### 2.3.1 データ挿入

- 集計されたデータをBigQueryに挿入
- リトライロジックで確実な保存
- バッチ処理で効率化

#### 2.3.2 テーブルスキーマ

```sql
data_date: DATE          -- データ取得日
url: STRING              -- URL（正規化済み）
query: STRING            -- 検索クエリ
impressions: INTEGER     -- インプレッション数
clicks: INTEGER          -- クリック数
avg_position: FLOAT       -- 平均順位
insert_time_japan: DATETIME -- 挿入時刻（JST）
```

### 2.4 進捗管理機能

#### 2.4.1 進捗テーブル

- **テーブル名**: `T_progress_tracking`
- **用途**: 各日付の処理状況を記録

#### 2.4.2 進捗情報

- `data_date`: 処理対象日付
- `record_position`: 最後に処理したレコード位置
- `is_date_completed`: 日付の処理完了フラグ
- `updated_at`: 更新時刻

#### 2.4.3 再開機能

- 前回の処理位置から再開
- 完了済み日付はスキップ
- 中断後も継続処理可能

#### 2.4.4 クリーンアップ機能

- 古い進捗レコードを自動削除
- ストリーミングバッファの制約を考慮
- 90分より古いレコードを削除対象

### 2.5 通知機能

#### 2.5.1 成功通知

- **送信タイミング**: 処理正常終了時
- **通知内容**:
  - 実行時刻
  - 日付ごとの取得件数
  - スキップされた日付
  - 合計取得件数

#### 2.5.2 エラー通知

- **送信タイミング**: エラー発生時
- **通知内容**:
  - エラーメッセージ
  - エラータイプ
  - トレースバック情報
  - 実行環境情報

#### 2.5.3 通知チャネル

- Google Chat Webhook
- Secret ManagerからWebhook URLを取得

### 2.6 認証・認可機能

#### 2.6.1 認証方式

- **Cloud Run環境**: Secret Managerから認証情報を取得
- **ローカル環境**: `secrets.env`ファイルから認証情報を取得
- **フォールバック**: Cloud Runのデフォルトサービスアカウント

#### 2.6.2 必要な権限

- BigQuery Data Editor
- Secret Manager Secret Accessor
- Cloud Logging Log Writer
- Google Search Console API読み取り権限

## 3. 非機能要件

### 3.1 パフォーマンス

- **API呼び出し効率**: 1日あたり200回以内
- **データ処理速度**: バッチサイズ25,000件で最適化
- **BigQuery挿入**: リトライロジックで確実性を確保

### 3.2 可用性

- **再試行機能**: API呼び出し失敗時の自動リトライ
- **進捗保存**: 処理状況を常に保存し、中断後も再開可能
- **エラーハンドリング**: 詳細なエラー情報を記録

### 3.3 セキュリティ

- **認証情報管理**: Secret Managerで安全に管理
- **環境変数**: 機密情報をコードに埋め込まない
- **アクセス制御**: 最小権限の原則に従う

### 3.4 保守性

- **ログ出力**: 詳細なログで動作状況を記録
- **エラー追跡**: スタックトレースを含む詳細なエラー情報
- **設定管理**: 設定ファイルで柔軟に変更可能

## 4. 技術仕様

### 4.1 実行環境

- **プラットフォーム**: Google Cloud Run Jobs
- **ランタイム**: Python 3.11
- **メモリ**: 2GB（設定可能）
- **CPU**: 1コア（設定可能）
- **タイムアウト**: 3時間（設定可能）

### 4.2 依存ライブラリ

主要な依存関係：

- `google-cloud-bigquery>=3.11.0`: BigQuery操作
- `google-api-python-client==2.108.0`: GSC API呼び出し
- `google-cloud-secret-manager>=2.16.0`: Secret Manager操作
- `google-cloud-logging>=3.8.0`: Cloud Logging
- `requests==2.31.0`: HTTP通信
- `pandas`: データ処理

### 4.3 データベース

- **プラットフォーム**: Google BigQuery
- **リージョン**: asia-northeast1
- **データセット**: `past_gsc_202411`
- **テーブル**: `T_searchdata_site_impression`
- **進捗テーブル**: `T_progress_tracking`

### 4.4 外部API

- **Google Search Console API**: データ取得
- **Google Chat Webhook API**: 通知送信

## 5. データフロー

### 5.1 正常フロー

```
1. Cloud Scheduler → Cloud Run Jobs起動
2. Secret Manager → 認証情報取得
3. BigQuery → 進捗情報取得
4. GSC API → データ取得
5. データ集計・正規化
6. BigQuery → データ保存
7. BigQuery → 進捗更新
8. Google Chat → 成功通知送信
```

### 5.2 エラーフロー

```
1. エラー発生
2. エラー情報をログに記録
3. Google Chat → エラー通知送信
4. ジョブ終了（エラーコード返却）
```

## 6. 設定項目

### 6.1 settings.ini

主要な設定項目：

```ini
[GSC]
site_url = https://www.juku.st/
batch_size = 25000
daily_api_limit = 200
retry_count = 3
retry_delay = 5

[GSC_INITIAL]
initial_run = false

[GSC_DAILY]
initial_fetch_days = 365
daily_fetch_days = 3

[BIGQUERY]
project_id = bigquery-jukust
dataset_id = past_gsc_202411
table_id = T_searchdata_site_impression
progress_table_id = T_progress_tracking
```

### 6.2 環境変数（Secret Manager）

- `Webhook_URL`: Google Chat Webhook URL
- `GOOGLE_APPLICATION_CREDENTIALS`: BigQuery認証情報（JSON）

## 7. 制約事項

### 7.1 GSC API制約

- 2日前までのデータのみ取得可能
- 1日あたりのAPI呼び出し制限あり
- データ取得に時間がかかる場合がある

### 7.2 BigQuery制約

- ストリーミングバッファの制約により、直近のデータは削除不可
- 進捗テーブルのクリーンアップは90分より古いデータのみ対象

### 7.3 Cloud Run Jobs制約

- 最大実行時間: 24時間
- メモリ制限: 設定可能（推奨: 2GB以上）
- 同時実行数: 1（デフォルト）

## 8. 運用要件

### 8.1 定期実行

- **スケジュール**: Cloud Schedulerで設定
- **推奨頻度**: 1日1回（午前8時45分 JST）
- **実行時間**: 通常30分〜1時間

### 8.2 監視

- **ログ**: Cloud Loggingで確認
- **通知**: Google Chatで成功・エラーを通知
- **メトリクス**: BigQueryのデータ件数で確認

### 8.3 メンテナンス

- **進捗テーブル**: 自動クリーンアップ（90分より古いデータ）
- **ログローテーション**: Cloud Loggingで自動管理
- **設定変更**: `settings.ini`を更新後、再デプロイ

## 9. 将来の拡張

### 9.1 機能拡張候補

- 複数サイトの対応
- リアルタイム通知の強化
- データ品質チェック機能
- 自動リカバリー機能

### 9.2 パフォーマンス改善

- 並列処理の実装
- キャッシュ機能の追加
- データ圧縮の最適化

