#!/bin/bash
# API有効化スクリプト（プロジェクトオーナー権限が必要）

set -e

PROJECT_ID="bigquery-jukust"
SERVICE_ACCOUNT="jukust-gcs@bigquery-jukust.iam.gserviceaccount.com"

echo "必要なAPIを有効化しています..."

gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID
echo "✓ Secret Manager API enabled"

gcloud services enable artifactregistry.googleapis.com --project=$PROJECT_ID
echo "✓ Artifact Registry API enabled"

gcloud services enable compute.googleapis.com --project=$PROJECT_ID
echo "✓ Compute Engine API enabled"

gcloud services enable cloudscheduler.googleapis.com --project=$PROJECT_ID
echo "✓ Cloud Scheduler API enabled"

echo ""
echo "すべてのAPIが有効化されました。"

