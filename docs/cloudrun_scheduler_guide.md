# Cloud Run スケジュール設定ガイド

このドキュメントでは、Cloud Run JobsをCloud Schedulerで定期実行する際の設定方法と、よくある間違いをまとめています。他のプロジェクトでも再利用できる汎用的な内容となっています。

## 目次

1. [概要](#概要)
2. [前提条件](#前提条件)
3. [基本的な設定手順](#基本的な設定手順)
4. [よくある間違いと対処法](#よくある間違いと対処法)
5. [スケジュール式（Cron）の書き方](#スケジュール式cronの書き方)
6. [トラブルシューティング](#トラブルシューティング)
7. [ベストプラクティス](#ベストプラクティス)

## 概要

Cloud Schedulerを使用してCloud Run Jobsを定期実行する場合、以下のコンポーネントが必要です：

- **Cloud Run Jobs**: 実行するジョブ
- **Cloud Scheduler**: スケジュール管理
- **サービスアカウント**: 認証と権限管理
- **IAM権限**: Cloud SchedulerからCloud Run Jobsを実行する権限

## 前提条件

以下のAPIが有効になっている必要があります：

```bash
gcloud services enable \
    run.googleapis.com \
    cloudscheduler.googleapis.com \
    --project=YOUR_PROJECT_ID
```

## 基本的な設定手順

### 1. 変数の設定

```bash
export PROJECT_ID="your-project-id"
export REGION="asia-northeast1"  # または他のリージョン
export JOB_NAME="your-job-name"
export SCHEDULER_JOB_NAME="your-scheduler-job-name"
export SCHEDULER_SA="your-scheduler-sa@${PROJECT_ID}.iam.gserviceaccount.com"
```

### 2. Cloud Scheduler用サービスアカウントの作成（推奨）

専用のサービスアカウントを作成することで、権限管理が明確になります：

```bash
# サービスアカウントの作成
gcloud iam service-accounts create cloud-scheduler-sa \
    --display-name="Cloud Scheduler Service Account" \
    --project=${PROJECT_ID}

# サービスアカウントのメールアドレスを変数に設定
export SCHEDULER_SA="cloud-scheduler-sa@${PROJECT_ID}.iam.gserviceaccount.com"
```

### 3. IAM権限の設定

**重要**: Cloud SchedulerがCloud Run Jobsを実行するには、`roles/run.invoker`権限が必要です。

```bash
# Cloud Run Jobsの実行権限を付与
gcloud run jobs add-iam-policy-binding ${JOB_NAME} \
    --region=${REGION} \
    --member="serviceAccount:${SCHEDULER_SA}" \
    --role="roles/run.invoker" \
    --project=${PROJECT_ID}
```

### 4. Cloud Schedulerジョブの作成

```bash
gcloud scheduler jobs create http ${SCHEDULER_JOB_NAME} \
    --location=${REGION} \
    --schedule="0 9 * * *" \
    --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
    --http-method=POST \
    --oauth-service-account-email=${SCHEDULER_SA} \
    --time-zone="Asia/Tokyo" \
    --project=${PROJECT_ID}
```

## よくある間違いと対処法

### ❌ 間違い1: タイムゾーンの指定漏れ

**問題**: `--time-zone`を指定しないと、デフォルトでUTC（協定世界時）になります。日本時間で実行したい場合、意図した時刻とずれます。

```bash
# ❌ 間違い: タイムゾーン未指定（UTCになる）
gcloud scheduler jobs create http my-schedule \
    --schedule="0 9 * * *" \
    --uri="..." \
    --project=${PROJECT_ID}

# ✅ 正しい: タイムゾーンを明示的に指定
gcloud scheduler jobs create http my-schedule \
    --schedule="0 9 * * *" \
    --time-zone="Asia/Tokyo" \
    --uri="..." \
    --project=${PROJECT_ID}
```

**確認方法**:
```bash
gcloud scheduler jobs describe ${SCHEDULER_JOB_NAME} \
    --location=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(timeZone)"
```

### ❌ 間違い2: IAM権限の設定漏れ

**問題**: Cloud Schedulerのサービスアカウントに`roles/run.invoker`権限を付与していないと、403エラーが発生します。

**症状**: Cloud Schedulerの実行履歴で以下のエラーが表示される：
```
Permission denied. The caller does not have permission
```

**対処法**:
```bash
# 権限の確認
gcloud run jobs get-iam-policy ${JOB_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID}

# 権限の付与（まだ付与されていない場合）
gcloud run jobs add-iam-policy-binding ${JOB_NAME} \
    --region=${REGION} \
    --member="serviceAccount:${SCHEDULER_SA}" \
    --role="roles/run.invoker" \
    --project=${PROJECT_ID}
```

### ❌ 間違い3: URIの形式が間違っている

**問題**: Cloud Run Jobsの実行URIは特定の形式である必要があります。

```bash
# ❌ 間違い: Cloud Run Services用のURI形式
--uri="https://${JOB_NAME}-xxxxx-${REGION}.a.run.run"

# ❌ 間違い: 間違ったエンドポイント
--uri="https://run.googleapis.com/v1/projects/${PROJECT_ID}/jobs/${JOB_NAME}:run"

# ✅ 正しい: Cloud Run Jobs用の正しいURI形式
--uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run"
```

**URI形式の確認方法**:
```bash
# Cloud Run Jobsの正しいURIを取得
gcloud run jobs describe ${JOB_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(status.url)"
```

### ❌ 間違い4: リージョンの不一致

**問題**: Cloud Run JobsとCloud Schedulerのリージョンが異なると、実行に失敗する可能性があります。

```bash
# ❌ 間違い: リージョンが異なる
gcloud run jobs create my-job --region=asia-northeast1 ...
gcloud scheduler jobs create http my-schedule --location=us-central1 ...

# ✅ 正しい: 同じリージョンを使用
gcloud run jobs create my-job --region=asia-northeast1 ...
gcloud scheduler jobs create http my-schedule --location=asia-northeast1 ...
```

**確認方法**:
```bash
# Cloud Run Jobsのリージョン確認
gcloud run jobs describe ${JOB_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(metadata.labels['cloud.googleapis.com/location'])"

# Cloud Schedulerのリージョン確認
gcloud scheduler jobs describe ${SCHEDULER_JOB_NAME} \
    --location=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(region)"
```

### ❌ 間違い5: プロジェクトIDの指定漏れ

**問題**: 複数のプロジェクトを使用している場合、プロジェクトIDの指定漏れで意図しないプロジェクトにリソースが作成されます。

```bash
# ❌ 間違い: プロジェクトID未指定（デフォルトプロジェクトが使用される）
gcloud scheduler jobs create http my-schedule \
    --schedule="0 9 * * *" \
    --uri="..."

# ✅ 正しい: プロジェクトIDを明示的に指定
gcloud scheduler jobs create http my-schedule \
    --schedule="0 9 * * *" \
    --uri="..." \
    --project=${PROJECT_ID}
```

**対処法**: すべてのコマンドで`--project`オプションを明示的に指定することを推奨します。

### ❌ 間違い6: スケジュール式の誤り

**問題**: Cron式の形式が間違っていると、スケジュールが正しく動作しません。

```bash
# ❌ 間違い: 5フィールド形式ではない
--schedule="0 9 * * * *"  # 6フィールド（間違い）

# ❌ 間違い: フィールドの順序が間違っている
--schedule="* * * 9 0"  # 分 時 日 月 曜日（間違い）

# ✅ 正しい: 5フィールド形式（分 時 日 月 曜日）
--schedule="0 9 * * *"  # 毎日9時0分
```

詳細は[スケジュール式（Cron）の書き方](#スケジュール式cronの書き方)を参照してください。

### ❌ 間違い7: 既存スケジューラーの更新方法の誤り

**問題**: 既存のスケジューラーを更新する際に`create`コマンドを使用するとエラーになります。

```bash
# ❌ 間違い: 既存のスケジューラーに対してcreateコマンドを使用
gcloud scheduler jobs create http existing-schedule \
    --schedule="0 10 * * *" \
    --uri="..."
# エラー: Job [existing-schedule] already exists

# ✅ 正しい: updateコマンドを使用
gcloud scheduler jobs update http existing-schedule \
    --schedule="0 10 * * *" \
    --location=${REGION} \
    --project=${PROJECT_ID}
```

**対処法**: 既存かどうかを確認してから適切なコマンドを使用：

```bash
# 既存かどうかを確認
if gcloud scheduler jobs describe ${SCHEDULER_JOB_NAME} \
    --location=${REGION} \
    --project=${PROJECT_ID} &>/dev/null; then
    echo "Updating existing scheduler job..."
    gcloud scheduler jobs update http ${SCHEDULER_JOB_NAME} \
        --schedule="0 10 * * *" \
        --location=${REGION} \
        --project=${PROJECT_ID}
else
    echo "Creating new scheduler job..."
    gcloud scheduler jobs create http ${SCHEDULER_JOB_NAME} \
        --schedule="0 10 * * *" \
        --uri="..." \
        --location=${REGION} \
        --project=${PROJECT_ID}
fi
```

### ❌ 間違い8: サービスアカウントの指定漏れ

**問題**: `--oauth-service-account-email`を指定しないと、デフォルトのCompute Engineサービスアカウントが使用され、権限不足でエラーになる可能性があります。

```bash
# ❌ 間違い: サービスアカウント未指定
gcloud scheduler jobs create http my-schedule \
    --schedule="0 9 * * *" \
    --uri="..." \
    --project=${PROJECT_ID}

# ✅ 正しい: サービスアカウントを明示的に指定
gcloud scheduler jobs create http my-schedule \
    --schedule="0 9 * * *" \
    --uri="..." \
    --oauth-service-account-email=${SCHEDULER_SA} \
    --project=${PROJECT_ID}
```

## スケジュール式（Cron）の書き方

Cloud Schedulerは標準的なCron形式（5フィールド）をサポートしています：

```
分 時 日 月 曜日
```

### フィールドの説明

| フィールド | 範囲 | 説明 |
|-----------|------|------|
| 分 | 0-59 | 分 |
| 時 | 0-23 | 時（24時間形式） |
| 日 | 1-31 | 日 |
| 月 | 1-12 または JAN-DEC | 月 |
| 曜日 | 0-6 または SUN-SAT | 曜日（0またはSUNが日曜日） |

### よく使うスケジュール例

```bash
# 毎日午前9時（JST）
--schedule="0 9 * * *" --time-zone="Asia/Tokyo"

# 毎日午前0時（JST）
--schedule="0 0 * * *" --time-zone="Asia/Tokyo"

# 毎週月曜日の午前9時（JST）
--schedule="0 9 * * 1" --time-zone="Asia/Tokyo"
# または
--schedule="0 9 * * MON" --time-zone="Asia/Tokyo"

# 毎月1日の午前0時（JST）
--schedule="0 0 1 * *" --time-zone="Asia/Tokyo"

# 平日（月〜金）の午前9時（JST）
--schedule="0 9 * * 1-5" --time-zone="Asia/Tokyo"
# または
--schedule="0 9 * * MON-FRI" --time-zone="Asia/Tokyo"

# 30分ごと
--schedule="*/30 * * * *" --time-zone="Asia/Tokyo"

# 毎時0分と30分
--schedule="0,30 * * * *" --time-zone="Asia/Tokyo"

# 毎日午前8時45分（JST）
--schedule="45 8 * * *" --time-zone="Asia/Tokyo"
```

### タイムゾーンの指定

**重要**: 必ず`--time-zone`オプションでタイムゾーンを指定してください。

```bash
# 日本時間（JST）
--time-zone="Asia/Tokyo"

# アメリカ東部時間（EST/EDT）
--time-zone="America/New_York"

# 協定世界時（UTC）
--time-zone="UTC"

# その他のタイムゾーン
--time-zone="Europe/London"
--time-zone="America/Los_Angeles"
```

利用可能なタイムゾーンの一覧：
```bash
# IANAタイムゾーンデータベースを参照
# https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
```

## トラブルシューティング

### スケジューラーが実行されない

1. **スケジューラーの状態を確認**:
```bash
gcloud scheduler jobs describe ${SCHEDULER_JOB_NAME} \
    --location=${REGION} \
    --project=${PROJECT_ID}
```

2. **実行履歴を確認**:
```bash
gcloud scheduler jobs list \
    --location=${REGION} \
    --project=${PROJECT_ID}

# 実行履歴の詳細
gcloud logging read \
    "resource.type=cloud_scheduler_job AND resource.labels.job_id=${SCHEDULER_JOB_NAME}" \
    --limit=50 \
    --project=${PROJECT_ID} \
    --format="table(timestamp,severity,textPayload)"
```

3. **手動実行でテスト**:
```bash
gcloud scheduler jobs run ${SCHEDULER_JOB_NAME} \
    --location=${REGION} \
    --project=${PROJECT_ID}
```

### 403 Permission Denied エラー

1. **IAM権限を確認**:
```bash
gcloud run jobs get-iam-policy ${JOB_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID}
```

2. **権限を再付与**:
```bash
gcloud run jobs add-iam-policy-binding ${JOB_NAME} \
    --region=${REGION} \
    --member="serviceAccount:${SCHEDULER_SA}" \
    --role="roles/run.invoker" \
    --project=${PROJECT_ID}
```

### 404 Not Found エラー

1. **Cloud Run Jobsが存在するか確認**:
```bash
gcloud run jobs describe ${JOB_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID}
```

2. **URIが正しいか確認**:
```bash
# 正しいURI形式
https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run
```

### スケジュールが意図した時刻に実行されない

1. **タイムゾーンを確認**:
```bash
gcloud scheduler jobs describe ${SCHEDULER_JOB_NAME} \
    --location=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(timeZone)"
```

2. **スケジュール式を確認**:
```bash
gcloud scheduler jobs describe ${SCHEDULER_JOB_NAME} \
    --location=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(schedule)"
```

3. **次回実行時刻を確認**:
```bash
gcloud scheduler jobs describe ${SCHEDULER_JOB_NAME} \
    --location=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(scheduleTime)"
```

## ベストプラクティス

### 1. 変数を使用して設定を一元管理

```bash
#!/bin/bash
# config.sh
export PROJECT_ID="your-project-id"
export REGION="asia-northeast1"
export JOB_NAME="your-job-name"
export SCHEDULER_JOB_NAME="your-scheduler-job-name"
export SCHEDULER_SA="cloud-scheduler-sa@${PROJECT_ID}.iam.gserviceaccount.com"
export SCHEDULE="0 9 * * *"
export TIME_ZONE="Asia/Tokyo"
```

### 2. 設定の検証スクリプト

```bash
#!/bin/bash
# verify_scheduler.sh

# スケジューラーの存在確認
if ! gcloud scheduler jobs describe ${SCHEDULER_JOB_NAME} \
    --location=${REGION} \
    --project=${PROJECT_ID} &>/dev/null; then
    echo "❌ Scheduler job not found"
    exit 1
fi

# IAM権限の確認
if ! gcloud run jobs get-iam-policy ${JOB_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --flatten="bindings[].members" \
    --filter="bindings.members:${SCHEDULER_SA}" \
    --format="value(bindings.role)" | grep -q "roles/run.invoker"; then
    echo "❌ IAM permission not set"
    exit 1
fi

# Cloud Run Jobsの存在確認
if ! gcloud run jobs describe ${JOB_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} &>/dev/null; then
    echo "❌ Cloud Run Job not found"
    exit 1
fi

echo "✅ All checks passed"
```

### 3. 段階的なデプロイ

1. まず手動実行でテスト
2. スケジューラーを作成（頻度を高く設定してテスト）
3. 本番スケジュールに変更

```bash
# 1. 手動実行テスト
gcloud run jobs execute ${JOB_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID}

# 2. テスト用スケジューラー（5分ごと）
gcloud scheduler jobs create http ${SCHEDULER_JOB_NAME}-test \
    --schedule="*/5 * * * *" \
    --uri="..." \
    --location=${REGION} \
    --project=${PROJECT_ID}

# 3. 本番スケジュールに更新
gcloud scheduler jobs update http ${SCHEDULER_JOB_NAME}-test \
    --schedule="0 9 * * *" \
    --location=${REGION} \
    --project=${PROJECT_ID}
```

### 4. ログ監視の設定

```bash
# Cloud Schedulerの実行ログを監視
gcloud logging read \
    "resource.type=cloud_scheduler_job AND resource.labels.job_id=${SCHEDULER_JOB_NAME}" \
    --limit=10 \
    --project=${PROJECT_ID} \
    --format="table(timestamp,severity,textPayload)"

# Cloud Run Jobsの実行ログを監視
gcloud logging read \
    "resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME}" \
    --limit=10 \
    --project=${PROJECT_ID} \
    --format="table(timestamp,severity,textPayload)"
```

### 5. エラー通知の設定

Cloud Schedulerの失敗時に通知を受け取るには、Cloud Monitoringのアラートポリシーを設定します。

```bash
# アラートポリシーの作成例（Cloud Consoleで設定することを推奨）
# https://cloud.google.com/monitoring/alerts
```

## 完全なセットアップスクリプト例

```bash
#!/bin/bash
# setup_scheduler.sh

set -e  # エラー時に停止

# 変数の設定
export PROJECT_ID="your-project-id"
export REGION="asia-northeast1"
export JOB_NAME="your-job-name"
export SCHEDULER_JOB_NAME="your-scheduler-job-name"
export SCHEDULER_SA="cloud-scheduler-sa@${PROJECT_ID}.iam.gserviceaccount.com"
export SCHEDULE="0 9 * * *"
export TIME_ZONE="Asia/Tokyo"

# 1. サービスアカウントの作成（存在しない場合）
if ! gcloud iam service-accounts describe ${SCHEDULER_SA} \
    --project=${PROJECT_ID} &>/dev/null; then
    echo "Creating service account..."
    gcloud iam service-accounts create cloud-scheduler-sa \
        --display-name="Cloud Scheduler Service Account" \
        --project=${PROJECT_ID}
fi

# 2. IAM権限の設定
echo "Setting IAM permissions..."
gcloud run jobs add-iam-policy-binding ${JOB_NAME} \
    --region=${REGION} \
    --member="serviceAccount:${SCHEDULER_SA}" \
    --role="roles/run.invoker" \
    --project=${PROJECT_ID}

# 3. URIの構築
JOB_URI="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run"

# 4. スケジューラーの作成または更新
if gcloud scheduler jobs describe ${SCHEDULER_JOB_NAME} \
    --location=${REGION} \
    --project=${PROJECT_ID} &>/dev/null; then
    echo "Updating existing scheduler job..."
    gcloud scheduler jobs update http ${SCHEDULER_JOB_NAME} \
        --schedule="${SCHEDULE}" \
        --uri="${JOB_URI}" \
        --oauth-service-account-email=${SCHEDULER_SA} \
        --time-zone=${TIME_ZONE} \
        --location=${REGION} \
        --project=${PROJECT_ID}
else
    echo "Creating new scheduler job..."
    gcloud scheduler jobs create http ${SCHEDULER_JOB_NAME} \
        --schedule="${SCHEDULE}" \
        --uri="${JOB_URI}" \
        --http-method=POST \
        --oauth-service-account-email=${SCHEDULER_SA} \
        --time-zone=${TIME_ZONE} \
        --location=${REGION} \
        --project=${PROJECT_ID}
fi

echo "✅ Scheduler setup completed"
echo "Scheduler job: ${SCHEDULER_JOB_NAME}"
echo "Schedule: ${SCHEDULE} (${TIME_ZONE})"
echo "Target job: ${JOB_NAME}"
```

## 参考リンク

- [Cloud Scheduler ドキュメント](https://cloud.google.com/scheduler/docs)
- [Cloud Run Jobs ドキュメント](https://cloud.google.com/run/docs/create-jobs)
- [Cron形式のリファレンス](https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules)
- [IAM権限のリファレンス](https://cloud.google.com/iam/docs/understanding-roles)

## チェックリスト

スケジュール設定を行う際の確認項目：

- [ ] Cloud Scheduler APIが有効になっている
- [ ] Cloud Run Jobsが作成されている
- [ ] サービスアカウントが作成されている
- [ ] IAM権限（`roles/run.invoker`）が設定されている
- [ ] URIが正しい形式である
- [ ] リージョンが一致している
- [ ] タイムゾーンが指定されている
- [ ] スケジュール式（Cron）が正しい
- [ ] プロジェクトIDがすべてのコマンドで指定されている
- [ ] 手動実行でテスト済み


