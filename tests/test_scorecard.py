import unittest
import sys
import os

# Add the project root and scripts directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.update_data import evaluate_scorecard

class TestScorecard(unittest.TestCase):

    def test_evaluate_scorecard_healthy(self):
        # Setup indicators where everything is healthy
        indicators = {
            "sp500_trend": [{"date": "2026-06-29", "value": 5200.0, "ma50": 5100.0, "ma200": 5000.0}],
            "sp500_breadth": [{"date": "2026-06-29", "value": 75.0}],
            "vix": [{"date": "2026-06-29", "value": 15.0}],
            "high_yield_spread": [{"date": "2026-06-29", "value": 3.5}],
            "m2_growth": [{"date": "2026-06-29", "value": 2.0}]
        }
        
        scorecard, health_score, health_total = evaluate_scorecard(indicators)
        
        # We expect:
        # sp500_trend: healthy (5200 > 5000)
        # sp500_momentum: healthy (5100 > 5000)
        # sp500_breadth: healthy (75 > 70)
        # vix: healthy (15 <= 20)
        # hy_spread: healthy (3.5 < 5.0)
        # m2_growth: healthy (2.0 >= 0.0)
        # Total healthy = 6
        # Total available = 6 (others are unavailable)
        self.assertEqual(health_score, 6)
        self.assertEqual(health_total, 6)
        
        # Verify status details
        for item in scorecard:
            if item["id"] in ["sp500_trend", "sp500_momentum", "sp500_breadth", "vix", "hy_spread", "m2_growth"]:
                self.assertEqual(item["status"], "healthy")
            else:
                self.assertEqual(item["status"], "unavailable")
                self.assertIsNone(item["value"])

    def test_evaluate_scorecard_unhealthy(self):
        # Setup indicators where everything is unhealthy
        indicators = {
            "sp500_trend": [{"date": "2026-06-29", "value": 4900.0, "ma50": 4800.0, "ma200": 5000.0}],
            "sp500_breadth": [{"date": "2026-06-29", "value": 65.0}],
            "vix": [{"date": "2026-06-29", "value": 25.0}],
            "high_yield_spread": [{"date": "2026-06-29", "value": 5.5}],
            "m2_growth": [{"date": "2026-06-29", "value": -1.0}]
        }
        
        scorecard, health_score, health_total = evaluate_scorecard(indicators)
        
        # We expect:
        # sp500_trend: unhealthy (4900 <= 5000)
        # sp500_momentum: unhealthy (4800 <= 5000)
        # sp500_breadth: unhealthy (65 <= 70)
        # vix: unhealthy (25 > 20)
        # hy_spread: unhealthy (5.5 >= 5.0)
        # m2_growth: unhealthy (-1.0 < 0.0)
        # Total healthy = 0
        # Total available = 6
        self.assertEqual(health_score, 0)
        self.assertEqual(health_total, 6)
        
        # Verify status details
        for item in scorecard:
            if item["id"] in ["sp500_trend", "sp500_momentum", "sp500_breadth", "vix", "hy_spread", "m2_growth"]:
                self.assertEqual(item["status"], "unhealthy")

    def test_evaluate_scorecard_mixed_and_missing(self):
        # Setup indicators with mixed healthy/unhealthy and some missing
        indicators = {
            "sp500_trend": [{"date": "2026-06-29", "value": 5200.0, "ma50": 4900.0, "ma200": 5000.0}], # trend: healthy, momentum: unhealthy
            # sp500_breadth: missing
            "vix": [{"date": "2026-06-29", "value": 22.0}], # unhealthy
            "high_yield_spread": [{"date": "2026-06-29", "value": 3.5}] # healthy
            # m2_growth: missing
        }
        
        scorecard, health_score, health_total = evaluate_scorecard(indicators)
        
        # Available:
        # sp500_trend (healthy)
        # sp500_momentum (unhealthy)
        # vix (unhealthy)
        # hy_spread (healthy)
        # Total healthy = 2 (trend, hy_spread)
        # Total available = 4
        self.assertEqual(health_score, 2)
        self.assertEqual(health_total, 4)

if __name__ == '__main__':
    unittest.main()
