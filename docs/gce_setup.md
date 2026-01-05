# GCE定期実行環境構築ガイド

Google Compute Engine (GCE) 上で Google Search Console データ取得アプリケーションを定期実行するための手順書です。

## 目次

1. [前提条件](#前提条件)
2. [Secret Manager の設定](#secret-manager-の設定)
3. [初回デプロイ](#初回デプロイ)
4. [Cloud Scheduler の設定](#cloud-scheduler-の設定)
5. [運用とメンテナンス](#運用とメンテナンス)
6. [トラブルシューティング](#トラブルシューティング)

## 前提条件

### 必要なツール

- Google Cloud SDK (gcloud CLI)
- Docker
- 適切な権限を持つGCPプロジェクト

### 必要な権限

- Artifact Registry の作成・管理
- GCE VM インスタンスの作成・管理
- Secret Manager の作成・読み取り
- Cloud Scheduler の作成・管理

### 環境変数の設定

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GCE_REGION="asia-northeast1"
export GCE_ZONE="asia-northeast1-a"
export ARTIFACT_REPO="gsc-repo"
export GCE_INSTANCE_NAME="gsc-scheduler-vm"
export GCE_MACHINE_TYPE="e2-micro"
```

## Secret Manager の設定

GCE環境では、設定ファイル（`settings.ini`、`secrets.env`）を Secret Manager に保存します。

### 1. Secret Manager API の有効化

```bash
gcloud services enable secretmanager.googleapis.com --project=$GOOGLE_CLOUD_PROJECT
```

### 2. settings.ini の登録

```bash
# settings.ini の内容を Secret Manager に登録
gcloud secrets create settings-ini \
    --project=$GOOGLE_CLOUD_PROJECT \
    --data-file=config/settings.ini \
    --replication-policy="automatic"
```

### 3. secrets.env の登録

```bash
# secrets.env の内容を Secret Manager に登録
gcloud secrets create secrets-env \
    --project=$GOOGLE_CLOUD_PROJECT \
    --data-file=config/secrets.env \
    --replication-policy="automatic"
```

### 4. サービスアカウントへの権限付与

GCE VM のデフォルトサービスアカウントに Secret Manager の読み取り権限を付与します。

```bash
# サービスアカウントのメールアドレスを取得
SERVICE_ACCOUNT=$(gcloud compute project-info describe --project=$GOOGLE_CLOUD_PROJECT --format="value(defaultServiceAccount)")

# Secret Manager の読み取り権限を付与
gcloud secrets add-iam-policy-binding settings-ini \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$GOOGLE_CLOUD_PROJECT

gcloud secrets add-iam-policy-binding secrets-env \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$GOOGLE_CLOUD_PROJECT
```

## 初回デプロイ

### 1. デプロイスクリプトの実行

```bash
# デプロイスクリプトに実行権限を付与（Linux/Mac）
chmod +x gce/deploy.sh

# デプロイを実行
./gce/deploy.sh
```

デプロイスクリプトは以下を自動実行します：

1. Artifact Registry リポジトリの作成
2. Docker イメージのビルド
3. Artifact Registry へのイメージプッシュ
4. GCE VM インスタンスの作成
5. 起動スクリプトの設定

### 2. 手動でのデプロイ（オプション）

デプロイスクリプトを使わない場合：

```bash
# Artifact Registry リポジトリの作成
gcloud artifacts repositories create gsc-repo \
    --repository-format=docker \
    --location=asia-northeast1 \
    --description="GSC Data Scraper Repository"

# Docker 認証の設定
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# イメージのビルドとプッシュ
export IMAGE_URL="asia-northeast1-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT}/gsc-repo/bq-gsc-scraper:latest"
docker build -t $IMAGE_URL .
docker push $IMAGE_URL

# VM インスタンスの作成
gcloud compute instances create gsc-scheduler-vm \
    --zone=asia-northeast1-a \
    --machine-type=e2-micro \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --image-family=cos-stable \
    --image-project=cos-cloud \
    --metadata-from-file startup-script=gce/startup-script.sh \
    --preemptible
```

## Cloud Scheduler の設定

定期実行のために Cloud Scheduler を設定します。

### 1. Cloud Scheduler API の有効化

```bash
gcloud services enable cloudscheduler.googleapis.com --project=$GOOGLE_CLOUD_PROJECT
```

### 2. サービスアカウントの作成（推奨）

```bash
# Cloud Scheduler 用のサービスアカウントを作成
gcloud iam service-accounts create cloud-scheduler-sa \
    --display-name="Cloud Scheduler Service Account" \
    --project=$GOOGLE_CLOUD_PROJECT

# Compute Engine の起動権限を付与
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:cloud-scheduler-sa@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com" \
    --role="roles/compute.instanceAdmin.v1"
```

### 3. スケジュールジョブの作成

```bash
# 毎日午前2時（JST）に実行
gcloud scheduler jobs create http start-gsc-vm \
    --schedule="0 2 * * *" \
    --uri="https://compute.googleapis.com/compute/v1/projects/${GOOGLE_CLOUD_PROJECT}/zones/asia-northeast1-a/instances/gsc-scheduler-vm/start" \
    --http-method=POST \
    --oauth-service-account-email="cloud-scheduler-sa@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com" \
    --time-zone="Asia/Tokyo" \
    --project=$GOOGLE_CLOUD_PROJECT
```

### 4. スケジュールの確認

```bash
# スケジュールジョブの一覧
gcloud scheduler jobs list --project=$GOOGLE_CLOUD_PROJECT

# スケジュールジョブの詳細
gcloud scheduler jobs describe start-gsc-vm --project=$GOOGLE_CLOUD_PROJECT
```

## 運用とメンテナンス

### コード更新時のデプロイ

```bash
# イメージを再ビルドしてプッシュ
./gce/deploy.sh
```

次回のスケジュール実行時に新しいイメージが使用されます。

### 手動実行

```bash
# VM を手動で起動
gcloud compute instances start gsc-scheduler-vm --zone=asia-northeast1-a
```

### ログの確認

#### Cloud Logging から確認

```bash
# VM のログを確認
gcloud logging read "resource.type=gce_instance AND resource.labels.instance_id=gsc-scheduler-vm" \
    --limit=50 \
    --format=json

# アプリケーションのログを確認
gcloud logging read "resource.type=gce_instance AND jsonPayload.logger=src.main" \
    --limit=50
```

#### GCE コンソールから確認

1. GCP コンソール > Compute Engine > VM インスタンス
2. `gsc-scheduler-vm` を選択
3. 「ログ」タブをクリック

### VM の状態確認

```bash
# VM の状態を確認
gcloud compute instances describe gsc-scheduler-vm \
    --zone=asia-northeast1-a \
    --format="value(status)"
```

## トラブルシューティング

### コンテナが起動しない

1. **起動スクリプトのログを確認**
   ```bash
   gcloud compute instances get-serial-port-output gsc-scheduler-vm \
       --zone=asia-northeast1-a
   ```

2. **イメージが正しくプッシュされているか確認**
   ```bash
   gcloud artifacts docker images list \
       asia-northeast1-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT}/gsc-repo/bq-gsc-scraper
   ```

### Secret Manager から設定が取得できない

1. **サービスアカウントの権限を確認**
   ```bash
   gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT \
       --flatten="bindings[].members" \
       --filter="bindings.members:*compute*"
   ```

2. **Secret Manager のシークレットが存在するか確認**
   ```bash
   gcloud secrets list --project=$GOOGLE_CLOUD_PROJECT
   ```

### Cloud Scheduler が VM を起動しない

1. **スケジュールジョブの実行履歴を確認**
   ```bash
   gcloud scheduler jobs describe start-gsc-vm \
       --project=$GOOGLE_CLOUD_PROJECT \
       --format="value(state, scheduleTime, lastAttemptTime)"
   ```

2. **サービスアカウントの権限を確認**
   - `roles/compute.instanceAdmin.v1` が付与されているか確認

### コスト最適化のヒント

1. **プリエンプティブル VM の使用**
   - デプロイスクリプトで `--preemptible` フラグを使用（デフォルトで有効）

2. **最小限のマシンタイプ**
   - `e2-micro` を使用（デフォルト）

3. **自動シャットダウン**
   - 起動スクリプトが処理完了後に自動的に VM をシャットダウン

4. **スケジュールの最適化**
   - 必要な頻度で実行するようスケジュールを調整

## セキュリティのベストプラクティス

1. **Secret Manager の使用**
   - 機密情報は Secret Manager に保存
   - ファイルとしてコンテナに含めない

2. **最小権限の原則**
   - サービスアカウントには必要最小限の権限のみ付与

3. **ネットワークセキュリティ**
   - 必要に応じて VPC やファイアウォールルールを設定

4. **ログの監視**
   - Cloud Logging で異常な動作を監視

## 参考リンク

- [GCE ドキュメント](https://cloud.google.com/compute/docs)
- [Artifact Registry ドキュメント](https://cloud.google.com/artifact-registry/docs)
- [Secret Manager ドキュメント](https://cloud.google.com/secret-manager/docs)
- [Cloud Scheduler ドキュメント](https://cloud.google.com/scheduler/docs)

