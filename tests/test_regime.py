import unittest
import sys
import os
from datetime import datetime, timedelta

# Add the project root and scripts directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.pipeline.regime import (
    normalize_vix,
    normalize_yield_curve,
    normalize_high_yield_spread,
    normalize_sp500_breadth,
    normalize_m2_growth,
    calculate_market_regime_index
)

class TestMarketRegimeIndex(unittest.TestCase):

    def test_normalize_vix(self):
        # VIX <= 12 should be 100
        self.assertEqual(normalize_vix(10.0), 100.0)
        self.assertEqual(normalize_vix(12.0), 100.0)
        # VIX >= 35 should be 0
        self.assertEqual(normalize_vix(35.0), 0.0)
        self.assertEqual(normalize_vix(40.0), 0.0)
        # VIX in between should scale linearly
        # Halfway between 12 and 35 is 23.5 -> score should be 50.0
        self.assertAlmostEqual(normalize_vix(23.5), 50.0, places=4)

    def test_normalize_yield_curve(self):
        # Yield spread <= -0.5 should be 0
        self.assertEqual(normalize_yield_curve(-1.0), 0.0)
        self.assertEqual(normalize_yield_curve(-0.5), 0.0)
        # Yield spread >= 1.5 should be 100
        self.assertEqual(normalize_yield_curve(1.5), 100.0)
        self.assertEqual(normalize_yield_curve(2.0), 100.0)
        # Yield spread in between should scale linearly
        # Halfway between -0.5 and 1.5 is 0.5 -> score should be 50.0
        self.assertAlmostEqual(normalize_yield_curve(0.5), 50.0, places=4)

    def test_normalize_high_yield_spread(self):
        # HY spread <= 3.0 should be 100
        self.assertEqual(normalize_high_yield_spread(2.5), 100.0)
        self.assertEqual(normalize_high_yield_spread(3.0), 100.0)
        # HY spread >= 8.5 should be 0
        self.assertEqual(normalize_high_yield_spread(8.5), 0.0)
        self.assertEqual(normalize_high_yield_spread(10.0), 0.0)
        # HY spread in between should scale linearly
        # Halfway between 3.0 and 8.5 is 5.75 -> score should be 50.0
        self.assertAlmostEqual(normalize_high_yield_spread(5.75), 50.0, places=4)

    def test_normalize_sp500_breadth(self):
        # S&P 500 breadth should scale 0-100 directly
        self.assertEqual(normalize_sp500_breadth(0.0), 0.0)
        self.assertEqual(normalize_sp500_breadth(100.0), 100.0)
        self.assertEqual(normalize_sp500_breadth(50.0), 50.0)
        # Clamped
        self.assertEqual(normalize_sp500_breadth(-5.0), 0.0)
        self.assertEqual(normalize_sp500_breadth(105.0), 100.0)

    def test_normalize_m2_growth(self):
        # M2 growth <= 0.0 should be 0
        self.assertEqual(normalize_m2_growth(-1.0), 0.0)
        self.assertEqual(normalize_m2_growth(0.0), 0.0)
        # M2 growth >= 8.0 should be 100
        self.assertEqual(normalize_m2_growth(8.0), 100.0)
        self.assertEqual(normalize_m2_growth(10.0), 100.0)
        # M2 growth in between should scale linearly
        # Halfway between 0.0 and 8.0 is 4.0 -> score should be 50.0
        self.assertAlmostEqual(normalize_m2_growth(4.0), 50.0, places=4)

    def test_calculate_market_regime_index(self):
        # Test calculations with aligned sample dates
        indicators = {
            "vix": [{"date": "2026-06-25", "value": 12.0}, {"date": "2026-06-26", "value": 23.5}],
            "yield_curve": [{"date": "2026-06-25", "value": 1.5}, {"date": "2026-06-26", "value": 0.5}],
            "high_yield_spread": [{"date": "2026-06-25", "value": 3.0}, {"date": "2026-06-26", "value": 5.75}],
            "sp500_breadth": [{"date": "2026-06-25", "value": 100.0}, {"date": "2026-06-26", "value": 50.0}],
            "m2_growth": [{"date": "2026-06-25", "value": 8.0}, {"date": "2026-06-26", "value": 4.0}]
        }
        
        # Expected scores:
        # For 2026-06-25: all normalized scores should be 100.0 -> composite = 100.0
        # For 2026-06-26: all normalized scores should be 50.0 -> composite = 50.0
        timeline = calculate_market_regime_index(indicators)
        
        self.assertEqual(len(timeline), 2)
        
        self.assertEqual(timeline[0]["date"], "2026-06-25")
        self.assertAlmostEqual(timeline[0]["value"], 100.0, places=2)
        
        self.assertEqual(timeline[1]["date"], "2026-06-26")
        self.assertAlmostEqual(timeline[1]["value"], 50.0, places=2)

if __name__ == '__main__':
    unittest.main()
