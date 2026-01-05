# Dockerfile for GCE定期実行環境

FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY src/ ./src/
COPY config/ ./config/

# ログディレクトリの作成
RUN mkdir -p logs

# 環境変数の設定
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# エントリーポイント
ENTRYPOINT ["python", "src/main.py"]

