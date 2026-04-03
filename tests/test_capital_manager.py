"""
Unit tests for CapitalManager
"""
import unittest
from datetime import date
from backtesting.capital_manager import CapitalManager

class TestCapitalManager(unittest.TestCase):

    def test_initial_capital(self):
        """Test starting capital is 70K"""
        manager = CapitalManager(
            start_date=date(2020, 1, 1),
            starting_cash=70000,
            monthly_injection=70000
        )

        self.assertEqual(manager.available_cash, 70000)
        self.assertEqual(manager.total_injected, 70000)
        self.assertEqual(manager.portfolio_value, 70000)

    def test_monthly_injection(self):
        """Test monthly injection increases cash"""
        manager = CapitalManager(
            start_date=date(2020, 1, 1),
            starting_cash=70000,
            monthly_injection=70000
        )

        # Same month - no injection
        manager.update_date(date(2020, 1, 15))
        self.assertEqual(manager.available_cash, 70000)

        # New month - should inject 70K
        manager.update_date(date(2020, 2, 1))
        self.assertEqual(manager.available_cash, 140000)
        self.assertEqual(manager.total_injected, 140000)

        # Another month
        manager.update_date(date(2020, 3, 1))
        self.assertEqual(manager.available_cash, 210000)
        self.assertEqual(manager.total_injected, 210000)

    def test_only_one_injection_per_month(self):
        """Test multiple dates in same month don't cause multiple injections"""
        manager = CapitalManager(
            start_date=date(2020, 1, 1),
            starting_cash=70000,
            monthly_injection=70000
        )

        manager.update_date(date(2020, 2, 1))
        manager.update_date(date(2020, 2, 15))
        manager.update_date(date(2020, 2, 28))

        # Should only inject once
        self.assertEqual(manager.available_cash, 140000)

    def test_backwards_date_no_double_injection(self):
        """Test that moving backwards in time doesn't cause double injection"""
        manager = CapitalManager(
            start_date=date(2020, 1, 1),
            starting_cash=70000,
            monthly_injection=70000
        )

        # Move to February
        manager.update_date(date(2020, 2, 1))
        self.assertEqual(manager.available_cash, 140000)

        # Move backwards to January 15 - should NOT inject again
        manager.update_date(date(2020, 1, 15))
        self.assertEqual(manager.available_cash, 140000)  # Still 140K, not 210K

if __name__ == '__main__':
    unittest.main()
