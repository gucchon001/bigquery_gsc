# tests/test_url_utils.py
import unittest
from src.utils.url_utils import normalize_url, aggregate_records

class TestURLUtils(unittest.TestCase):

    def test_normalize_url(self):
        url_with_query = "https://www.juku.st/info/entry/843?param=value"
        expected = "https://www.juku.st/info/entry/843"
        self.assertEqual(normalize_url(url_with_query), expected)

        url_without_query = "https://www.juku.st/info/entry/843"
        self.assertEqual(normalize_url(url_without_query), url_without_query)

    def test_aggregate_records(self):
        records = [
            {
                'keys': ['query1', 'https://www.juku.st/info/entry/843?param=value1'],
                'clicks': 10,
                'impressions': 100,
                'position': 1.5
            },
            {
                'keys': ['query1', 'https://www.juku.st/info/entry/843?param=value2'],
                'clicks': 20,
                'impressions': 200,
                'position': 2.0
            },
            {
                'keys': ['query2', 'https://www.juku.st/info/entry/844'],
                'clicks': 5,
                'impressions': 50,
                'position': 3.0
            }
        ]

        expected = [
            {
                "query": "query1",
                "url": "https://www.juku.st/info/entry/843",
                "clicks": 30,
                "impressions": 300,
                "avg_position": 1.75
            },
            {
                "query": "query2",
                "url": "https://www.juku.st/info/entry/844",
                "clicks": 5,
                "impressions": 50,
                "avg_position": 3.0
            }
        ]

        result = aggregate_records(records)
        # ソートして比較
        self.assertEqual(sorted(result, key=lambda x: (x['query'], x['url'])),
                         sorted(expected, key=lambda x: (x['query'], x['url'])))

if __name__ == '__main__':
    unittest.main()
