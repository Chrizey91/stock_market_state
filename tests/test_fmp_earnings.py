import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the project root and scripts directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.update_data import (
    fetch_sp500_earnings_fmp,
    compute_yoy_growth,
    _quarter_key,
    _quarter_date_label,
)


class TestFMPEarnings(unittest.TestCase):

    @patch.dict(os.environ, {}, clear=True)
    def test_fetch_sp500_earnings_fmp_no_key(self):
        """Verify it skips gracefully when FMP_API_KEY is absent."""
        eps, rev = fetch_sp500_earnings_fmp()
        self.assertEqual(eps, [])
        self.assertEqual(rev, [])

    @patch.dict(os.environ, {"FMP_API_KEY": "dummy_key"})
    @patch("requests.get")
    def test_fetch_sp500_earnings_fmp_403(self, mock_get):
        """Verify it handles 403 Forbidden gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        eps, rev = fetch_sp500_earnings_fmp()
        self.assertEqual(eps, [])
        self.assertEqual(rev, [])

    @patch.dict(os.environ, {"FMP_API_KEY": "dummy_key"})
    @patch("requests.get")
    def test_fetch_sp500_earnings_fmp_402(self, mock_get):
        """Verify it handles 402 Payment Required gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_get.return_value = mock_response

        eps, rev = fetch_sp500_earnings_fmp()
        self.assertEqual(eps, [])
        self.assertEqual(rev, [])

    def test_compute_yoy_growth(self):
        """Test YoY growth calculation on quarterly data."""
        data = [
            {"date": "2022-03-31", "revenue": 1000.0, "eps": 2.0},
            {"date": "2022-06-30", "revenue": 1100.0, "eps": 2.2},
            {"date": "2022-09-30", "revenue": 1200.0, "eps": 2.4},
            {"date": "2022-12-31", "revenue": 1300.0, "eps": 2.6},
            {"date": "2023-03-31", "revenue": 1100.0, "eps": 2.2},  # YoY: +10%
            {"date": "2023-06-30", "revenue": 1210.0, "eps": 2.42}, # YoY: +10%
        ]

        eps_growth = compute_yoy_growth(data, "eps")
        rev_growth = compute_yoy_growth(data, "revenue")

        self.assertEqual(len(eps_growth), 2)
        self.assertEqual(eps_growth[0], {"date": "2023-03-31", "value": 10.0})
        self.assertEqual(eps_growth[1], {"date": "2023-06-30", "value": 10.0})

        self.assertEqual(len(rev_growth), 2)
        self.assertEqual(rev_growth[0], {"date": "2023-03-31", "value": 10.0})
        self.assertEqual(rev_growth[1], {"date": "2023-06-30", "value": 10.0})

    def test_quarter_key(self):
        from datetime import datetime
        self.assertEqual(_quarter_key(datetime(2025, 1, 15)), (2025, 1))
        self.assertEqual(_quarter_key(datetime(2025, 3, 31)), (2025, 1))
        self.assertEqual(_quarter_key(datetime(2025, 4, 1)), (2025, 2))
        self.assertEqual(_quarter_key(datetime(2025, 6, 30)), (2025, 2))
        self.assertEqual(_quarter_key(datetime(2025, 7, 1)), (2025, 3))
        self.assertEqual(_quarter_key(datetime(2025, 12, 31)), (2025, 4))

    def test_quarter_date_label(self):
        self.assertEqual(_quarter_date_label(2025, 1), "2025-03-31")
        self.assertEqual(_quarter_date_label(2025, 2), "2025-06-30")
        self.assertEqual(_quarter_date_label(2025, 3), "2025-09-30")
        self.assertEqual(_quarter_date_label(2025, 4), "2025-12-31")
        self.assertEqual(_quarter_date_label(2024, 1), "2024-03-31")

    @patch.dict(os.environ, {"FMP_API_KEY": "dummy_key"})
    @patch("requests.get")
    def test_fetch_sp500_earnings_fmp_success(self, mock_get):
        """Test successful income-statement fetch with aggregation and YoY growth.

        Mocks the /stable/income-statement endpoint. Each ticker call returns
        quarterly income statement records. We check aggregation by quarter
        and YoY growth computation.
        """
        # Build mock data per ticker.
        # AAPL: Q1 2025 EPS=2.0, Rev=100B; Q1 2026 EPS=3.0, Rev=150B
        # MSFT: Q1 2025 EPS=3.0, Rev=200B; Q1 2026 EPS=4.0, Rev=260B
        aapl_data = [
            {"date": "2026-01-30", "symbol": "AAPL", "epsDiluted": 3.0, "revenue": 150000000000,
             "period": "Q1", "fiscalYear": "2026", "eps": 3.0},
            {"date": "2025-01-30", "symbol": "AAPL", "epsDiluted": 2.0, "revenue": 100000000000,
             "period": "Q1", "fiscalYear": "2025", "eps": 2.0},
        ]
        msft_data = [
            {"date": "2026-01-23", "symbol": "MSFT", "epsDiluted": 4.0, "revenue": 260000000000,
             "period": "Q1", "fiscalYear": "2026", "eps": 4.0},
            {"date": "2025-01-23", "symbol": "MSFT", "epsDiluted": 3.0, "revenue": 200000000000,
             "period": "Q1", "fiscalYear": "2025", "eps": 3.0},
        ]
        # All other tickers return empty
        empty_data = []

        def side_effect(url, timeout=15):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            if "symbol=AAPL" in url:
                mock_resp.json.return_value = aapl_data
            elif "symbol=MSFT" in url:
                mock_resp.json.return_value = msft_data
            else:
                mock_resp.json.return_value = empty_data
            return mock_resp

        mock_get.side_effect = side_effect

        eps_growth, rev_growth = fetch_sp500_earnings_fmp()

        # Q1 2025: AAPL EPS=2.0, MSFT EPS=3.0 → aggregate=5.0
        # Q1 2026: AAPL EPS=3.0, MSFT EPS=4.0 → aggregate=7.0
        # YoY EPS growth = (7.0 - 5.0) / 5.0 * 100 = 40.0%
        self.assertTrue(len(eps_growth) >= 1, f"Expected at least 1 EPS growth point, got {len(eps_growth)}")
        q1_2026_eps = [p for p in eps_growth if "2026" in p["date"]]
        self.assertTrue(len(q1_2026_eps) >= 1, f"Expected Q1 2026 EPS growth, got {q1_2026_eps}")
        self.assertAlmostEqual(q1_2026_eps[0]["value"], 40.0, places=1)

        # Q1 2025: Rev=300B, Q1 2026: Rev=410B → YoY = 36.67%
        self.assertTrue(len(rev_growth) >= 1, f"Expected at least 1 revenue growth point, got {len(rev_growth)}")
        q1_2026_rev = [p for p in rev_growth if "2026" in p["date"]]
        self.assertTrue(len(q1_2026_rev) >= 1, f"Expected Q1 2026 revenue growth, got {q1_2026_rev}")
        self.assertAlmostEqual(q1_2026_rev[0]["value"], 36.67, places=1)

    @patch.dict(os.environ, {"FMP_API_KEY": "dummy_key"})
    @patch("requests.get")
    def test_fetch_sp500_earnings_fmp_empty_data(self, mock_get):
        """Test that empty API responses return empty arrays."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        eps, rev = fetch_sp500_earnings_fmp()
        self.assertEqual(eps, [])
        self.assertEqual(rev, [])


if __name__ == '__main__':
    unittest.main()
