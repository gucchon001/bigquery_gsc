# Google Chat API メンション機能のセットアップガイド

このドキュメントでは、Google Chat APIを使用してエラー通知にメンション機能を追加する方法を説明します。

## 概要

Google Chat APIを使用することで、エラー通知時に特定のユーザー（原口さん: y-haraguchi@tomonokai-corp.com）をメンションできます。

## 前提条件

- Google Chat APIが有効になっていること
- サービスアカウントがGoogle Chatスペースにアクセスできること
- スペースIDが取得できること

## セットアップ手順

### 1. Google Chat APIの有効化

```bash
gcloud services enable chat.googleapis.com --project=bigquery-jukust
```

### 2. スペースIDの取得

Google ChatのスペースIDを取得する方法：

1. **Google Chatでスペースを開く**
2. **スペースのURLを確認**
   - URL形式: `https://chat.google.com/room/AAAAxxxxxxx`
   - `AAAAxxxxxxx`の部分がスペースIDです
3. **スペースIDの形式**
   - 使用する形式: `spaces/AAAAxxxxxxx`
   - 例: `spaces/AAAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 3. Secret ManagerにスペースIDを保存

```bash
# Secret ManagerにスペースIDを保存
echo -n "spaces/AAAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" | \
  gcloud secrets create chat-space-id \
    --data-file=- \
    --project=bigquery-jukust \
    --replication-policy="automatic"

# または既存のシークレットを更新
echo -n "spaces/AAAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" | \
  gcloud secrets versions add chat-space-id \
    --data-file=- \
    --project=bigquery-jukust
```

### 4. 環境変数の設定

Cloud Run Jobsの環境変数として設定するか、Secret Managerから読み込むように設定します。

**Secret Managerから読み込む場合**（推奨）:
- Secret Managerに`chat-space-id`という名前で保存されている場合、環境変数`CHAT_SPACE_ID`として読み込まれます

**環境変数として直接設定する場合**:
```bash
gcloud run jobs update bq-gsc-scraper-job \
  --set-env-vars="CHAT_SPACE_ID=spaces/AAAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  --region=asia-northeast1 \
  --project=bigquery-jukust
```

### 5. サービスアカウントの権限設定

サービスアカウントがGoogle Chatスペースにアクセスできるようにする必要があります。

**方法1: スペースにサービスアカウントを追加**
1. Google Chatスペースを開く
2. スペース設定 > メンバーとアプリ
3. 「メンバーを追加」をクリック
4. サービスアカウントのメールアドレス（`jukust-gcs@bigquery-jukust.iam.gserviceaccount.com`）を追加

**方法2: Google Workspace管理者に依頼**
- 組織のGoogle Workspace管理者に、サービスアカウントをGoogle Chatにアクセスできるように設定してもらう

## 使用方法

### 自動検出

`CHAT_SPACE_ID`環境変数が設定されている場合、自動的にGoogle Chat APIを使用してメンション機能付きで通知が送信されます。

### フォールバック

- `CHAT_SPACE_ID`が設定されていない場合、従来のWebhook方式が使用されます
- Google Chat APIの初期化に失敗した場合、Webhook方式にフォールバックします

## 動作確認

1. **環境変数の確認**
   ```bash
   gcloud run jobs describe bq-gsc-scraper-job \
     --region=asia-northeast1 \
     --project=bigquery-jukust \
     --format="value(spec.template.spec.containers[0].env)"
   ```

2. **テスト実行**
   - エラーを意図的に発生させて、メンション機能が動作することを確認

## トラブルシューティング

### メンションが動作しない

1. **スペースIDが正しいか確認**
   - スペースIDは`spaces/`で始まる必要があります
   - スペースURLから正しく取得できているか確認

2. **サービスアカウントがスペースにアクセスできるか確認**
   - サービスアカウントがスペースのメンバーになっているか確認
   - Google Workspace管理者に確認

3. **Google Chat APIの権限を確認**
   ```bash
   gcloud projects get-iam-policy bigquery-jukust \
     --flatten="bindings[].members" \
     --filter="bindings.members:jukust-gcs@bigquery-jukust.iam.gserviceaccount.com"
   ```

### エラーログの確認

```bash
gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="bq-gsc-scraper-job"' \
  --limit=50 \
  --project=bigquery-jukust
```

## 参考リンク

- [Google Chat API ドキュメント](https://developers.google.com/chat/api/guides)
- [Google Chat API メンション](https://developers.google.com/chat/api/guides/message-formats/mention-users)
- [Secret Manager ドキュメント](https://cloud.google.com/secret-manager/docs)

