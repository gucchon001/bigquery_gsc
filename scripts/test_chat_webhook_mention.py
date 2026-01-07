#!/usr/bin/env python3
"""
Google Chat Incoming Webhook を使って、ユーザーIDメンション付きで通知を送るテストスクリプト
"""
import os
import sys
import json
import requests

# ユーザーID辞書（使い回し可能）
USER_IDS = {
    "haraguchi": "111863040728288757718",
}

def build_text(message: str, mentions=None) -> str:
    mentions = mentions or []
    ids = [USER_IDS[m] for m in mentions if m in USER_IDS]
    mention_text = " ".join([f"<users/{uid}>" for uid in ids])
    if mention_text:
        return f"{mention_text}\n\n{message}"
    return message

def main():
    webhook_url = os.getenv("Webhook_URL")
    if not webhook_url:
        print("ERROR: Webhook_URL environment variable is not set.")
        sys.exit(1)

    text = build_text("Webhook経由のメンション通知テストです。", mentions=["haraguchi"])
    payload = {
        "text": text
    }
    resp = requests.post(webhook_url, json=payload, timeout=10)
    if resp.ok:
        print("SUCCESS: Message sent via webhook.")
    else:
        print(f"ERROR: Failed to send message. status={resp.status_code} body={resp.text}")
        sys.exit(1)

if __name__ == "__main__":
    main()


