# Cloud Buildトリガーのセットアップガイド

このドキュメントでは、GitHub Actionsではなく、Cloud Buildトリガーを直接使用して自動デプロイを設定する方法を説明します。

## 概要

Cloud Buildトリガーを使用することで、GitHub Actionsを介さずに、GitHubへのpushを直接Cloud Buildが検知して自動的にビルドとデプロイを実行します。

### メリット

- **シンプル**: GitHub Secretsの設定が不要
- **高速**: GitHub Actionsを介さないため、より高速
- **コスト効率**: GitHub Actionsの実行時間を消費しない
- **組み込み変数**: `SHORT_SHA`などの組み込み変数が自動的に使用可能

## 前提条件

- GitHubリポジトリが設定されていること
- Google Cloudプロジェクトへのアクセス権限があること
- Cloud Build APIが有効になっていること

## セットアップ手順

### クイックセットアップ

セットアップスクリプトを実行します：

```bash
chmod +x scripts/setup_cloudbuild_trigger.sh
./scripts/setup_cloudbuild_trigger.sh
```

このスクリプトは以下を自動的に実行します：
- Cloud Build APIの有効化
- Cloud Buildサービスアカウントへの権限付与
- Cloud Buildトリガーの作成

### 手動セットアップ

#### 1. Cloud Build APIの有効化

```bash
gcloud services enable cloudbuild.googleapis.com --project=bigquery-jukust
```

#### 2. Cloud Buildサービスアカウントの権限設定

```bash
PROJECT_ID="bigquery-jukust"
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Artifact Registryへの書き込み権限
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/artifactregistry.writer"

# Cloud Run Jobsへの権限
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/run.admin"

# Service Account User権限
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/iam.serviceAccountUser"
```

#### 3. Cloud Buildトリガーの作成

```bash
gcloud builds triggers create github \
  --name="gsc-scraper-deploy" \
  --repo-name="bigquery_gsc" \
  --repo-owner="gucchon001" \
  --branch-pattern="^master$" \
  --build-config="cloudbuild.yaml" \
  --project=bigquery-jukust \
  --substitutions=_REGION=asia-northeast1,_REPOSITORY=gsc-repo,_IMAGE_NAME=bq-gsc-scraper,_JOB_NAME=bq-gsc-scraper-job,_SERVICE_ACCOUNT=jukust-gcs@bigquery-jukust.iam.gserviceaccount.com \
  --include-logs-with-status
```

## 使用方法

### 自動デプロイ

`master`ブランチにpushすると、自動的にCloud Buildトリガーが実行されます：

```bash
git add .
git commit -m "Update application"
git push origin master
```

### デプロイの確認

Cloud Buildの実行状況は、以下のコマンドで確認できます：

```bash
gcloud builds list --project=bigquery-jukust --limit=5
```

または、GCPコンソールの「Cloud Build」>「履歴」ページから確認できます。

### トリガーの一覧確認

```bash
gcloud builds triggers list --project=bigquery-jukust
```

### トリガーの詳細確認

```bash
gcloud builds triggers describe gsc-scraper-deploy --project=bigquery-jukust
```

## デプロイフロー

1. **GitHubへのpush**
   - `master`ブランチへのpushを検知

2. **Cloud Buildトリガーの実行**
   - 自動的にCloud Buildが起動
   - `SHORT_SHA`などの組み込み変数が自動的に設定される

3. **Cloud Buildの実行**
   - Dockerイメージをビルド
   - Artifact Registryにプッシュ（`SHORT_SHA`タグと`latest`タグ）
   - Cloud Run Jobsの更新

## GitHub Actionsからの切り替え

GitHub ActionsからCloud Buildトリガーに切り替える場合：

1. **Cloud Buildトリガーをセットアップ**
   ```bash
   ./scripts/setup_cloudbuild_trigger.sh
   ```

2. **GitHub Actionsワークフローを無効化**
   - `.github/workflows/deploy.yml`は既に無効化されています
   - 必要に応じて削除することも可能です

3. **動作確認**
   - `master`ブランチにpushして、Cloud Buildトリガーが正常に動作することを確認

## トラブルシューティング

### トリガーが実行されない

1. **トリガーの状態を確認**:
   ```bash
   gcloud builds triggers describe gsc-scraper-deploy --project=bigquery-jukust
   ```

2. **ブランチパターンを確認**:
   - `--branch-pattern="^master$"`が正しく設定されているか確認

3. **GitHub接続を確認**:
   - GCPコンソールで「Cloud Build」>「トリガー」から、GitHub接続が正常か確認

### 権限エラー

Cloud Buildサービスアカウントに必要な権限が付与されているか確認：

```bash
PROJECT_NUMBER=$(gcloud projects describe bigquery-jukust --format="value(projectNumber)")
gcloud projects get-iam-policy bigquery-jukust \
  --flatten="bindings[].members" \
  --filter="bindings.members:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --format="table(bindings.role)"
```

### ビルドが失敗する場合

1. **Cloud Buildのログを確認**:
   ```bash
   gcloud builds log <BUILD_ID> --project=bigquery-jukust
   ```

2. **substitution変数を確認**:
   - `cloudbuild.yaml`で使用している変数が正しく定義されているか確認

## 注意事項

- トリガーは`master`ブランチへのpush時のみ実行されます（他のブランチパターンに変更可能）
- ビルドには数分かかる場合があります
- `SHORT_SHA`はCloud Buildトリガーが自動的に設定する組み込み変数です

## 参考リンク

- [Cloud Build トリガー ドキュメント](https://cloud.google.com/build/docs/triggers)
- [GitHub リポジトリ接続](https://cloud.google.com/build/docs/automating-builds/create-github-app-triggers)
- [Cloud Build の組み込み変数](https://cloud.google.com/build/docs/configuring-builds/substitute-variable-values)

