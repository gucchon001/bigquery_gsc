# Cloud Run Jobs 環境構築ガイド

このドキュメントでは、GSCデータ取得アプリケーションをCloud Run Jobsで定期実行するための設定手順を説明します。

## 概要

Cloud Run Jobsを使用することで、以下のメリットがあります：

- **サーバーレス**: VMの管理が不要
- **自動スケーリング**: 実行時のみリソースが使用される
- **長時間実行対応**: 最大24時間まで実行可能（task-timeout設定）
- **コスト効率**: 実行時のみ課金される

## 前提条件

- Google Cloud SDK (gcloud コマンド) がインストールされていること
- Docker がローカルで動作していること（イメージビルド用）
- 必要なGCP APIが有効になっていること

## 1. 必要なAPIの有効化

```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    cloudscheduler.googleapis.com \
    --project=bigquery-jukust
```

## 2. Artifact Registryリポジトリの作成

Dockerイメージを保存する場所を作成します。

```bash
export PROJECT_ID="bigquery-jukust"
export REGION="asia-northeast1"
export REPO_NAME="gsc-repo"

gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="GSC Data Scraper Repository" \
    --project=$PROJECT_ID
```

## 3. サービスアカウントの権限設定

Cloud Run Jobsで使用するサービスアカウントに必要な権限を付与します。

```bash
SERVICE_ACCOUNT="jukust-gcs@bigquery-jukust.iam.gserviceaccount.com"

# BigQueryへの書き込み権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/bigquery.dataEditor"

# Secret Managerへの読み取り権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"

# Cloud Loggingへの書き込み権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/logging.logWriter"
```

## 4. Dockerイメージのビルドとプッシュ

### 方法1: デプロイスクリプトを使用（推奨）

```bash
chmod +x cloudrun/deploy.sh
./cloudrun/deploy.sh
```

### 方法2: 手動でビルドとプッシュ

```bash
export PROJECT_ID="bigquery-jukust"
export REGION="asia-northeast1"
export REPO_NAME="gsc-repo"
export IMAGE_NAME="bq-gsc-scraper"
IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"

# Artifact Registry認証
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# イメージのビルド
docker build -t "$IMAGE_URL" .

# イメージのプッシュ
docker push "$IMAGE_URL"
```

## 5. Cloud Run Jobsの作成

```bash
export PROJECT_ID="bigquery-jukust"
export REGION="asia-northeast1"
export JOB_NAME="bq-gsc-scraper-job"
export IMAGE_URL="asia-northeast1-docker.pkg.dev/${PROJECT_ID}/gsc-repo/bq-gsc-scraper:latest"
export SERVICE_ACCOUNT="jukust-gcs@bigquery-jukust.iam.gserviceaccount.com"

gcloud run jobs create $JOB_NAME \
    --image=$IMAGE_URL \
    --region=$REGION \
    --memory=2Gi \
    --cpu=1 \
    --task-timeout=3h \
    --max-retries=0 \
    --service-account=$SERVICE_ACCOUNT \
    --project=$PROJECT_ID
```

### 設定のポイント

- `--task-timeout 3h`: デフォルト（10分）だと処理が途中で止まってしまいます。余裕を持って3時間に設定しています。
- `--memory 2Gi`: メモリ使用量に応じて調整可能です。必要に応じて4Giに増やすこともできます。
- `--max-retries 0`: エラー時に自動再試行させない設定です（データの重複実行を防ぐため）。

## 6. Cloud Run Jobsの更新

イメージを更新した後、ジョブを更新します。

```bash
gcloud run jobs update $JOB_NAME \
    --image=$IMAGE_URL \
    --region=$REGION \
    --memory=2Gi \
    --cpu=1 \
    --task-timeout=3h \
    --max-retries=0 \
    --service-account=$SERVICE_ACCOUNT \
    --project=$PROJECT_ID
```

## 7. Cloud Schedulerの設定

定期実行のためのスケジューラーを設定します。

```bash
export PROJECT_ID="bigquery-jukust"
export REGION="asia-northeast1"
export JOB_NAME="bq-gsc-scraper-job"
export SCHEDULER_SA="jukust-gcs@bigquery-jukust.iam.gserviceaccount.com"

# Cloud Run Jobsの実行権限を付与
gcloud run jobs add-iam-policy-binding $JOB_NAME \
    --region=$REGION \
    --member="serviceAccount:${SCHEDULER_SA}" \
    --role="roles/run.invoker" \
    --project=$PROJECT_ID

# スケジューラーの作成（毎日 午前8時45分 JSTに実行）
gcloud scheduler jobs create http gsc-daily-schedule \
    --location=$REGION \
    --schedule="45 8 * * *" \
    --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
    --http-method=POST \
    --oauth-service-account-email=$SCHEDULER_SA \
    --time-zone="Asia/Tokyo" \
    --project=$PROJECT_ID
```

## 8. 手動実行テスト

定期実行を待たずに、今すぐテスト実行したい場合：

```bash
gcloud run jobs execute $JOB_NAME --region=$REGION --project=$PROJECT_ID
```

実行状況の確認：

```bash
# 実行履歴の確認
gcloud run jobs executions list --job=$JOB_NAME --region=$REGION --project=$PROJECT_ID

# ログの確認
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME" \
    --limit=50 \
    --project=$PROJECT_ID \
    --format="table(timestamp,severity,textPayload)"
```

## 9. GitHub Actionsによる自動デプロイ

`main`または`master`ブランチにpushすると、自動的に以下が実行されます：

1. Dockerイメージのビルド
2. Artifact Registryへのプッシュ
3. Cloud Run Jobsの更新

詳細は `docs/git_deployment.md` を参照してください。

## トラブルシューティング

### ジョブがタイムアウトする

`--task-timeout` の値を増やしてください（最大24時間）。

```bash
gcloud run jobs update $JOB_NAME \
    --task-timeout=6h \
    --region=$REGION \
    --project=$PROJECT_ID
```

### メモリ不足エラー

`--memory` の値を増やしてください。

```bash
gcloud run jobs update $JOB_NAME \
    --memory=4Gi \
    --region=$REGION \
    --project=$PROJECT_ID
```

### 認証エラー

サービスアカウントに必要な権限が付与されているか確認してください。

```bash
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:jukust-gcs@bigquery-jukust.iam.gserviceaccount.com"
```

## コスト最適化

- Cloud Run Jobsは実行時のみ課金されます
- 実行時間が短いほどコストが削減されます
- メモリとCPUの設定を必要最小限にすることでコストを最適化できます

## 参考リンク

- [Cloud Run Jobs ドキュメント](https://cloud.google.com/run/docs/create-jobs)
- [Cloud Scheduler ドキュメント](https://cloud.google.com/scheduler/docs)
- [Artifact Registry ドキュメント](https://cloud.google.com/artifact-registry/docs)

