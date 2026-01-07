#!/bin/bash
# Cloud Buildトリガーのセットアップスクリプト

set -e

PROJECT_ID="bigquery-jukust"
REGION="asia-northeast1"
REPO_OWNER="gucchon001"
REPO_NAME="bigquery_gsc"
TRIGGER_NAME="gsc-scraper-deploy"
BRANCH_PATTERN="^master$"

echo "=========================================="
echo "Cloud Buildトリガーセットアップ"
echo "=========================================="
echo "Project ID: ${PROJECT_ID}"
echo "Repository: ${REPO_OWNER}/${REPO_NAME}"
echo "Branch Pattern: ${BRANCH_PATTERN}"
echo "=========================================="

# 1. Cloud Build APIの有効化
echo "1. Cloud Build APIを有効化しています..."
gcloud services enable cloudbuild.googleapis.com --project=${PROJECT_ID}

# 2. Cloud Buildサービスアカウントの権限設定
echo "2. Cloud Buildサービスアカウントに権限を付与しています..."
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Artifact Registryへの書き込み権限
echo "  - Artifact Registryへの書き込み権限を付与..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/artifactregistry.writer" \
  --condition=None || echo "  (既に付与済み)"

# Cloud Run Jobsへの権限
echo "  - Cloud Run Jobsへの権限を付与..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/run.admin" \
  --condition=None || echo "  (既に付与済み)"

# Service Account User権限
echo "  - Service Account User権限を付与..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/iam.serviceAccountUser" \
  --condition=None || echo "  (既に付与済み)"

# 3. 既存のトリガーを確認
echo "3. 既存のトリガーを確認しています..."
EXISTING_TRIGGER=$(gcloud builds triggers list --project=${PROJECT_ID} --filter="name:${TRIGGER_NAME}" --format="value(name)" 2>/dev/null || echo "")

if [ -n "$EXISTING_TRIGGER" ]; then
    echo "既存のトリガーが見つかりました。削除して再作成します..."
    gcloud builds triggers delete ${TRIGGER_NAME} --project=${PROJECT_ID} --quiet
fi

# 4. Cloud Buildトリガーの作成
echo "4. Cloud Buildトリガーを作成しています..."
gcloud builds triggers create github \
  --name="${TRIGGER_NAME}" \
  --repo-name="${REPO_NAME}" \
  --repo-owner="${REPO_OWNER}" \
  --branch-pattern="${BRANCH_PATTERN}" \
  --build-config="cloudbuild.yaml" \
  --project=${PROJECT_ID} \
  --substitutions=_REGION=${REGION},_REPOSITORY=gsc-repo,_IMAGE_NAME=bq-gsc-scraper,_JOB_NAME=bq-gsc-scraper-job,_SERVICE_ACCOUNT=jukust-gcs@bigquery-jukust.iam.gserviceaccount.com \
  --include-logs-with-status

echo ""
echo "=========================================="
echo "セットアップ完了"
echo "=========================================="
echo ""
echo "作成されたトリガー情報:"
echo "  名前: ${TRIGGER_NAME}"
echo "  リポジトリ: ${REPO_OWNER}/${REPO_NAME}"
echo "  ブランチ: ${BRANCH_PATTERN}"
echo ""
echo "次のステップ:"
echo "1. masterブランチにpushしてデプロイをテスト"
echo "   git push origin master"
echo ""
echo "2. Cloud Buildの実行状況を確認"
echo "   gcloud builds list --project=${PROJECT_ID} --limit=5"
echo ""
echo "3. トリガーの一覧を確認"
echo "   gcloud builds triggers list --project=${PROJECT_ID}"
echo "=========================================="

