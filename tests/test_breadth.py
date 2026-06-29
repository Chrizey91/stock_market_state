import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import sys
import os

# Add the project root and scripts directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.update_data import get_sp500_tickers, chunk_tickers, calculate_breadth

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

if __name__ == '__main__':
    unittest.main()
