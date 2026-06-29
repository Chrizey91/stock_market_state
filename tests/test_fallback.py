import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add the project root and scripts directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.update_data import main

class TestDataPipelineFallback(unittest.TestCase):

    @patch('scripts.update_data.load_existing_data')
    @patch('scripts.update_data.save_data')
    @patch('scripts.update_data.fetch_vix')
    @patch('scripts.update_data.fetch_fred_series')
    @patch('scripts.update_data.fetch_m2_growth')
    @patch('scripts.update_data.fetch_sp500_breadth')
    @patch('scripts.update_data.fetch_cnn_fear_greed')
    @patch('scripts.update_data.fetch_insider_ratio')
    def test_vix_fallback_duplicates_last_value(
        self,
        mock_fetch_insider,
        mock_fetch_fg,
        mock_fetch_breadth,
        mock_fetch_m2,
        mock_fetch_fred,
        mock_fetch_vix,
        mock_save_data,
        mock_load_data
    ):
        # Setup mock loaded data
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        mock_load_data.return_value = {
            "indicators": {
                "vix": [{"date": yesterday_str, "value": 15.0}],
                "fed_funds": [{"date": yesterday_str, "value": 5.25}],
                "treasury_10y": [{"date": yesterday_str, "value": 4.25}],
                "yield_curve": [{"date": yesterday_str, "value": -0.1}],
                "high_yield_spread": [{"date": yesterday_str, "value": 3.5}],
                "ism_pmi": [{"date": yesterday_str, "value": 51.0}],
                "m2_growth": [{"date": yesterday_str, "value": 1.5}],
                "sp500_breadth": [{"date": yesterday_str, "value": 65.0}],
                "fear_greed": [{"date": yesterday_str, "value": 45.0}],
                "insider_ratio": [{"date": yesterday_str, "value": 0.25}]
            }
        }
        
        # VIX fetch fails, others succeed
        mock_fetch_vix.side_effect = ValueError("VIX API is down")
        mock_fetch_fred.return_value = []
        mock_fetch_m2.return_value = []
        mock_fetch_breadth.return_value = []
        mock_fetch_fg.return_value = {"date": today_str, "value": 50.0}
        mock_fetch_insider.return_value = {"date": today_str, "value": 0.3}

        # Run main script
        main()

        # Check what was saved
        self.assertTrue(mock_save_data.called)
        saved_data = mock_save_data.call_args[0][0]
        
        vix_series = saved_data["indicators"]["vix"]
        # We expect it to have duplicated yesterday's value for today
        self.assertEqual(len(vix_series), 2)
        self.assertEqual(vix_series[0]["date"], yesterday_str)
        self.assertEqual(vix_series[0]["value"], 15.0)
        self.assertEqual(vix_series[1]["date"], today_str)
        self.assertEqual(vix_series[1]["value"], 15.0)

    @patch('scripts.update_data.load_existing_data')
    @patch('scripts.update_data.save_data')
    @patch('scripts.update_data.fetch_vix')
    @patch('scripts.update_data.fetch_fred_series')
    @patch('scripts.update_data.fetch_m2_growth')
    @patch('scripts.update_data.fetch_sp500_breadth')
    @patch('scripts.update_data.fetch_cnn_fear_greed')
    @patch('scripts.update_data.fetch_insider_ratio')
    def test_fallback_no_previous_history(
        self,
        mock_fetch_insider,
        mock_fetch_fg,
        mock_fetch_breadth,
        mock_fetch_m2,
        mock_fetch_fred,
        mock_fetch_vix,
        mock_save_data,
        mock_load_data
    ):
        # Setup: missing/empty history
        mock_load_data.return_value = {}
        
        # All fetches fail
        mock_fetch_vix.side_effect = ValueError("VIX fail")
        mock_fetch_fred.side_effect = ValueError("FRED fail")
        mock_fetch_m2.side_effect = ValueError("M2 fail")
        mock_fetch_breadth.side_effect = ValueError("Breadth fail")
        mock_fetch_fg.side_effect = ValueError("FG fail")
        mock_fetch_insider.side_effect = ValueError("Insider fail")

        # Run main script
        main()

        # Check what was saved
        self.assertTrue(mock_save_data.called)
        saved_data = mock_save_data.call_args[0][0]
        
        # Check that it runs successfully and builds a new structure
        self.assertIn("last_updated", saved_data)
        self.assertIn("indicators", saved_data)
        
        # F&G, Insider, and ISM PMI should have generated mock fallback data
        self.assertTrue(len(saved_data["indicators"]["fear_greed"]) > 0)
        self.assertTrue(len(saved_data["indicators"]["insider_ratio"]) > 0)
        self.assertTrue(len(saved_data["indicators"]["ism_pmi"]) > 0)
        
        # Others with no generators should be empty lists (and shouldn't crash the script)
        self.assertEqual(saved_data["indicators"]["vix"], [])
        self.assertEqual(saved_data["indicators"]["fed_funds"], [])

    @patch('scripts.update_data.load_existing_data')
    @patch('scripts.update_data.save_data')
    @patch('scripts.update_data.fetch_vix')
    @patch('scripts.update_data.fetch_fred_series')
    @patch('scripts.update_data.fetch_m2_growth')
    @patch('scripts.update_data.fetch_sp500_breadth')
    @patch('scripts.update_data.fetch_cnn_fear_greed')
    @patch('scripts.update_data.fetch_insider_ratio')
    def test_initialization_creates_new_file(
        self,
        mock_fetch_insider,
        mock_fetch_fg,
        mock_fetch_breadth,
        mock_fetch_m2,
        mock_fetch_fred,
        mock_fetch_vix,
        mock_save_data,
        mock_load_data
    ):
        # Setup: missing/empty history
        mock_load_data.return_value = {}
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # All fetches succeed
        mock_fetch_vix.return_value = [{"date": today_str, "value": 14.5}]
        mock_fetch_fred.return_value = [{"date": today_str, "value": 4.5}]
        mock_fetch_m2.return_value = [{"date": today_str, "value": 2.0}]
        mock_fetch_breadth.return_value = [{"date": today_str, "value": 70.0}]
        mock_fetch_fg.return_value = {"date": today_str, "value": 55.0}
        mock_fetch_insider.return_value = {"date": today_str, "value": 0.35}

        # Run main script
        main()

        # Check what was saved
        self.assertTrue(mock_save_data.called)
        saved_data = mock_save_data.call_args[0][0]
        
        # Check components are populated
        self.assertEqual(saved_data["indicators"]["vix"], [{"date": today_str, "value": 14.5}])
        self.assertEqual(saved_data["indicators"]["fed_funds"], [{"date": today_str, "value": 4.5}])
        self.assertEqual(saved_data["indicators"]["yield_curve"], [{"date": today_str, "value": 4.5}])
        self.assertEqual(saved_data["indicators"]["m2_growth"], [{"date": today_str, "value": 2.0}])
        self.assertEqual(saved_data["indicators"]["sp500_breadth"], [{"date": today_str, "value": 70.0}])
        # F&G / Insider should contain history + today's value
        self.assertEqual(saved_data["indicators"]["fear_greed"][-1], {"date": today_str, "value": 55.0})
        self.assertEqual(saved_data["indicators"]["insider_ratio"][-1], {"date": today_str, "value": 0.35})

if __name__ == '__main__':
    unittest.main()
