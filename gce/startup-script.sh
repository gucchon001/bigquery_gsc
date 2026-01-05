#!/bin/bash
# GCE起動スクリプト
# VM起動時にコンテナを実行し、処理完了後にシャットダウンします

set -e  # エラー時に終了

# ログファイルの設定
LOG_FILE="/var/log/gce-startup.log"
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "=========================================="
echo "GCE Startup Script Started"
echo "Timestamp: $(date)"
echo "=========================================="

# プロジェクトIDとリージョンの取得
PROJECT_ID=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/project/project-id)
REGION=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/zone | sed 's/.*\///' | sed 's/-[a-z]$//')
REPOSITORY="gsc-repo"
IMAGE_NAME="bq-gsc-scraper"
IMAGE_TAG="latest"

# Artifact RegistryのURL構築
IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Image URL: $IMAGE_URL"

# Dockerの確認（COSにはDockerがプリインストールされている）
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not available"
    exit 1
fi

# gcloud CLIのインストール確認（COSにはgcloudがプリインストールされている）
if ! command -v gcloud &> /dev/null; then
    echo "WARNING: gcloud CLI not found, but continuing..."
    # COSにはgcloudがプリインストールされているはず
fi

# Artifact Registry認証
# COSではサービスアカウントの認証情報が自動的に利用可能
# gcloudコマンドのパスを確認して使用
echo "Authenticating with Artifact Registry..."
GCLOUD_PATH=""
if command -v gcloud &> /dev/null; then
    GCLOUD_PATH=$(command -v gcloud)
elif [ -f /usr/bin/gcloud ]; then
    GCLOUD_PATH="/usr/bin/gcloud"
elif [ -f /usr/local/bin/gcloud ]; then
    GCLOUD_PATH="/usr/local/bin/gcloud"
fi

if [ -n "$GCLOUD_PATH" ]; then
    echo "Using gcloud at: $GCLOUD_PATH"
    $GCLOUD_PATH auth configure-docker ${REGION}-docker.pkg.dev --quiet || {
        echo "WARNING: gcloud auth configure-docker failed, but continuing..."
    }
else
    echo "WARNING: gcloud not found, trying to authenticate using service account credentials..."
    # COSではサービスアカウントの認証情報が自動的に利用可能なため、直接docker pullを試みる
    # サービスアカウントの認証情報を取得してDockerに設定
    ACCESS_TOKEN=$(curl -s -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    if [ -n "$ACCESS_TOKEN" ]; then
        echo "Obtained access token, configuring Docker..."
        echo "$ACCESS_TOKEN" | docker login -u oauth2accesstoken --password-stdin ${REGION}-docker.pkg.dev || {
            echo "WARNING: Docker login with access token failed, but continuing..."
        }
    fi
fi

# イメージのプル
echo "Pulling Docker image..."
docker pull "$IMAGE_URL" || {
    echo "ERROR: Failed to pull Docker image"
    exit 1
}

# コンテナの実行
echo "Starting container..."
EXIT_CODE=0
docker run --rm \
    --log-driver=gcplogs \
    --log-opt gcp-project="$PROJECT_ID" \
    "$IMAGE_URL" || {
    EXIT_CODE=$?
    echo "ERROR: Container execution failed with exit code $EXIT_CODE"
}

echo "=========================================="
echo "Container execution completed"
echo "Exit code: $EXIT_CODE"
echo "Timestamp: $(date)"
echo "=========================================="

# 処理完了後にVMをシャットダウン
echo "Shutting down VM..."
sleep 5  # ログが書き込まれるまで少し待つ
shutdown -h now

