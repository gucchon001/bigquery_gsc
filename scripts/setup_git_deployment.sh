#!/bin/bash
# Git連携による自動デプロイのセットアップスクリプト

set -e

PROJECT_ID="bigquery-jukust"
REGION="asia-northeast1"
SERVICE_ACCOUNT_NAME="github-actions-deploy"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=========================================="
echo "Git連携自動デプロイセットアップ"
echo "=========================================="
echo "Project ID: ${PROJECT_ID}"
echo "=========================================="

# 1. Cloud Build APIの有効化
echo "1. Cloud Build APIを有効化しています..."
gcloud services enable cloudbuild.googleapis.com --project=${PROJECT_ID}

# 2. Cloud Buildサービスアカウントの権限設定
echo "2. Cloud Buildサービスアカウントに権限を付与しています..."
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Artifact Registryへの書き込み権限
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/artifactregistry.writer" \
  --condition=None

# Compute Engineへの書き込み権限
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/compute.instanceAdmin.v1" \
  --condition=None

# 3. GitHub Actions用サービスアカウントの作成
echo "3. GitHub Actions用サービスアカウントを作成しています..."
if ! gcloud iam service-accounts describe ${SERVICE_ACCOUNT_EMAIL} --project=${PROJECT_ID} &>/dev/null; then
    gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
      --display-name="GitHub Actions Deploy" \
      --project=${PROJECT_ID}
    echo "サービスアカウントを作成しました: ${SERVICE_ACCOUNT_EMAIL}"
else
    echo "サービスアカウントは既に存在します: ${SERVICE_ACCOUNT_EMAIL}"
fi

# 4. GitHub Actions用サービスアカウントに権限を付与
echo "4. GitHub Actions用サービスアカウントに権限を付与しています..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/cloudbuild.builds.editor" \
  --condition=None

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/serviceusage.serviceUsageConsumer" \
  --condition=None

# 5. サービスアカウントキーの作成
echo "5. サービスアカウントキーを作成しています..."
KEY_FILE="github-actions-key.json"
if [ -f "${KEY_FILE}" ]; then
    echo "警告: ${KEY_FILE} は既に存在します。上書きしますか？ (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "キーの作成をスキップしました。"
        exit 0
    fi
fi

gcloud iam service-accounts keys create ${KEY_FILE} \
  --iam-account=${SERVICE_ACCOUNT_EMAIL} \
  --project=${PROJECT_ID}

echo "=========================================="
echo "セットアップ完了"
echo "=========================================="
echo ""
echo "次のステップ: GitHub Secretsの設定"
echo ""
echo "【方法1】GitHub CLIを使用（推奨）:"
echo "  gh secret set GCP_SA_KEY < ${KEY_FILE}"
echo ""
echo "【方法2】手動で設定:"
echo "  1. GitHubリポジトリのSettings > Secrets and variables > Actionsに移動"
echo "  2. 新しいシークレット 'GCP_SA_KEY' を追加"
echo "  3. ${KEY_FILE} の内容（JSON全体）をコピーして貼り付け"
echo ""
echo "設定後、mainブランチにpushしてデプロイをテストしてください。"
echo ""
echo "注意: ${KEY_FILE} は機密情報です。Gitにコミットしないでください。"

