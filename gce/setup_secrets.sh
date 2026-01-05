#!/bin/bash
# Secret Managerへのシークレット登録スクリプト

set -e

PROJECT_ID="bigquery-jukust"
SERVICE_ACCOUNT="jukust-gcs@bigquery-jukust.iam.gserviceaccount.com"
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Secret Managerへのシークレット登録を開始します..."

# settings.ini の登録
if gcloud secrets describe settings-ini --project=$PROJECT_ID &>/dev/null; then
    echo "settings-ini は既に存在します。更新します..."
    gcloud secrets versions add settings-ini \
        --project=$PROJECT_ID \
        --data-file="$BASE_DIR/config/settings.ini"
else
    echo "settings-ini を作成します..."
    gcloud secrets create settings-ini \
        --project=$PROJECT_ID \
        --data-file="$BASE_DIR/config/settings.ini" \
        --replication-policy="automatic"
fi

# secrets.env の登録
if gcloud secrets describe secrets-env --project=$PROJECT_ID &>/dev/null; then
    echo "secrets-env は既に存在します。更新します..."
    gcloud secrets versions add secrets-env \
        --project=$PROJECT_ID \
        --data-file="$BASE_DIR/config/secrets.env"
else
    echo "secrets-env を作成します..."
    gcloud secrets create secrets-env \
        --project=$PROJECT_ID \
        --data-file="$BASE_DIR/config/secrets.env" \
        --replication-policy="automatic"
fi

# サービスアカウントへの権限付与
echo "サービスアカウントに権限を付与します..."

gcloud secrets add-iam-policy-binding settings-ini \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

gcloud secrets add-iam-policy-binding secrets-env \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

echo ""
echo "Secret Managerの設定が完了しました。"

