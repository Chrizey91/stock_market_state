import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add the project root and scripts directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.pipeline.fallback import fetch_with_fallback, fallback_duplicate_last_value

class TestFallback(unittest.TestCase):

    def test_fallback_duplicate_last_value_empty(self):
        # Empty list should return empty list if no mock generator exists
        res = fallback_duplicate_last_value("vix", [])
        self.assertEqual(res, [])

    def test_fallback_duplicate_last_value_success(self):
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        data = [{"date": yesterday, "value": 15.0}]
        res = fallback_duplicate_last_value("vix", data, today_str=today)
        
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["date"], yesterday)
        self.assertEqual(res[1]["date"], today)
        self.assertEqual(res[1]["value"], 15.0)

    def test_fetch_with_fallback_replace_success(self):
        fetcher = MagicMock(return_value=[{"date": "2026-06-30", "value": 20.0}])
        res = fetch_with_fallback(fetcher, "vix", {}, mode="replace")
        self.assertEqual(res, [{"date": "2026-06-30", "value": 20.0}])

    def test_fetch_with_fallback_replace_failure(self):
        fetcher = MagicMock(side_effect=Exception("API down"))
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        existing = {"vix": [{"date": yesterday, "value": 15.0}]}
        
        # Test fallback
        res = fetch_with_fallback(fetcher, "vix", existing, mode="replace")
        self.assertEqual(len(res), 2)
        self.assertEqual(res[1]["date"], today)
        self.assertEqual(res[1]["value"], 15.0)

    def test_fetch_with_fallback_upsert_success(self):
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        fetcher = MagicMock(return_value={"date": today, "value": 20.0})
        existing = {"fear_greed": [{"date": yesterday, "value": 15.0}]}
        
        res = fetch_with_fallback(fetcher, "fear_greed", existing, mode="upsert")
        self.assertEqual(len(res), 2)
        self.assertEqual(res[1]["date"], today)
        self.assertEqual(res[1]["value"], 20.0)

    def test_fetch_with_fallback_upsert_failure(self):
        fetcher = MagicMock(side_effect=Exception("API down"))
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        existing = {"fear_greed": [{"date": yesterday, "value": 15.0}]}
        res = fetch_with_fallback(fetcher, "fear_greed", existing, mode="upsert")
        
        # Should duplicate the last entry
        self.assertEqual(len(res), 2)
        self.assertEqual(res[1]["date"], today)
        self.assertEqual(res[1]["value"], 15.0)

if __name__ == '__main__':
    unittest.main()
