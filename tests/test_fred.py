import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd
import os
import sys

# Add the project root and scripts directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.pipeline.adapters.fred import fetch_fred_series, fetch_m2_growth

class TestFredApiAndFallback(unittest.TestCase):

    def setUp(self):
        # Save original env
        self.original_env = os.environ.copy()
        if "FRED_API_KEY" in os.environ:
            del os.environ["FRED_API_KEY"]

    def tearDown(self):
        # Restore env
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch('scripts.pipeline.adapters.fred.pd.read_csv')
    def test_fetch_fred_series_key_absent_uses_csv(self, mock_read_csv):
        # Mock CSV response from FRED
        mock_df = pd.DataFrame({
            'observation_date': ['2026-06-01', '2026-06-02', '2026-06-03'],
            'FEDFUNDS': ['5.25', '5.30', '.']
        })
        mock_read_csv.return_value = mock_df

        res = fetch_fred_series('FEDFUNDS', api_key=None, years=5)
        
        # Verify CSV path was used (read_csv called)
        mock_read_csv.assert_called_once_with('https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS')
        
        # Check structure
        self.assertEqual(len(res), 2)  # Dot was coerced and dropped
        self.assertEqual(res[0]['date'], '2026-06-01')
        self.assertEqual(res[0]['value'], 5.25)
        self.assertEqual(res[1]['date'], '2026-06-02')
        self.assertEqual(res[1]['value'], 5.30)

    @patch('scripts.pipeline.adapters.fred.requests.get')
    def test_fetch_fred_series_key_present_uses_api(self, mock_get):
        os.environ["FRED_API_KEY"] = "fake_key"
        
    @patch('scripts.pipeline.adapters.fred.requests.get')
    def test_fetch_fred_series_api_success(self, mock_get):
        # Set dummy API key
        api_key = "fake_key"
        
        # Mock API JSON response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "observations": [
                {"date": "2026-06-01", "value": "5.25"},
                {"date": "2026-06-02", "value": "5.30"},
                {"date": "2026-06-03", "value": "."}
            ]
        }
        mock_get.return_value = mock_response

        # We also need to patch read_csv to make sure it's NOT called
        with patch('scripts.pipeline.adapters.fred.pd.read_csv') as mock_read_csv:
            res = fetch_fred_series('FEDFUNDS', api_key="fake_key", years=5)
            mock_read_csv.assert_not_called()
            mock_get.assert_called_once()
            
            # Verify URL used
            called_url = mock_get.call_args[0][0]
            self.assertIn("series_id=FEDFUNDS", called_url)
            self.assertIn("api_key=fake_key", called_url)
            self.assertIn("file_type=json", called_url)
            
            # Check structure
            self.assertEqual(len(res), 2)
            self.assertEqual(res[0]['date'], '2026-06-01')
            self.assertEqual(res[0]['value'], 5.25)
            self.assertEqual(res[1]['date'], '2026-06-02')
            self.assertEqual(res[1]['value'], 5.30)

    @patch('scripts.pipeline.adapters.fred.requests.get')
    @patch('scripts.pipeline.adapters.fred.pd.read_csv')
    def test_fetch_fred_series_api_fails_falls_back_to_csv(self, mock_read_csv, mock_get):
        # Mock API returns error
        mock_get.side_effect = Exception("API rate limit exceeded")
        
        # Mock CSV fallback success
        mock_df = pd.DataFrame({
            'observation_date': ['2026-06-01', '2026-06-02'],
            'FEDFUNDS': ['5.25', '5.30']
        })
        mock_read_csv.return_value = mock_df

        res = fetch_fred_series('FEDFUNDS', api_key="fake_key", years=5)
        
        mock_get.assert_called_once()
        mock_read_csv.assert_called_once()
        
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]['date'], '2026-06-01')
        self.assertEqual(res[0]['value'], 5.25)

    @patch('scripts.pipeline.adapters.fred.requests.get')
    @patch('scripts.pipeline.adapters.fred.pd.read_csv')
    def test_fetch_m2_growth_identical_structure(self, mock_read_csv, mock_get):
        # We want to verify both paths yield identical results for fetch_m2_growth
        
        # 1. API path setup
        mock_response = MagicMock()
        mock_response.status_code = 200
        # M2 growth needs at least 13 months to compute YoY pct change
        observations = []
        for i in range(24):
            date_str = (datetime(2024, 1, 1) + timedelta(days=i*30)).strftime('%Y-%m-%d')
            observations.append({"date": date_str, "value": str(20000 + i*100)})
        mock_response.json.return_value = {"observations": observations}
        mock_get.return_value = mock_response
        
        res_api = fetch_m2_growth(api_key="fake_key", years=5)
        
        # 2. CSV fallback path setup
        csv_rows = []
        for i in range(24):
            date_str = (datetime(2024, 1, 1) + timedelta(days=i*30)).strftime('%Y-%m-%d')
            csv_rows.append({'observation_date': date_str, 'M2SL': 20000 + i*100})
        mock_df = pd.DataFrame(csv_rows)
        mock_read_csv.return_value = mock_df
        
        res_csv = fetch_m2_growth(api_key=None, years=5)
        
        # Both results should be identical
        self.assertEqual(res_api, res_csv)
        self.assertTrue(len(res_api) > 0)

    def test_build_fred_fetchers(self):
        from scripts.pipeline.adapters.fred import build_fred_fetchers
        config = MagicMock()
        config.fred_api_key = "dummy_key"
        fetchers = build_fred_fetchers(config)
        keys = [f["key"] for f in fetchers]
        self.assertIn("ig_spread", keys)
        self.assertIn("fed_balance_sheet", keys)
        self.assertIn("bank_lending", keys)

if __name__ == '__main__':
    unittest.main()
