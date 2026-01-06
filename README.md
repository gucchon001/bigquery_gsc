# GSC Data Scraper for BigQuery

Google Search Console（GSC）からデータを取得し、BigQueryに保存する自動化システムです。Cloud Run Jobsで定期実行され、Google Chatに通知を送信します。

## 📋 目次

- [システム概要](#システム概要)
- [主要機能](#主要機能)
- [アーキテクチャ](#アーキテクチャ)
- [セットアップ](#セットアップ)
- [実行方法](#実行方法)
- [設定](#設定)
- [デプロイ](#デプロイ)
- [トラブルシューティング](#トラブルシューティング)
- [ドキュメント](#ドキュメント)

## システム概要

このシステムは、Google Search Console APIから検索パフォーマンスデータを取得し、BigQueryに保存するための自動化ツールです。

### 主な特徴

- **サーバーレス実行**: Cloud Run Jobsで実行され、VM管理が不要
- **自動進捗管理**: BigQueryの進捗テーブルで処理状況を管理し、中断後も再開可能
- **通知機能**: Google Chatに成功・エラー通知を送信
- **Secret Manager統合**: 認証情報をSecret Managerで安全に管理
- **リトライ機能**: API呼び出しやBigQuery挿入時の自動リトライ
- **データ集計**: URLごとにクリック数、インプレッション数、平均順位を集計

### 対象ユーザー

- SEOデータを分析するデータアナリスト
- ビジネスインテリジェンスツールでGSCデータを活用したいマーケティング担当者
- 定期的なデータ収集を自動化したい開発者

## 主要機能

### 1. GSCデータ取得

- `GSCConnector`クラスを使用してGSC APIからデータを取得
- 指定された日付範囲のデータをバッチ処理で取得
- 1日あたりのAPI呼び出し制限（デフォルト: 200回）を管理

### 2. データ集計と正規化

- `url_utils`モジュールでURLごとにデータを集計
- クエリパラメータとフラグメントを除去してURLを正規化
- クリック数、インプレッション数、平均順位を計算

### 3. BigQueryへの保存

- 集計されたデータをBigQueryに挿入
- リトライロジックで確実なデータ保存
- 進捗テーブルで処理状況を管理

### 4. 進捗管理

- 各日付の処理状況をBigQueryに保存
- 中断後も前回の位置から再開可能
- 完了済み日付のスキップ機能

### 5. 通知機能

- **成功通知**: 処理完了時に日付ごとの取得件数やスキップ情報を通知
- **エラー通知**: エラー発生時に詳細なエラー情報を通知
- Google Chat Webhookを使用

### 6. 環境管理

- Secret Managerから認証情報を取得（Cloud Run環境）
- ローカル環境では`secrets.env`ファイルを使用
- `settings.ini`で設定を管理

## アーキテクチャ

```
┌─────────────────┐
│  Cloud Scheduler │  (定期実行トリガー)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Cloud Run Jobs │  (実行環境)
└────────┬────────┘
         │
         ├──► Secret Manager (認証情報)
         │
         ├──► Google Search Console API (データ取得)
         │
         ├──► BigQuery (データ保存・進捗管理)
         │
         └──► Google Chat (通知)
```

### 主要コンポーネント

- **`src/main.py`**: エントリーポイント、エラーハンドリング
- **`src/modules/gsc_handler.py`**: メイン処理ロジック、進捗管理
- **`src/modules/gsc_fetcher.py`**: GSC APIとの通信
- **`src/utils/environment.py`**: 環境設定と認証情報管理
- **`src/utils/webhook_notifier.py`**: Google Chat通知機能

## セットアップ

### 前提条件

- Python 3.11以上
- Google Cloud SDK (gcloud)
- Docker (ローカル開発用)
- GCPプロジェクトと必要なAPIの有効化

### ローカル環境のセットアップ

1. **リポジトリのクローン**

```bash
git clone <repository-url>
cd BQ_gsc
```

2. **仮想環境の作成と有効化**

```bash
.\run_dev.bat
```

または手動で：

```bash
python -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
```

3. **設定ファイルの準備**

`config/secrets.env`を作成：

```env
GOOGLE_APPLICATION_CREDENTIALS=bigquery-jukust-e4234348209d.json
Webhook_URL=https://chat.googleapis.com/v1/spaces/...
```

4. **認証情報ファイルの配置**

`config/`ディレクトリにサービスアカウントのJSONファイルを配置

## 実行方法

### ローカル実行

```bash
.\run_dev.bat
```

または：

```bash
python src/main.py
```

### Cloud Run Jobsでの実行

手動実行：

```bash
gcloud run jobs execute bq-gsc-scraper-job \
    --region=asia-northeast1 \
    --project=bigquery-jukust
```

ログ確認：

```bash
gcloud logging read \
    "resource.type=cloud_run_job AND resource.labels.job_name=bq-gsc-scraper-job" \
    --limit=50 \
    --project=bigquery-jukust \
    --format="table(timestamp,severity,textPayload)"
```

## 設定

### settings.ini

主要な設定項目：

```ini
[GSC]
site_url = https://www.juku.st/
batch_size = 25000
daily_api_limit = 200

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

### 環境変数（Secret Manager）

Cloud Run環境では、Secret Managerから以下のシークレットを取得：

- `secrets-env`: 環境変数（`Webhook_URL`など）
- `bigquery-credentials-json`: BigQuery認証情報

## デプロイ

### Cloud Run Jobsへのデプロイ

詳細は [Cloud Run セットアップガイド](./docs/cloudrun_setup.md) を参照してください。

#### クイックデプロイ

1. **Dockerイメージのビルドとプッシュ**

```bash
gcloud builds submit \
    --tag asia-northeast1-docker.pkg.dev/bigquery-jukust/gsc-repo/bq-gsc-scraper:latest \
    --project=bigquery-jukust
```

2. **Cloud Run Jobの更新**

```bash
gcloud run jobs update bq-gsc-scraper-job \
    --image=asia-northeast1-docker.pkg.dev/bigquery-jukust/gsc-repo/bq-gsc-scraper:latest \
    --region=asia-northeast1 \
    --project=bigquery-jukust
```

### GitHub Actionsによる自動デプロイ

`main`または`master`ブランチにpushすると、自動的に以下が実行されます：

1. Dockerイメージのビルド
2. Artifact Registryへのプッシュ
3. Cloud Run Jobsの更新

詳細は [Git デプロイガイド](./docs/git_deployment.md) を参照してください。

## トラブルシューティング

### よくある問題

#### 1. 認証エラー

**症状**: `403 Permission denied` エラー

**解決方法**:
- サービスアカウントに必要な権限が付与されているか確認
- Secret Managerのシークレットにアクセス権限があるか確認

```bash
gcloud projects get-iam-policy bigquery-jukust \
    --flatten="bindings[].members" \
    --filter="bindings.members:jukust-gcs@bigquery-jukust.iam.gserviceaccount.com"
```

#### 2. タイムアウトエラー

**症状**: ジョブが途中で終了する

**解決方法**: `--task-timeout`を増やす

```bash
gcloud run jobs update bq-gsc-scraper-job \
    --task-timeout=6h \
    --region=asia-northeast1 \
    --project=bigquery-jukust
```

#### 3. メモリ不足

**症状**: メモリエラーが発生

**解決方法**: `--memory`を増やす

```bash
gcloud run jobs update bq-gsc-scraper-job \
    --memory=4Gi \
    --region=asia-northeast1 \
    --project=bigquery-jukust
```

#### 4. 通知が届かない

**症状**: Google Chatに通知が届かない

**解決方法**:
- `Webhook_URL`がSecret Managerに正しく設定されているか確認
- Webhook URLが有効か確認

#### 5. GitHub ActionsでCloud Buildが失敗する

**症状**: GitHub ActionsからCloud Buildを実行する際にエラーが発生する

**解決方法**:
- [GitHub Actions と Cloud Build のトラブルシューティングガイド](./docs/github_actions_troubleshooting.md)を参照
- よくあるエラー:
  - 認証エラー: `GCP_SA_KEY`シークレットが設定されているか確認
  - 権限エラー: サービスアカウントに必要な権限が付与されているか確認
  - Substitution変数エラー: `cloudbuild.yaml`の変数設定を確認

## ドキュメント

- [Cloud Run セットアップガイド](./docs/cloudrun_setup.md) - Cloud Run Jobs環境の構築手順
- [Cloud Scheduler 設定ガイド](./docs/cloudrun_scheduler_guide.md) - 定期実行の設定
- [Git デプロイガイド](./docs/git_deployment.md) - GitHub Actionsによる自動デプロイ
- [GitHub Actions トラブルシューティング](./docs/github_actions_troubleshooting.md) - GitHub ActionsとCloud Buildのエラー解決ガイド
- [システム仕様書](./docs/system_specification.md) - システム全体の詳細仕様
- [アーキテクチャドキュメント](./docs/architecture.md) - アーキテクチャとコンポーネント設計

## 技術スタック

- **言語**: Python 3.11
- **クラウドプラットフォーム**: Google Cloud Platform
- **実行環境**: Cloud Run Jobs
- **データベース**: BigQuery
- **認証**: Google Service Account
- **通知**: Google Chat Webhook
- **CI/CD**: GitHub Actions, Cloud Build

## ライセンス

[ライセンス情報を記載]

## 更新履歴

- **2026-01-06**: 本番運用に向けた準備完了
  - テストコードの削除
  - 通知機能の改善
  - ドキュメントの整備
