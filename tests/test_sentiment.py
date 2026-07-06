import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add the project root and scripts directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.pipeline.adapters.sentiment import fetch_cnn_fear_greed, fetch_insider_ratio
from scripts.pipeline.fallback import generate_mock_fear_greed, generate_mock_insider_ratio

class TestSentimentIndicators(unittest.TestCase):

    @patch('scripts.pipeline.adapters.sentiment.requests.get')
    def test_fetch_cnn_fear_greed_success(self, mock_get):
        # Mock successful CNN JSON response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "score": 45.5,
            "rating": "neutral",
            "timestamp": "2026-06-29T19:00:00+00:00"
        }
        mock_get.return_value = mock_response

        res = fetch_cnn_fear_greed()
        self.assertEqual(res["date"], "2026-06-29")
        self.assertEqual(res["value"], 45.5)

    @patch('scripts.pipeline.adapters.sentiment.requests.get')
    def test_fetch_insider_ratio_success(self, mock_get):
        # Mock successful OpenInsider HTML response
        mock_html = """
        <html>
            <body>
                <table class="tinytable">
                    <thead>
                        <tr>
                            <th></th>
                            <th>Filing Date</th>
                            <th>Trade Date</th>
                            <th>Ticker</th>
                            <th>Company Name</th>
                            <th>Insider Name</th>
                            <th>Title</th>
                            <th>Trade Type</th>
                            <th>Price</th>
                            <th>Qty</th>
                            <th>Owned</th>
                            <th>ΔOwn</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td></td>
                            <td>2026-06-29 14:58:45</td>
                            <td>2026-06-25</td>
                            <td>TEST</td>
                            <td>Test Inc</td>
                            <td>John Doe</td>
                            <td>CEO</td>
                            <td>P - Purchase</td>
                            <td>$10.00</td>
                            <td>+1,000</td>
                            <td>10,000</td>
                            <td>+10%</td>
                            <td>+$10,000</td>
                        </tr>
                        <tr>
                            <td></td>
                            <td>2026-06-29 14:50:00</td>
                            <td>2026-06-25</td>
                            <td>TEST</td>
                            <td>Test Inc</td>
                            <td>Jane Smith</td>
                            <td>CFO</td>
                            <td>S - Sale</td>
                            <td>$10.00</td>
                            <td>-2,000</td>
                            <td>8,000</td>
                            <td>-20%</td>
                            <td>-$20,000</td>
                        </tr>
                        <tr>
                            <td></td>
                            <td>2026-06-29 14:40:00</td>
                            <td>2026-06-25</td>
                            <td>TEST</td>
                            <td>Test Inc</td>
                            <td>Bob Johnson</td>
                            <td>VP</td>
                            <td>S - Sale</td>
                            <td>$10.00</td>
                            <td>-5,000</td>
                            <td>5,000</td>
                            <td>-50%</td>
                            <td>-$50,000</td>
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

        # Buys = 1, Sells = 2 -> Ratio = 0.5
        res = fetch_insider_ratio()
        self.assertEqual(res["date"], datetime.now().strftime('%Y-%m-%d'))
        self.assertEqual(res["value"], 0.5)

    def test_generate_mock_fear_greed(self):
        data = generate_mock_fear_greed(10)
        self.assertEqual(len(data), 10)
        for point in data:
            self.assertIn("date", point)
            self.assertIn("value", point)
            self.assertTrue(10.0 <= point["value"] <= 90.0)

    def test_generate_mock_insider_ratio(self):
        data = generate_mock_insider_ratio(10)
        self.assertEqual(len(data), 10)
        for point in data:
            self.assertIn("date", point)
            self.assertIn("value", point)
            self.assertTrue(0.0 <= point["value"] <= 2.0)

if __name__ == '__main__':
    unittest.main()
