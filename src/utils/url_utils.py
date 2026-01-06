# src/utils/url_utils.py
from urllib.parse import urlparse, urlunparse
from collections import defaultdict

def normalize_url(url):
    """
    URLからクエリパラメータとフラグメント識別子を除去します。

    Args:
        url (str): 正規化前のURL

    Returns:
        str: クエリパラメータとフラグメント識別子を除去したURL
    """
    parsed_url = urlparse(url)
    # クエリとフラグメントを除去
    normalized_url = urlunparse(parsed_url._replace(query="", fragment=""))
    return normalized_url

def aggregate_records(records):
    """
    レコードをURLでグルーピングし、クリック数、インプレッション数、平均順位を集計します。

    Args:
        records (list): GSCから取得したレコードのリスト

    Returns:
        list: 集計後のレコードリスト
    """
    aggregated_data = defaultdict(lambda: {"clicks": 0, "impressions": 0, "positions": []})

    for record in records:
        query = record['keys'][0]
        url = record['keys'][1]
        clicks = record.get('clicks', 0)
        impressions = record.get('impressions', 0)
        position = record.get('position', 0.0)

        normalized_url = normalize_url(url)

        key = (query, normalized_url)
        aggregated_data[key]["clicks"] += clicks
        aggregated_data[key]["impressions"] += impressions
        aggregated_data[key]["positions"].append(position)

    # 平均順位を計算
    final_records = []
    for (query, url), data in aggregated_data.items():
        avg_position = sum(data["positions"]) / len(data["positions"]) if data["positions"] else 0.0
        final_records.append({
            "query": query,
            "url": url,
            "clicks": data["clicks"],
            "impressions": data["impressions"],
            "avg_position": avg_position  # フィールド名を統一
        })

    return final_records
