# GitHub Actions と Cloud Build のトラブルシューティングガイド

このドキュメントでは、GitHub ActionsからCloud Buildを実行する際によく発生するエラーとその解決方法をまとめています。

## 目次

1. [認証エラー](#認証エラー)
2. [権限エラー](#権限エラー)
3. [Cloud Build設定エラー](#cloud-build設定エラー)
4. [サービスアカウント関連エラー](#サービスアカウント関連エラー)
5. [チェックリスト](#チェックリスト)

---

## 認証エラー

### エラー1: `workload_identity_provider` または `credentials_json` が指定されていない

**エラーメッセージ:**
```
Error: google-github-actions/auth failed with: the GitHub Action workflow must specify exactly one of "workload_identity_provider" or "credentials_json"!
```

**原因:**
- GitHubリポジトリに`GCP_SA_KEY`シークレットが設定されていない
- シークレットが空の値になっている
- フォークからのプルリクエストの場合、シークレットは利用できない

**解決方法:**

1. **サービスアカウントキーの作成**（まだ作成していない場合）:
   ```bash
   gcloud iam service-accounts keys create github-actions-key.json \
     --iam-account=jukust-gcs@bigquery-jukust.iam.gserviceaccount.com \
     --project=bigquery-jukust
   ```

2. **GitHub Secretsの設定**:
   - GitHub CLIを使用する場合:
     ```bash
     gh secret set GCP_SA_KEY < github-actions-key.json
     ```
   - 手動で設定する場合:
     - GitHubリポジトリの Settings > Secrets and variables > Actions に移動
     - "New repository secret" をクリック
     - Name: `GCP_SA_KEY`
     - Secret: `github-actions-key.json`の内容全体をコピー&ペースト

3. **ワークフローでの検証ステップ追加**（推奨）:
   ```yaml
   - name: Validate GCP credentials
     env:
       GCP_SA_KEY: ${{ secrets.GCP_SA_KEY }}
     run: |
       if [ -z "$GCP_SA_KEY" ]; then
         echo "::error::GCP_SA_KEY secret is not set or is empty"
         exit 1
       fi
       if ! echo "$GCP_SA_KEY" | jq empty 2>/dev/null; then
         echo "::error::GCP_SA_KEY does not appear to be valid JSON"
         exit 1
       fi
       echo "✓ GCP_SA_KEY secret is set and appears to be valid JSON"
   ```

---

## 権限エラー

### エラー2: Cloud Buildバケットへのアクセス権限がない

**エラーメッセージ:**
```
ERROR: (gcloud.builds.submit) The user is forbidden from accessing the bucket [bigquery-jukust_cloudbuild]. 
Please check your organization's policy or if the user has the "serviceusage.services.use" permission.
```

**原因:**
- GitHub Actionsで使用しているサービスアカウントに、Cloud Buildサービスを使用する権限がない
- Cloud Storageバケットへのアクセス権限がない

**解決方法:**

以下の権限を付与します：

```bash
PROJECT_ID="bigquery-jukust"
SERVICE_ACCOUNT="jukust-gcs@bigquery-jukust.iam.gserviceaccount.com"

# Cloud Build Editor権限
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/cloudbuild.builds.editor"

# Service Usage Consumer権限
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/serviceusage.serviceUsageConsumer"

# Storage Admin権限（Cloud Buildバケットへのアクセス用）
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/storage.admin"
```

### エラー3: サービスアカウントユーザー権限がない

**エラーメッセージ:**
```
ERROR: (gcloud.builds.submit) PERMISSION_DENIED: Permission 'iam.serviceAccounts.actAs' denied on service account [ID: 114348919693888452740]
```

**原因:**
- GitHub Actionsで使用しているサービスアカウントが、Cloud Buildの実行時に使用するサービスアカウントを「なりすます」権限を持っていない

**解決方法:**

1. **プロジェクト番号の確認**:
   ```bash
   PROJECT_NUMBER=$(gcloud projects describe bigquery-jukust --format="value(projectNumber)")
   echo $PROJECT_NUMBER  # 例: 883093986860
   ```

2. **Compute Engineデフォルトサービスアカウントへの権限付与**:
   ```bash
   gcloud iam service-accounts add-iam-policy-binding \
     ${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
     --member="serviceAccount:jukust-gcs@bigquery-jukust.iam.gserviceaccount.com" \
     --role="roles/iam.serviceAccountUser" \
     --project=bigquery-jukust
   ```

3. **ワークフローでサービスアカウントを明示的に指定**:
   ```yaml
   - name: Submit Cloud Build
     run: |
       gcloud builds submit \
         --config=cloudbuild.yaml \
         --service-account="projects/bigquery-jukust/serviceAccounts/${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
         --project=bigquery-jukust
   ```

**重要:** `--service-account`オプションには、フルパス形式（`projects/{PROJECT_ID}/serviceAccounts/{EMAIL}`）で指定する必要があります。

---

## Cloud Build設定エラー

### エラー4: Substitution変数のエラー

**エラーメッセージ1:**
```
ERROR: (gcloud.builds.submit) INVALID_ARGUMENT: invalid value for 'build.substitutions': 
key in the template "IMAGE_URL" is not a valid built-in substitution
```

**原因:**
- Cloud Buildは`${VARIABLE}`形式の文字列をすべてsubstitutionとして解釈する
- bashスクリプト内のローカル変数（例：`IMAGE_URL`）がCloud Buildのsubstitutionとして解釈されてしまう

**解決方法:**

bashスクリプト内で変数を使わず、直接値を展開する：

```yaml
# ❌ 悪い例
- name: 'gcr.io/cloud-builders/gcloud'
  entrypoint: 'bash'
  args:
    - '-c'
    - |
      IMAGE_URL="${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPOSITORY}/${_IMAGE_NAME}:latest"
      gcloud run jobs update ${_JOB_NAME} --image=${IMAGE_URL}

# ✅ 良い例
- name: 'gcr.io/cloud-builders/gcloud'
  entrypoint: 'bash'
  args:
    - '-c'
    - |
      gcloud run jobs update ${_JOB_NAME} \
        --image=${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPOSITORY}/${_IMAGE_NAME}:latest
```

**エラーメッセージ2:**
```
ERROR: (gcloud.builds.submit) INVALID_ARGUMENT: invalid image name "...bq-gsc-scraper:": 
could not parse reference: ...bq-gsc-scraper:
```

**原因:**
- `SHORT_SHA`はCloud Buildの組み込み変数だが、GitHub Actionsから`gcloud builds submit`を実行する場合は自動的に設定されない

**解決方法:**

1. **カスタム変数を使用**（推奨）:
   ```yaml
   # cloudbuild.yaml
   substitutions:
     _SHORT_SHA: 'latest'  # デフォルト値
   ```
   
   ```yaml
   # .github/workflows/deploy.yml
   - name: Submit Cloud Build
     run: |
       SHORT_SHA=$(echo "${{ github.sha }}" | cut -c1-7)
       gcloud builds submit \
         --config=cloudbuild.yaml \
         --substitutions=_SHORT_SHA=${SHORT_SHA},...
   ```

2. **cloudbuild.yamlでSHORT_SHAを_SHORT_SHAに置き換え**:
   ```yaml
   # すべての${SHORT_SHA}を${_SHORT_SHA}に変更
   - '${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPOSITORY}/${_IMAGE_NAME}:${_SHORT_SHA}'
   ```

---

## サービスアカウント関連エラー

### エラー5: --service-accountオプションの形式エラー

**エラーメッセージ:**
```
ERROR: (gcloud.builds.submit) INVALID_ARGUMENT: invalid value for '--service-account'
```

**原因:**
- `--service-account`オプションにメールアドレス形式で指定している
- フルパス形式（`projects/{PROJECT_ID}/serviceAccounts/{EMAIL}`）で指定する必要がある

**解決方法:**

```yaml
# ❌ 悪い例
--service-account=883093986860-compute@developer.gserviceaccount.com

# ✅ 良い例
--service-account="projects/bigquery-jukust/serviceAccounts/883093986860-compute@developer.gserviceaccount.com"
```

---

## チェックリスト

GitHub ActionsからCloud Buildを正常に実行するために、以下のチェックリストを確認してください：

### 認証
- [ ] `GCP_SA_KEY`シークレットがGitHubリポジトリに設定されている
- [ ] シークレットの値が有効なJSON形式である
- [ ] ワークフローに認証ステップが含まれている

### 権限
- [ ] `roles/cloudbuild.builds.editor`が付与されている
- [ ] `roles/serviceusage.serviceUsageConsumer`が付与されている
- [ ] `roles/storage.admin`が付与されている（Cloud Buildバケットへのアクセス用）
- [ ] `roles/iam.serviceAccountUser`が付与されている（サービスアカウントのなりすまし用）

### Cloud Build設定
- [ ] `cloudbuild.yaml`が存在し、構文が正しい
- [ ] substitution変数が正しく定義されている
- [ ] bashスクリプト内で不要な変数を使用していない
- [ ] `SHORT_SHA`などの組み込み変数をカスタム変数に置き換えている（必要に応じて）

### ワークフロー設定
- [ ] `gcloud builds submit`コマンドが正しく記述されている
- [ ] `--service-account`オプションがフルパス形式で指定されている
- [ ] 必要なsubstitution変数がすべて渡されている

### API有効化
- [ ] Cloud Build APIが有効になっている
- [ ] Artifact Registry APIが有効になっている（イメージをプッシュする場合）

---

## よくある質問（FAQ）

### Q1: 権限を付与してもエラーが解消されない

**A:** 権限の反映には数分かかることがあります。また、サービスアカウントキーを再生成する必要がある場合もあります。

### Q2: フォークからのプルリクエストでワークフローが失敗する

**A:** セキュリティ上の理由で、フォークからのプルリクエストではGitHub Secretsは利用できません。この場合は、フォークをマージしてから本番ブランチで実行してください。

### Q3: Cloud Buildのサービスアカウントが見つからない

**A:** Cloud Build APIを有効化すると、自動的にサービスアカウントが作成されます。しばらく待ってから再度試してください。

### Q4: substitution変数の優先順位は？

**A:** `gcloud builds submit`の`--substitutions`で指定した値が、`cloudbuild.yaml`のデフォルト値を上書きします。

---

## 参考リンク

- [Google Cloud Build ドキュメント](https://cloud.google.com/build/docs)
- [GitHub Actions for Google Cloud](https://github.com/google-github-actions)
- [Cloud Build IAM とアクセス権限](https://cloud.google.com/build/docs/iam-and-access-control)
- [サービスアカウントの権限](https://cloud.google.com/iam/docs/service-accounts)

---

## 更新履歴

- 2026-01-06: 初版作成
  - 認証エラーのトラブルシューティング
  - 権限エラーのトラブルシューティング
  - Cloud Build設定エラーのトラブルシューティング
  - サービスアカウント関連エラーのトラブルシューティング

