import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the project root and scripts directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.pipeline.adapters.fmp import fetch_sp500_pe_fmp, fetch_cape_ratio_nasdaq

class TestValuationPeCape(unittest.TestCase):

    def test_fetch_cape_ratio_nasdaq_no_key(self):
        """Verify it skips gracefully when NASDAQ_DATA_LINK_API_KEY is absent."""
        cape = fetch_cape_ratio_nasdaq(api_key=None)
        self.assertEqual(cape, [])

    @patch("scripts.pipeline.adapters.fmp.requests.get")
    def test_fetch_cape_ratio_nasdaq_403(self, mock_get):
        """Verify it handles 403 Forbidden gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        cape = fetch_cape_ratio_nasdaq(api_key="dummy_key")
        self.assertEqual(cape, [])

    @patch("scripts.pipeline.adapters.fmp.requests.get")
    def test_fetch_cape_ratio_nasdaq_success(self, mock_get):
        """Test successful CAPE ratio fetch and filtering."""
        # Setup mock data (newest first, as the API usually returns)
        mock_data = {
            "dataset": {
                "data": [
                    ["2026-06-30", 33.1],
                    ["2022-06-30", 31.0],
                    ["2018-06-30", 30.5], # older than 5 years, should be filtered
                    ["invalid_row"],      # should be skipped safely
                ]
            }
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        cape = fetch_cape_ratio_nasdaq(api_key="dummy_key")
        
        # Expect 2026 and 2022 to be present, but 2018 filtered out
        self.assertEqual(len(cape), 2)
        # Should be sorted chronologically
        self.assertEqual(cape[0], {"date": "2022-06-30", "value": 31.0})
        self.assertEqual(cape[1], {"date": "2026-06-30", "value": 33.1})

    def test_fetch_sp500_pe_fmp_no_key(self):
        """Verify it skips gracefully when FMP_API_KEY is absent."""
        pe = fetch_sp500_pe_fmp(api_key=None)
        self.assertEqual(pe, [])

    @patch("scripts.pipeline.adapters.fmp.requests.get")
    def test_fetch_sp500_pe_fmp_403(self, mock_get):
        """Verify it handles 403 Forbidden gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        pe = fetch_sp500_pe_fmp(api_key="dummy_key")
        self.assertEqual(pe, [])

    @patch("scripts.pipeline.adapters.fmp.requests.get")
    def test_fetch_sp500_pe_fmp_success(self, mock_get):
        """Test successful FMP Forward P/E fetch and parsing (various keys)."""
        mock_data = [
            {"date": "2026-06-30", "pe": 21.3},
            {"date": "2025-06-30", "peRatio": 18.5},
            {"date": "2024-06-30", "value": 16.2},
            {"date": "2018-06-30", "priceToEarnings": 15.0}  # Should be filtered out (> 5 years ago)
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        pe = fetch_sp500_pe_fmp(api_key="dummy_key")
        
        # Expect 3 points (2026, 2025, 2024)
        self.assertEqual(len(pe), 3)
        # Should be sorted chronologically
        self.assertEqual(pe[0], {"date": "2024-06-30", "value": 16.2})
        self.assertEqual(pe[1], {"date": "2025-06-30", "value": 18.5})
        self.assertEqual(pe[2], {"date": "2026-06-30", "value": 21.3})

if __name__ == '__main__':
    unittest.main()
