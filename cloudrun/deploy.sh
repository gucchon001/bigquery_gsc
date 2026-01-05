#!/bin/bash
# Cloud Run Jobs環境へのデプロイスクリプト
# Artifact RegistryへのイメージプッシュとCloud Run Jobsの作成/更新を行います

set -e

# 設定変数（環境に応じて変更してください）
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-bigquery-jukust}"
REGION="${REGION:-asia-northeast1}"
REPOSITORY="${ARTIFACT_REPO:-gsc-repo}"
IMAGE_NAME="bq-gsc-scraper"
IMAGE_TAG="latest"
JOB_NAME="bq-gsc-scraper-job"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-jukust-gcs@bigquery-jukust.iam.gserviceaccount.com}"
IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "=========================================="
echo "Cloud Run Jobs Deployment Script"
echo "=========================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Repository: $REPOSITORY"
echo "Image: $IMAGE_NAME:$IMAGE_TAG"
echo "Job: $JOB_NAME"
echo "Service Account: $SERVICE_ACCOUNT"
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

# Cloud Run Jobsの作成または更新
echo "Setting up Cloud Run Jobs..."

# ジョブが存在するか確認
if gcloud run jobs describe "$JOB_NAME" --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
    echo "Job already exists. Updating..."
    gcloud run jobs update "$JOB_NAME" \
        --image="$IMAGE_URL" \
        --region="$REGION" \
        --memory=2Gi \
        --cpu=1 \
        --task-timeout=3h \
        --max-retries=0 \
        --service-account="$SERVICE_ACCOUNT" \
        --project="$PROJECT_ID"
    echo "Job updated successfully"
else
    echo "Creating new Cloud Run Job..."
    gcloud run jobs create "$JOB_NAME" \
        --image="$IMAGE_URL" \
        --region="$REGION" \
        --memory=2Gi \
        --cpu=1 \
        --task-timeout=3h \
        --max-retries=0 \
        --service-account="$SERVICE_ACCOUNT" \
        --project="$PROJECT_ID"
    echo "Job created successfully"
fi

echo ""
echo "=========================================="
echo "Deployment completed!"
echo "=========================================="
echo "Job name: $JOB_NAME"
echo "Region: $REGION"
echo "Image: $IMAGE_URL"
echo ""
echo "To execute the job manually:"
echo "  gcloud run jobs execute $JOB_NAME --region=$REGION"
echo ""
echo "To view logs:"
echo "  gcloud logging read 'resource.type=\"cloud_run_job\" AND resource.labels.job_name=\"$JOB_NAME\"' --limit=50"
echo "=========================================="

