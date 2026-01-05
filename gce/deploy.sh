#!/bin/bash
# GCE環境へのデプロイスクリプト
# Artifact RegistryへのイメージプッシュとGCE VMインスタンスの作成/更新を行います

set -e

# 設定変数（環境に応じて変更してください）
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-bigquery-jukust}"
REGION="${GCE_REGION:-asia-northeast1}"
ZONE="${GCE_ZONE:-asia-northeast1-a}"
REPOSITORY="${ARTIFACT_REPO:-gsc-repo}"
IMAGE_NAME="bq-gsc-scraper"
IMAGE_TAG="latest"
INSTANCE_NAME="${GCE_INSTANCE_NAME:-gsc-scheduler-vm}"
MACHINE_TYPE="${GCE_MACHINE_TYPE:-e2-micro}"
SERVICE_ACCOUNT="${GCE_SERVICE_ACCOUNT:-jukust-gcs@bigquery-jukust.iam.gserviceaccount.com}"
IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "=========================================="
echo "GCE Deployment Script"
echo "=========================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Zone: $ZONE"
echo "Repository: $REPOSITORY"
echo "Image: $IMAGE_NAME:$IMAGE_TAG"
echo "Instance: $INSTANCE_NAME"
echo "=========================================="

# プロジェクトIDの確認
if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: GOOGLE_CLOUD_PROJECT is not set"
    exit 1
fi

# gcloud CLIの認証確認
echo "Checking gcloud authentication..."
gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 || {
    echo "ERROR: No active gcloud authentication found"
    exit 1
}

# Artifact Registryリポジトリの作成（存在しない場合）
echo "Setting up Artifact Registry repository..."
if ! gcloud artifacts repositories describe "$REPOSITORY" --location="$REGION" --project="$PROJECT_ID" &>/dev/null; then
    echo "Creating Artifact Registry repository..."
    gcloud artifacts repositories create "$REPOSITORY" \
        --repository-format=docker \
        --location="$REGION" \
        --description="GSC Data Scraper Repository" \
        --project="$PROJECT_ID"
else
    echo "Repository already exists"
fi

# Artifact Registry認証
echo "Configuring Docker authentication..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# Dockerイメージのビルド
echo "Building Docker image..."
docker build -t "$IMAGE_URL" .

# イメージのプッシュ
echo "Pushing Docker image to Artifact Registry..."
docker push "$IMAGE_URL"

echo "Docker image pushed successfully: $IMAGE_URL"

# 起動スクリプトのパス
STARTUP_SCRIPT_PATH="$(pwd)/gce/startup-script.sh"

if [ ! -f "$STARTUP_SCRIPT_PATH" ]; then
    echo "ERROR: Startup script not found: $STARTUP_SCRIPT_PATH"
    exit 1
fi

# GCE VMインスタンスの作成または更新
echo "Setting up GCE VM instance..."

# インスタンスが存在するか確認
if gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --project="$PROJECT_ID" &>/dev/null; then
    echo "Instance already exists. Updating startup script..."
    
    # 起動スクリプトを更新
    gcloud compute instances add-metadata "$INSTANCE_NAME" \
        --zone="$ZONE" \
        --metadata-from-file startup-script="$STARTUP_SCRIPT_PATH" \
        --project="$PROJECT_ID"
    
    echo "Startup script updated. Restart the instance to apply changes."
else
    echo "Creating new VM instance..."
    
    # 新しいインスタンスを作成
    gcloud compute instances create "$INSTANCE_NAME" \
        --zone="$ZONE" \
        --machine-type="$MACHINE_TYPE" \
        --network-tier=PREMIUM \
        --maintenance-policy=MIGRATE \
        --scopes=https://www.googleapis.com/auth/cloud-platform \
        --tags=http-server,https-server \
        --image-family=cos-stable \
        --image-project=cos-cloud \
        --boot-disk-size=10GB \
        --boot-disk-type=pd-standard \
        --metadata-from-file startup-script="$STARTUP_SCRIPT_PATH" \
        --project="$PROJECT_ID" \
        --preemptible
    
    echo "VM instance created: $INSTANCE_NAME"
fi

# Cloud Schedulerジョブの設定（オプション）
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo "1. Set up Cloud Scheduler to start the VM:"
echo "   gcloud scheduler jobs create http start-gsc-vm \\"
echo "     --schedule='0 2 * * *' \\"
echo "     --uri='https://compute.googleapis.com/compute/v1/projects/${PROJECT_ID}/zones/${ZONE}/instances/${INSTANCE_NAME}/start' \\"
echo "     --http-method=POST \\"
echo "     --oauth-service-account-email=\$(gcloud iam service-accounts list --filter='displayName:Cloud Scheduler Service Account' --format='value(email)') \\"
echo "     --time-zone='Asia/Tokyo'"
echo ""
echo "2. Or manually start the VM:"
echo "   gcloud compute instances start $INSTANCE_NAME --zone=$ZONE"
echo ""
echo "3. View logs:"
echo "   gcloud logging read 'resource.type=\"gce_instance\" AND resource.labels.instance_id=\"$INSTANCE_NAME\"' --limit=50"
echo "=========================================="

