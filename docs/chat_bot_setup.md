# Google Chat Bot セットアップガイド

Google Chat APIを使用してメンション機能を有効にするには、サービスアカウントをChat Botとして設定する必要があります。

## 前提条件

- Google Workspace管理者権限
- Google Chat APIが有効になっていること
- サービスアカウントが作成されていること

## セットアップ手順

### 方法1: Google Workspace管理コンソールで設定（推奨）

1. **Google Workspace管理コンソールにアクセス**
   - https://admin.google.com/ にアクセス
   - 管理者アカウントでログイン

2. **Chat Botの作成**
   - 「アプリ」>「Google Chat API」に移動
   - 「Chat Botを作成」をクリック
   - サービスアカウントのメールアドレスを入力:
     - `jukust-gcs@bigquery-jukust.iam.gserviceaccount.com`
   - Bot名を設定（例: "GSC Scraper Bot"）
   - 「作成」をクリック

3. **スペースへの追加**
   - Google Chatで対象のスペースを開く
   - スペース設定 > メンバーとアプリ
   - 「メンバーを追加」をクリック
   - サービスアカウントのメールアドレスを追加

### 方法2: Google Cloud Consoleで設定

1. **Google Cloud Consoleでプロジェクトを選択**
   ```bash
   gcloud config set project bigquery-jukust
   ```

2. **Chat APIの設定**
   - Google Cloud Console > APIとサービス > Google Chat API
   - 「設定」タブを開く
   - 「Chat Botを作成」をクリック

3. **サービスアカウントをBotとして登録**
   - サービスアカウント: `jukust-gcs@bigquery-jukust.iam.gserviceaccount.com`
   - Bot名: "GSC Scraper Bot"
   - 説明: "GSC Data Scraper notification bot"

## 認証スコープ

Google Chat APIを使用するには、以下のスコープが必要です：

```
https://www.googleapis.com/auth/chat.bot
```

このスコープは、サービスアカウントがChat Botとして動作するために必要です。

## 動作確認

Chat Botとして設定後、以下のコマンドでテストできます：

```bash
# 環境変数を設定
export CHAT_SPACE_ID=spaces/AAQAnTHYlco

# テストスクリプトを実行
python scripts/test_chat_mention.py
```

## トラブルシューティング

### エラー: "Request had insufficient authentication scopes"

**原因**: サービスアカウントがChat Botとして設定されていない

**解決方法**:
1. Google Workspace管理コンソールでChat Botを作成
2. サービスアカウントをスペースのメンバーに追加
3. 数分待ってから再度試行（設定の反映に時間がかかる場合があります）

### エラー: "Permission denied"

**原因**: サービスアカウントがスペースのメンバーではない

**解決方法**:
1. Google Chatでスペースを開く
2. スペース設定 > メンバーとアプリ
3. サービスアカウントのメールアドレスを追加

### メンションが動作しない

**原因**: メンション形式が正しくない、またはユーザーIDが必要

**解決方法**:
- メールアドレス形式: `<users/y-haraguchi@tomonokai-corp.com>`
- ユーザーID形式: `<users/USER_ID>`（ユーザーIDが必要な場合）

## 参考リンク

- [Google Chat API ドキュメント](https://developers.google.com/chat/api/guides)
- [Chat Bot の作成](https://developers.google.com/chat/api/guides/auth/service-accounts)
- [Google Workspace管理コンソール](https://admin.google.com/)

