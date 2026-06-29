import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import sys
import os

# Add the project root and scripts directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.update_data import get_sp500_tickers, chunk_tickers, calculate_breadth, calculate_ad_line, calculate_new_highs_lows

class TestMarketBreadth(unittest.TestCase):
    
    @patch('scripts.update_data.requests.get')
    def test_get_sp500_tickers(self, mock_get):
        # Mock HTML response for Wikipedia S&P 500 companies list
        mock_html = """
        <html>
            <body>
                <table class="wikitable sortable" id="constituents">
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Security</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><a href="/wiki/3M">MMM</a></td>
                            <td>3M</td>
                        </tr>
                        <tr>
                            <td><a href="/wiki/Apple_Inc.">AAPL</a></td>
                            <td>Apple Inc.</td>
                        </tr>
                        <tr>
                            <td><a href="/wiki/Berkshire_Hathaway">BRK.B</a></td>
                            <td>Berkshire Hathaway</td>
                        </tr>
                    </tbody>
                </table>
            </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response
        
        tickers = get_sp500_tickers()
        self.assertEqual(tickers, ["AAPL", "BRK-B", "MMM"])
        
    def test_chunk_tickers(self):
        tickers = [f"T{i}" for i in range(10)]
        chunks = chunk_tickers(tickers, 3)
        self.assertEqual(len(chunks), 4)
        self.assertEqual(chunks[0], ["T0", "T1", "T2"])
        self.assertEqual(chunks[1], ["T3", "T4", "T5"])
        self.assertEqual(chunks[2], ["T6", "T7", "T8"])
        self.assertEqual(chunks[3], ["T9"])

    def test_calculate_breadth(self):
        # Create a mock DataFrame of prices
        # We need a 200-day simple moving average.
        # Let's create 250 days of data for 2 assets:
        # Asset A: price always above 200-day SMA (e.g. steadily rising)
        # Asset B: price always below 200-day SMA (e.g. steadily falling)
        dates = pd.date_range(start="2025-01-01", periods=250, freq='B')
        
        # Asset A: Close rises from 100 to 350 (always > 200 SMA once SMA is calculated)
        close_a = np.linspace(100, 350, 250)
        # Asset B: Close falls from 350 to 100 (always < 200 SMA once SMA is calculated)
        close_b = np.linspace(350, 100, 250)
        
        df_close = pd.DataFrame({
            "A": close_a,
            "B": close_b
        }, index=dates)
        
        breadth = calculate_breadth(df_close)
        
        # Verify we only return data where the 200-day SMA is valid
        # There should be 250 - 199 = 51 data points
        self.assertEqual(len(breadth), 51)
        
        # Check calculation for the last day:
        # For Asset A: latest price is 350, SMA is mean of last 200 elements of close_a, which is around 250. 350 > 250 (Above)
        # For Asset B: latest price is 100, SMA is mean of last 200 elements of close_b, which is around 250. 100 < 250 (Below)
        # So exactly 1 out of 2 stocks is above. Breadth = 50%
        self.assertEqual(breadth[-1]['value'], 50.0)
        self.assertEqual(breadth[-1]['date'], dates[-1].strftime('%Y-%m-%d'))

    def test_calculate_ad_line(self):
        # Setup short df with 5 business days
        # We want to test the cumulative calculation:
        # Day 0: [100, 200] -> CumSum = 0 (first row is NaN for diff)
        # Day 1: [101, 201] -> Both rise (+1, +1). Adv=2, Dec=0. daily=2. CumSum = 2
        # Day 2: [102, 202] -> Both rise (+1, +1). Adv=2, Dec=0. daily=2. CumSum = 4
        # Day 3: [101, 201] -> Both fall (-1, -1). Adv=0, Dec=2. daily=-2. CumSum = 2
        # Day 4: [103, 200] -> A rises (+2), B falls (-1). Adv=1, Dec=1. daily=0. CumSum = 2
        dates = pd.date_range(end=pd.Timestamp.now(), periods=5, freq='B')
        
        df_close = pd.DataFrame({
            "A": [100.0, 101.0, 102.0, 101.0, 103.0],
            "B": [200.0, 201.0, 202.0, 201.0, 200.0]
        }, index=dates)
        
        ad_line = calculate_ad_line(df_close)
        
        self.assertEqual(len(ad_line), 5)
        self.assertEqual(ad_line[0]["value"], 0)
        self.assertEqual(ad_line[1]["value"], 2)
        self.assertEqual(ad_line[2]["value"], 4)
        self.assertEqual(ad_line[3]["value"], 2)
        self.assertEqual(ad_line[4]["value"], 2)
        
        self.assertEqual(ad_line[4]["date"], dates[-1].strftime('%Y-%m-%d'))

    def test_calculate_new_highs_lows(self):
        # 52-week High/Low requires 252 trading days.
        # Let's create 300 business days.
        # Asset A: price rises steadily from 100 to 400.
        # Asset B: price falls steadily from 400 to 100.
        # On the last day, Asset A will make a 52-week High (close is 400, max of window is 400).
        # Asset B will make a 52-week Low (close is 100, min of window is 100).
        dates = pd.date_range(end=pd.Timestamp.now(), periods=300, freq='B')
        
        close_a = np.linspace(100, 400, 300)
        close_b = np.linspace(400, 100, 300)
        
        df_close = pd.DataFrame({
            "A": close_a,
            "B": close_b
        }, index=dates)
        
        new_highs_lows = calculate_new_highs_lows(df_close)
        
        # Valid window is from day 252 (252nd element is at index 251).
        # There should be 300 - 251 = 49 valid data points.
        # But filtering keeps the last 365 calendar days, which is approx 261 business days.
        self.assertEqual(len(new_highs_lows), 261)
        
        # On the last day: Highs should be 1 (Asset A), Lows should be 1 (Asset B).
        latest = new_highs_lows[-1]
        self.assertEqual(latest["highs"], 1)
        self.assertEqual(latest["lows"], 1)
        self.assertEqual(latest["date"], dates[-1].strftime('%Y-%m-%d'))

if __name__ == '__main__':
    unittest.main()
