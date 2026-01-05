#!/bin/bash
# Git連携による自動デプロイのセットアップスクリプト（GitHub CLI使用版）

set -e

PROJECT_ID="bigquery-jukust"
REGION="asia-northeast1"
SERVICE_ACCOUNT_NAME="github-actions-deploy"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE="github-actions-key.json"

echo "=========================================="
echo "Git連携自動デプロイセットアップ（GitHub CLI版）"
echo "=========================================="
echo "Project ID: ${PROJECT_ID}"
echo "=========================================="

# GitHub CLIのインストール確認
if ! command -v gh &> /dev/null; then
    echo "エラー: GitHub CLI (gh) がインストールされていません。"
    echo ""
    echo "インストール方法:"
    echo "  Windows: winget install GitHub.cli"
    echo "  macOS: brew install gh"
    echo "  Linux: https://cli.github.com/manual/installation"
    exit 1
fi

# GitHub CLIの認証確認
if ! gh auth status &>/dev/null; then
    echo "GitHub CLIの認証が必要です。"
    echo "以下のコマンドで認証してください:"
    echo "  gh auth login"
    exit 1
fi

# リポジトリの確認
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [ -z "$REPO" ]; then
    echo "現在のディレクトリがGitHubリポジトリではありません。"
    echo "リポジトリのルートディレクトリで実行してください。"
    exit 1
fi

echo "リポジトリ: ${REPO}"
echo ""

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
if [ -f "${KEY_FILE}" ]; then
    echo "警告: ${KEY_FILE} は既に存在します。上書きしますか？ (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "キーの作成をスキップしました。"
        SKIP_KEY_CREATE=true
    else
        rm -f "${KEY_FILE}"
    fi
fi

if [ -z "$SKIP_KEY_CREATE" ]; then
    gcloud iam service-accounts keys create ${KEY_FILE} \
      --iam-account=${SERVICE_ACCOUNT_EMAIL} \
      --project=${PROJECT_ID}
fi

# 6. GitHub Secretsの設定
echo "6. GitHub Secretsを設定しています..."
if [ -f "${KEY_FILE}" ]; then
    echo "GCP_SA_KEYシークレットを設定中..."
    gh secret set GCP_SA_KEY < "${KEY_FILE}"
    echo "✅ GitHub Secretsの設定が完了しました。"
    
    # キーファイルを削除（オプション）
    echo ""
    echo "キーファイル ${KEY_FILE} を削除しますか？ (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -f "${KEY_FILE}"
        echo "キーファイルを削除しました。"
    else
        echo "キーファイルは保持されました。Gitにコミットしないでください。"
    fi
else
    echo "警告: ${KEY_FILE} が見つかりません。GitHub Secretsの設定をスキップします。"
    echo "手動で設定する場合:"
    echo "  gh secret set GCP_SA_KEY < ${KEY_FILE}"
fi

echo ""
echo "=========================================="
echo "セットアップ完了"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "1. mainブランチにpushしてデプロイをテスト"
echo "   git push origin main"
echo ""
echo "2. GitHub Actionsの実行状況を確認"
echo "   gh run list"
echo "   gh run watch"

