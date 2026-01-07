#!/usr/bin/env python3
"""
Google Chat APIを使用してメンション機能付きの通知をテストするスクリプト
"""
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def test_chat_mention():
    """Google Chat APIを使用してメンション機能付きの通知をテスト"""
    
    # スペースIDの取得
    space_id = os.getenv("CHAT_SPACE_ID")
    if not space_id:
        print("エラー: CHAT_SPACE_ID環境変数が設定されていません")
        print("設定方法: export CHAT_SPACE_ID=spaces/AAQAnTHYlco")
        return False
    
    # メンション対象のユーザー
    mention_email = "y-haraguchi@tomonokai-corp.com"
    
    try:
        # 認証情報の取得
        print("認証情報を取得しています...")
        # Google Chat APIに必要なスコープ
        scopes = ["https://www.googleapis.com/auth/chat.bot"]
        credentials, project = default(scopes=scopes)
        print(f"認証成功: プロジェクト={project}")
        
        # Google Chat APIクライアントの構築
        print("Google Chat APIクライアントを初期化しています...")
        chat_service = build('chat', 'v1', credentials=credentials)
        
        # テストメッセージの構築
        print(f"メッセージを構築しています（スペース: {space_id}）...")
        message_body = {
            "text": f"<users/{mention_email}> テスト通知です。メンション機能の動作確認をお願いします。",
            "cardsV2": [
                {
                    "cardId": "test-notification",
                    "card": {
                        "header": {
                            "title": "GSC Scraper テスト通知",
                            "subtitle": "メンション機能のテスト",
                            "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/info/default/48px.svg",
                            "imageType": "CIRCLE"
                        },
                        "sections": [
                            {
                                "widgets": [
                                    {
                                        "decoratedText": {
                                            "topLabel": "テストメッセージ",
                                            "text": "これはGoogle Chat APIを使用したメンション機能のテストです。",
                                            "wrapText": True
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        # メッセージの送信
        print(f"メッセージを送信しています...")
        result = chat_service.spaces().messages().create(
            parent=space_id,
            body=message_body
        ).execute()
        
        message_id = result.get('name', 'N/A')
        print(f"✅ メッセージ送信成功！")
        print(f"   メッセージID: {message_id}")
        print(f"   スペース: {space_id}")
        print(f"   メンション: {mention_email}")
        return True
        
    except HttpError as e:
        print(f"ERROR: Google Chat API error: {e}")
        print(f"   Error details: {e.error_details if hasattr(e, 'error_details') else 'N/A'}")
        print("\nTroubleshooting:")
        print("1. Check if service account is a member of the space")
        print("2. Check if Google Chat API is enabled")
        print("3. Check if space ID is correct")
        print("4. Check if service account has Chat Bot permissions")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Google Chat API Mention Function Test")
    print("=" * 60)
    print()
    
    success = test_chat_mention()
    
    print()
    print("=" * 60)
    if success:
        print("Test completed: SUCCESS")
    else:
        print("Test completed: FAILED")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

