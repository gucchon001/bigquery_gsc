# GCE環境セットアップ完了

## 完了した設定

### ✅ API有効化
- Secret Manager API
- Artifact Registry API
- Compute Engine API
- Cloud Scheduler API

### ✅ Secret Manager
- `settings-ini` シークレット作成済み
- `secrets-env` シークレット作成済み
- サービスアカウント `jukust-gcs@bigquery-jukust.iam.gserviceaccount.com` に読み取り権限付与済み

### ✅ Artifact Registry
- リポジトリ `gsc-repo` 作成済み（asia-northeast1）
- サービスアカウントに読み取り権限付与済み

### ✅ サービスアカウント権限
- `roles/compute.instanceAdmin.v1` - VM管理
- `roles/logging.logWriter` - ログ書き込み
- `roles/artifactregistry.reader` - Artifact Registry読み取り
- `roles/secretmanager.secretAccessor` - Secret Manager読み取り

## 次のステップ：デプロイ実行

### 1. サービスアカウントで認証

```bash
gcloud auth activate-service-account --key-file=config/bigquery-jukust-e4234348209d.json
gcloud config set project bigquery-jukust
```

### 2. 環境変数を設定（Windows PowerShell）

```powershell
$env:GOOGLE_CLOUD_PROJECT = "bigquery-jukust"
$env:GCE_REGION = "asia-northeast1"
$env:GCE_ZONE = "asia-northeast1-a"
```

### 3. デプロイスクリプトを実行

```bash
# Windowsの場合、WSLまたはGit Bashを使用
bash gce/deploy.sh
```

または手動で：

```bash
# Docker認証設定
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# イメージのビルドとプッシュ
export IMAGE_URL="asia-northeast1-docker.pkg.dev/bigquery-jukust/gsc-repo/bq-gsc-scraper:latest"
docker build -t $IMAGE_URL .
docker push $IMAGE_URL

# VMインスタンスの作成
gcloud compute instances create gsc-scheduler-vm \
    --zone=asia-northeast1-a \
    --machine-type=e2-micro \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --image-family=cos-stable \
    --image-project=cos-cloud \
    --boot-disk-size=10GB \
    --metadata-from-file startup-script=gce/startup-script.sh \
    --project=bigquery-jukust \
    --preemptible
```

## Cloud Scheduler設定（オプション）

定期実行を設定する場合：

```bash
# Cloud Scheduler用サービスアカウント作成
gcloud iam service-accounts create cloud-scheduler-sa \
    --display-name="Cloud Scheduler Service Account" \
    --project=bigquery-jukust

# 権限付与
gcloud projects add-iam-policy-binding bigquery-jukust \
    --member="serviceAccount:cloud-scheduler-sa@bigquery-jukust.iam.gserviceaccount.com" \
    --role="roles/compute.instanceAdmin.v1"

# スケジュールジョブ作成（毎日午前2時JST）
gcloud scheduler jobs create http start-gsc-vm \
    --schedule="0 2 * * *" \
    --uri="https://compute.googleapis.com/compute/v1/projects/bigquery-jukust/zones/asia-northeast1-a/instances/gsc-scheduler-vm/start" \
    --http-method=POST \
    --oauth-service-account-email="cloud-scheduler-sa@bigquery-jukust.iam.gserviceaccount.com" \
    --time-zone="Asia/Tokyo" \
    --project=bigquery-jukust
```

## 確認コマンド

```bash
# Secret Manager確認
gcloud secrets list --project=bigquery-jukust

# Artifact Registry確認
gcloud artifacts repositories list --project=bigquery-jukust --location=asia-northeast1

# VM確認
gcloud compute instances list --project=bigquery-jukust --zones=asia-northeast1-a

# ログ確認
gcloud logging read "resource.type=gce_instance" --limit=50 --project=bigquery-jukust
```

