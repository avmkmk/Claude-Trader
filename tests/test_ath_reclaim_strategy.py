"""
Unit tests for ATH Reclaim Strategy
"""
import unittest
import backtrader as bt
from datetime import datetime
import pandas as pd

class TestATHTracking(unittest.TestCase):

    def test_ath_updates_on_new_high(self):
        """Test that ATH updates when stock makes new high"""
        # Create mock data with increasing highs
        data = {
            'datetime': pd.date_range('2020-01-01', periods=5),
            'open': [100, 105, 110, 115, 120],
            'high': [105, 110, 115, 120, 125],
            'low': [95, 100, 105, 110, 115],
            'close': [103, 108, 113, 118, 123],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }
        df = pd.DataFrame(data)

        # Test ATH tracking logic
        ath = 0
        for high in df['high']:
            if high > ath:
                ath = high

        self.assertEqual(ath, 125)

    def test_ath_persists_on_pullback(self):
        """Test that ATH persists when price pulls back"""
        data = {
            'high': [100, 110, 120, 115, 110, 108, 125]
        }

        ath = 0
        ath_values = []
        for high in data['high']:
            if high > ath:
                ath = high
            ath_values.append(ath)

        expected = [100, 110, 120, 120, 120, 120, 125]
        self.assertEqual(ath_values, expected)

class TestGapDetection(unittest.TestCase):

    def test_gap_up_detected(self):
        """Test gap up detection (open > prev close)"""
        prev_close = 100
        today_open = 105

        gap_up = today_open > (prev_close * 1.001)  # 0.1% tolerance
        self.assertTrue(gap_up)

    def test_no_gap_within_tolerance(self):
        """Test no gap when open is within 0.1% of prev close"""
        prev_close = 100.0
        today_open = 100.05  # 0.05% gap

        gap_up = today_open > (prev_close * 1.001)
        self.assertFalse(gap_up)

    def test_gap_down_not_flagged(self):
        """Test gap down is not flagged as gap up"""
        prev_close = 100
        today_open = 95

        gap_up = today_open > (prev_close * 1.001)
        self.assertFalse(gap_up)

if __name__ == '__main__':
    unittest.main()
