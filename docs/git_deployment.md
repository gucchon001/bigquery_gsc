# Git連携による自動デプロイ設定

このドキュメントでは、GitHubへのpush時に自動的にGCP環境へデプロイする設定方法を説明します。

## 概要

GitHubにpushすると、以下の処理が自動的に実行されます：

1. Dockerイメージのビルド
2. Artifact Registryへのプッシュ
3. GCE VMの起動スクリプト更新（必要に応じて）

## 前提条件

- GitHubリポジトリが設定されていること
- Google Cloudプロジェクトへのアクセス権限があること
- Cloud Build APIが有効になっていること

## セットアップ手順

### クイックセットアップ（GitHub CLI使用）

GitHub CLIがインストールされている場合、自動セットアップスクリプトを使用できます：

```bash
chmod +x scripts/setup_git_deployment_gh.sh
./scripts/setup_git_deployment_gh.sh
```

このスクリプトは以下を自動的に実行します：
- Cloud Build APIの有効化
- サービスアカウントの作成と権限設定
- サービスアカウントキーの生成
- GitHub Secretsの設定（GitHub CLI経由）

### 手動セットアップ

### 1. Cloud Build APIの有効化

```bash
gcloud services enable cloudbuild.googleapis.com --project=bigquery-jukust
```

### 2. サービスアカウントの作成と権限設定

Cloud Build用のサービスアカウントに必要な権限を付与します：

```bash
# Cloud Buildサービスアカウントのメールアドレスを取得
PROJECT_NUMBER=$(gcloud projects describe bigquery-jukust --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Artifact Registryへの書き込み権限
gcloud projects add-iam-policy-binding bigquery-jukust \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/artifactregistry.writer"

# Compute Engineへの書き込み権限（VMメタデータ更新用）
gcloud projects add-iam-policy-binding bigquery-jukust \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/compute.instanceAdmin.v1"
```

### 3. GitHub Actions用のサービスアカウントキー作成

GitHub ActionsからCloud Buildを呼び出すためのサービスアカウントキーを作成します：

```bash
# サービスアカウントの作成（既存のものを使用する場合はスキップ）
gcloud iam service-accounts create github-actions-deploy \
  --display-name="GitHub Actions Deploy" \
  --project=bigquery-jukust

# 必要な権限を付与
gcloud projects add-iam-policy-binding bigquery-jukust \
  --member="serviceAccount:github-actions-deploy@bigquery-jukust.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"

# サービスアカウントキーの作成
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions-deploy@bigquery-jukust.iam.gserviceaccount.com \
  --project=bigquery-jukust
```

### 4. GitHub Secretsの設定

#### 方法1: GitHub CLIを使用（推奨）

GitHub CLIがインストールされていて、認証済みの場合：

```bash
# GitHub CLIでシークレットを設定
gh secret set GCP_SA_KEY < github-actions-key.json
```

または、自動セットアップスクリプト（GitHub CLI版）を使用：

```bash
chmod +x scripts/setup_git_deployment_gh.sh
./scripts/setup_git_deployment_gh.sh
```

#### 方法2: 手動で設定

GitHubリポジトリのSettings > Secrets and variables > Actionsで、以下のシークレットを追加します：

- **GCP_SA_KEY**: 上記で作成した`github-actions-key.json`の内容（JSON全体）

### 5. Cloud Buildトリガーの作成（オプション）

GitHub Actionsの代わりに、Cloud Buildトリガーを直接使用することもできます：

```bash
# GitHubリポジトリとの接続（初回のみ）
gcloud builds triggers create github \
  --name="gsc-scraper-deploy" \
  --repo-name="BQ_gsc" \
  --repo-owner="YOUR_GITHUB_USERNAME" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml" \
  --project=bigquery-jukust \
  --substitutions=_REGION=asia-northeast1,_REPOSITORY=gsc-repo,_IMAGE_NAME=bq-gsc-scraper,_VM_NAME=gsc-scheduler-vm,_ZONE=asia-northeast1-a,_STARTUP_SCRIPT_PATH=gce/startup-script.sh
```

## 使用方法

### 自動デプロイ

`main`または`master`ブランチにpushすると、自動的にデプロイが開始されます：

```bash
git add .
git commit -m "Update application"
git push origin main
```

### デプロイの確認

Cloud Buildの実行状況は、以下のコマンドで確認できます：

```bash
gcloud builds list --project=bigquery-jukust --limit=5
```

または、GCPコンソールの「Cloud Build」ページから確認できます。

## デプロイフロー

1. **GitHubへのpush**
   - `main`または`master`ブランチへのpushを検知

2. **GitHub Actionsの実行**
   - Cloud Buildにビルドを送信

3. **Cloud Buildの実行**
   - Dockerイメージをビルド
   - Artifact Registryにプッシュ
   - GCE VMのメタデータを更新

4. **次回のVM起動時**
   - 更新された起動スクリプトが実行され、最新のDockerイメージが使用される

## トラブルシューティング

**詳細なトラブルシューティングガイドは [GitHub Actions と Cloud Build のトラブルシューティングガイド](./github_actions_troubleshooting.md) を参照してください。**

### ビルドが失敗する場合

1. Cloud Buildのログを確認：
   ```bash
   gcloud builds log <BUILD_ID> --project=bigquery-jukust
   ```

2. サービスアカウントの権限を確認：
   ```bash
   gcloud projects get-iam-policy bigquery-jukust \
     --flatten="bindings[].members" \
     --format="table(bindings.role,bindings.members)"
   ```

### GitHub Actionsが失敗する場合

1. GitHub Actionsのログを確認（リポジトリの「Actions」タブ）
2. `GCP_SA_KEY`シークレットが正しく設定されているか確認
3. サービスアカウントの権限を確認

### よくあるエラーと解決方法

#### 認証エラー
- `GCP_SA_KEY`シークレットが設定されていない場合は、[トラブルシューティングガイド](./github_actions_troubleshooting.md#認証エラー)を参照

#### 権限エラー
- Cloud Buildバケットへのアクセス権限がない場合は、[トラブルシューティングガイド](./github_actions_troubleshooting.md#エラー2-cloud-buildバケットへのアクセス権限がない)を参照
- サービスアカウントユーザー権限がない場合は、[トラブルシューティングガイド](./github_actions_troubleshooting.md#エラー3-サービスアカウントユーザー権限がない)を参照

#### Cloud Build設定エラー
- Substitution変数のエラーは、[トラブルシューティングガイド](./github_actions_troubleshooting.md#エラー4-substitution変数のエラー)を参照

## 注意事項

- デプロイは`main`または`master`ブランチへのpush時のみ実行されます
- デプロイには数分かかる場合があります
- VMは次回起動時に新しいイメージを使用します（即座に反映されません）
- 即座に反映したい場合は、手動でVMを再起動してください：
  ```bash
  gcloud compute instances reset gsc-scheduler-vm --zone=asia-northeast1-a --project=bigquery-jukust
  ```

