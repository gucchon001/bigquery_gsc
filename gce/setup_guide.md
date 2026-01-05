# GCE環境セットアップガイド（bigquery-jukust プロジェクト）

このガイドでは、`bigquery-jukust` プロジェクトでGCE環境をセットアップする手順を説明します。

## 前提条件

- プロジェクトオーナーまたは適切な権限を持つアカウントで実行
- サービスアカウント: `jukust-gcs@bigquery-jukust.iam.gserviceaccount.com`
- プロジェクトID: `bigquery-jukust`

## セットアップ手順

### ステップ1: 必要なAPIの有効化

プロジェクトオーナー権限で以下のコマンドを実行してください：

```bash
# API有効化スクリプトを実行
chmod +x gce/setup_apis.sh
./gce/setup_apis.sh
```

または手動で実行：

```bash
gcloud services enable secretmanager.googleapis.com --project=bigquery-jukust
gcloud services enable artifactregistry.googleapis.com --project=bigquery-jukust
gcloud services enable compute.googleapis.com --project=bigquery-jukust
gcloud services enable cloudscheduler.googleapis.com --project=bigquery-jukust
```

### ステップ2: Secret Managerへのシークレット登録

```bash
# Secret Manager設定スクリプトを実行
chmod +x gce/setup_secrets.sh
./gce/setup_secrets.sh
```

このスクリプトは以下を実行します：
- `settings.ini` を Secret Manager に登録
- `secrets.env` を Secret Manager に登録
- サービスアカウントに Secret Manager 読み取り権限を付与

### ステップ3: Artifact Registryリポジトリの作成

```bash
gcloud artifacts repositories create gsc-repo \
    --repository-format=docker \
    --location=asia-northeast1 \
    --description="GSC Data Scraper Repository" \
    --project=bigquery-jukust
```

### ステップ4: サービスアカウントへの権限付与

```bash
SERVICE_ACCOUNT="jukust-gcs@bigquery-jukust.iam.gserviceaccount.com"

# Artifact Registry読み取り権限
gcloud artifacts repositories add-iam-policy-binding gsc-repo \
    --location=asia-northeast1 \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/artifactregistry.reader" \
    --project=bigquery-jukust

# Compute Engine サービスアカウント権限（VM作成時に使用）
gcloud projects add-iam-policy-binding bigquery-jukust \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/compute.instanceAdmin.v1"

# Cloud Logging書き込み権限
gcloud projects add-iam-policy-binding bigquery-jukust \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/logging.logWriter"
```

### ステップ5: デプロイの実行

サービスアカウントで認証してからデプロイを実行：

```bash
# サービスアカウントで認証
gcloud auth activate-service-account --key-file=config/bigquery-jukust-e4234348209d.json

# プロジェクトを設定
gcloud config set project bigquery-jukust

# 環境変数を設定
export GOOGLE_CLOUD_PROJECT=bigquery-jukust
export GCE_REGION=asia-northeast1
export GCE_ZONE=asia-northeast1-a

# デプロイスクリプトを実行
chmod +x gce/deploy.sh
./gce/deploy.sh
```

### ステップ6: Cloud Schedulerの設定（オプション）

定期実行を設定する場合：

```bash
# Cloud Scheduler用のサービスアカウントを作成（推奨）
gcloud iam service-accounts create cloud-scheduler-sa \
    --display-name="Cloud Scheduler Service Account" \
    --project=bigquery-jukust

# Compute Engine起動権限を付与
gcloud projects add-iam-policy-binding bigquery-jukust \
    --member="serviceAccount:cloud-scheduler-sa@bigquery-jukust.iam.gserviceaccount.com" \
    --role="roles/compute.instanceAdmin.v1"

# スケジュールジョブを作成（毎日午前2時JST）
gcloud scheduler jobs create http start-gsc-vm \
    --schedule="0 2 * * *" \
    --uri="https://compute.googleapis.com/compute/v1/projects/bigquery-jukust/zones/asia-northeast1-a/instances/gsc-scheduler-vm/start" \
    --http-method=POST \
    --oauth-service-account-email="cloud-scheduler-sa@bigquery-jukust.iam.gserviceaccount.com" \
    --time-zone="Asia/Tokyo" \
    --project=bigquery-jukust
```

## トラブルシューティング

### 権限エラーが発生する場合

サービスアカウント `jukust-gcs@bigquery-jukust.iam.gserviceaccount.com` に以下の権限が必要です：

- `roles/secretmanager.secretAccessor` - Secret Manager読み取り
- `roles/artifactregistry.reader` - Artifact Registry読み取り
- `roles/compute.instanceAdmin.v1` - VM管理
- `roles/logging.logWriter` - ログ書き込み

### APIが有効化されていない場合

プロジェクトオーナー権限でAPIを有効化してください：

```bash
gcloud services enable secretmanager.googleapis.com --project=bigquery-jukust
gcloud services enable artifactregistry.googleapis.com --project=bigquery-jukust
gcloud services enable compute.googleapis.com --project=bigquery-jukust
gcloud services enable cloudscheduler.googleapis.com --project=bigquery-jukust
```

## 次のステップ

セットアップが完了したら、`docs/gce_setup.md` を参照して運用を開始してください。

