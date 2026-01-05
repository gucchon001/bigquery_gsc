# クイックセットアップガイド

`bigquery-jukust` プロジェクトでGCE環境をセットアップするための簡易ガイドです。

## 現在の設定

- **プロジェクトID**: `bigquery-jukust`
- **サービスアカウント**: `jukust-gcs@bigquery-jukust.iam.gserviceaccount.com`
- **リージョン**: `asia-northeast1`
- **ゾーン**: `asia-northeast1-a`

## 実行手順

### 1. サービスアカウントで認証（既に実行済み）

```bash
gcloud auth activate-service-account --key-file=config/bigquery-jukust-e4234348209d.json
gcloud config set project bigquery-jukust
```

### 2. API有効化（プロジェクトオーナー権限が必要）

プロジェクトオーナーアカウントで実行してください：

```bash
# Windows PowerShellの場合
.\gce\setup_apis.sh

# または手動で
gcloud services enable secretmanager.googleapis.com --project=bigquery-jukust
gcloud services enable artifactregistry.googleapis.com --project=bigquery-jukust
gcloud services enable compute.googleapis.com --project=bigquery-jukust
gcloud services enable cloudscheduler.googleapis.com --project=bigquery-jukust
```

### 3. Secret Manager設定（プロジェクトオーナー権限が必要）

```bash
.\gce\setup_secrets.sh
```

### 4. Artifact Registry作成（プロジェクトオーナー権限が必要）

```bash
gcloud artifacts repositories create gsc-repo `
    --repository-format=docker `
    --location=asia-northeast1 `
    --description="GSC Data Scraper Repository" `
    --project=bigquery-jukust
```

### 5. サービスアカウント権限付与（プロジェクトオーナー権限が必要）

```bash
$SERVICE_ACCOUNT = "jukust-gcs@bigquery-jukust.iam.gserviceaccount.com"

# Artifact Registry読み取り権限
gcloud artifacts repositories add-iam-policy-binding gsc-repo `
    --location=asia-northeast1 `
    --member="serviceAccount:$SERVICE_ACCOUNT" `
    --role="roles/artifactregistry.reader" `
    --project=bigquery-jukust

# Compute Engine権限
gcloud projects add-iam-policy-binding bigquery-jukust `
    --member="serviceAccount:$SERVICE_ACCOUNT" `
    --role="roles/compute.instanceAdmin.v1"

# Cloud Logging権限
gcloud projects add-iam-policy-binding bigquery-jukust `
    --member="serviceAccount:$SERVICE_ACCOUNT" `
    --role="roles/logging.logWriter"
```

### 6. デプロイ実行（サービスアカウントで実行可能）

```powershell
$env:GOOGLE_CLOUD_PROJECT = "bigquery-jukust"
$env:GCE_REGION = "asia-northeast1"
$env:GCE_ZONE = "asia-northeast1-a"
.\gce\deploy.sh
```

## 現在の状態確認

サービスアカウントで実行できるコマンド：

```bash
# Artifact Registry確認
gcloud artifacts repositories list --project=bigquery-jukust --location=asia-northeast1

# Secret Manager確認
gcloud secrets list --project=bigquery-jukust

# VM確認
gcloud compute instances list --project=bigquery-jukust --zones=asia-northeast1-a
```

## 注意事項

- ステップ2-5はプロジェクトオーナー権限が必要です
- ステップ6はサービスアカウントで実行可能です
- Windows環境では、PowerShellでバッククォート（`）を使用してコマンドを複数行に分けます

