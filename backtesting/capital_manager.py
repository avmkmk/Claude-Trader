"""
Capital Manager for ATH Reclaim Strategy

Handles:
- Monthly capital injections
- Position sizing calculations
- Cash and portfolio tracking
"""
from datetime import date

class CapitalManager:
    """
    Manages capital with monthly injections and position sizing
    """

    def __init__(self, start_date, starting_cash=70000, monthly_injection=70000):
        """
        Initialize capital manager

        Args:
            start_date: Backtest start date
            starting_cash: Initial capital (default 70K)
            monthly_injection: Monthly injection amount (default 70K)
        """
        self.start_date = start_date
        self.starting_cash = starting_cash
        self.monthly_injection = monthly_injection

        # Capital tracking
        self.available_cash = starting_cash
        self.invested_capital = 0.0
        self.total_injected = starting_cash

        # Date tracking for injections
        self.current_date = start_date
        self.last_injection_month = (start_date.year, start_date.month)

    @property
    def portfolio_value(self):
        """Total portfolio value (cash + invested)"""
        return self.available_cash + self.invested_capital

    def update_date(self, current_date):
        """
        Update current date and inject capital if new month

        Args:
            current_date: Current backtest date
        """
        self.current_date = current_date
        current_month = (current_date.year, current_date.month)

        # Check if new month
        if current_month != self.last_injection_month:
            self.available_cash += self.monthly_injection
            self.total_injected += self.monthly_injection
            self.last_injection_month = current_month
