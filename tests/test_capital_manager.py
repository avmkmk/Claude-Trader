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

    def test_position_sizing_basic(self):
        """Test 10% position sizing calculation"""
        manager = CapitalManager(
            start_date=date(2020, 1, 1),
            starting_cash=70000,
            monthly_injection=70000
        )

        # Stock price 100, portfolio 70K, target 10% = 7K
        # Should buy 70 shares
        shares = manager.calculate_position_size(stock_price=100)
        self.assertEqual(shares, 70)

    def test_position_sizing_fractional_shares(self):
        """Test that shares are floored (no fractional shares)"""
        manager = CapitalManager(
            start_date=date(2020, 1, 1),
            starting_cash=70000,
            monthly_injection=70000
        )

        # Stock price 333, portfolio 70K, target 10% = 7K
        # 7000 / 333 = 21.02 → floor to 21
        shares = manager.calculate_position_size(stock_price=333)
        self.assertEqual(shares, 21)

    def test_position_sizing_insufficient_cash(self):
        """Test position sizing when cash < target position value"""
        manager = CapitalManager(
            start_date=date(2020, 1, 1),
            starting_cash=70000,
            monthly_injection=70000
        )

        # Simulate 60K in open positions
        manager.invested_capital = 60000
        manager.available_cash = 10000

        # Portfolio = 70K, target 10% = 7K, but only 10K cash available
        # Stock price 100 → should buy 70 shares (7K worth)
        # But only 10K cash → buy 100 shares max
        shares = manager.calculate_position_size(stock_price=100)
        self.assertEqual(shares, 70)  # 10% of portfolio, within cash limit

        # If stock price is 200, target = 35 shares (7K)
        # But 10K cash → can afford 50 shares
        # Should return 35 (target is lower than cash limit)
        shares = manager.calculate_position_size(stock_price=200)
        self.assertEqual(shares, 35)

    def test_position_sizing_expensive_stock(self):
        """Test that expensive stocks return 0 if can't afford 1 share"""
        manager = CapitalManager(
            start_date=date(2020, 1, 1),
            starting_cash=70000,
            monthly_injection=70000
        )

        # Stock price 10K, target 10% = 7K → can't afford even 1 share
        shares = manager.calculate_position_size(stock_price=10000)
        self.assertEqual(shares, 0)

    def test_entry_execution_updates_capital(self):
        """Test that entering trade updates cash and invested capital"""
        manager = CapitalManager(
            start_date=date(2020, 1, 1),
            starting_cash=70000,
            monthly_injection=70000
        )

        # Enter trade: 50 shares @ 100 = 5000
        manager.enter_trade(shares=50, entry_price=100)

        self.assertEqual(manager.available_cash, 65000)
        self.assertEqual(manager.invested_capital, 5000)
        self.assertEqual(manager.portfolio_value, 70000)

    def test_exit_execution_updates_capital(self):
        """Test that exiting trade updates cash and invested capital"""
        manager = CapitalManager(
            start_date=date(2020, 1, 1),
            starting_cash=70000,
            monthly_injection=70000
        )

        # Enter trade: 50 shares @ 100 = 5000
        manager.enter_trade(shares=50, entry_price=100)

        # Exit trade: 50 shares @ 150 = 7500
        manager.exit_trade(shares=50, entry_price=100, exit_price=150)

        self.assertEqual(manager.available_cash, 72500)  # 65K + 7.5K
        self.assertEqual(manager.invested_capital, 0)
        self.assertEqual(manager.portfolio_value, 72500)

    def test_mark_to_market_portfolio_value(self):
        """Test portfolio value updates with current prices (mark-to-market)"""
        manager = CapitalManager(
            start_date=date(2020, 1, 1),
            starting_cash=70000,
            monthly_injection=70000
        )

        # Enter trade: 50 shares @ 100 = 5000 cost
        manager.enter_trade(shares=50, entry_price=100)

        # Stock price rises to 120 → position worth 6000 now
        manager.update_position_value(shares=50, current_price=120)

        self.assertEqual(manager.available_cash, 65000)
        self.assertEqual(manager.invested_capital, 6000)  # Mark-to-market
        self.assertEqual(manager.portfolio_value, 71000)

if __name__ == '__main__':
    unittest.main()
