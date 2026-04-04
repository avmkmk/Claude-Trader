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
        current_month = (current_date.year, current_date.month)

        # Check if new month and moving forward in time
        if current_month != self.last_injection_month and current_date > self.current_date:
            self.available_cash += self.monthly_injection
            self.total_injected += self.monthly_injection
            self.last_injection_month = current_month

        self.current_date = current_date

    def calculate_position_size(self, stock_price):
        """
        Calculate position size (10% of portfolio)

        Args:
            stock_price: Current stock price

        Returns:
            Number of shares to buy (floored to integer)
        """
        # Target position value: 10% of portfolio
        target_value = self.portfolio_value * 0.10

        # Calculate shares (floor to integer)
        shares = int(target_value / stock_price)

        # Can't afford even 1 share
        if shares < 1:
            return 0

        # Check if we have enough cash
        required_cash = shares * stock_price
        if required_cash > self.available_cash:
            # Scale down to available cash
            shares = int(self.available_cash / stock_price)

        return shares

    def enter_trade(self, shares, entry_price):
        """
        Execute trade entry - update cash and invested capital

        Args:
            shares: Number of shares bought
            entry_price: Entry price per share
        """
        cost = shares * entry_price
        self.available_cash -= cost
        self.invested_capital += cost

    def exit_trade(self, shares, entry_price, exit_price):
        """
        Execute trade exit - update cash and invested capital

        Args:
            shares: Number of shares sold
            entry_price: Original entry price (to remove from invested capital)
            exit_price: Exit price per share
        """
        proceeds = shares * exit_price
        original_cost = shares * entry_price

        self.available_cash += proceeds
        self.invested_capital -= original_cost

    def update_position_value(self, shares, current_price):
        """
        Mark position to market (update invested capital with current price)

        Args:
            shares: Number of shares held
            current_price: Current market price

        Note: This replaces invested_capital entirely. Should be called
              with total portfolio position values, not individual trades.
        """
        self.invested_capital = shares * current_price
