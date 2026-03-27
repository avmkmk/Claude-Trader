import backtrader as bt


class SMACrossoverStrategy(bt.Strategy):
    """
    Simple Moving Average Crossover Strategy

    Strategy Logic:
    - BUY when fast SMA crosses above slow SMA (Golden Cross)
    - SELL when fast SMA crosses below slow SMA (Death Cross)

    Converted from main.py lines 64-79
    """

    params = (
        ('fast_period', 10),  # Fast SMA period (default from main.py)
        ('slow_period', 30),  # Slow SMA period (default from main.py)
    )

    def __init__(self):
        """Initialize indicators"""
        # Calculate SMAs using backtrader indicators
        self.fast_sma = bt.indicators.SimpleMovingAverage(
            self.data.close,
            period=self.params.fast_period
        )
        self.slow_sma = bt.indicators.SimpleMovingAverage(
            self.data.close,
            period=self.params.slow_period
        )

        # Crossover indicator
        # Positive value = fast SMA crosses above slow SMA
        # Negative value = fast SMA crosses below slow SMA
        self.crossover = bt.indicators.CrossOver(
            self.fast_sma,
            self.slow_sma
        )

    def next(self):
        """
        Called for each new data point
        Implements trading logic from main.py lines 76-79
        """
        if not self.position:  # Not in market
            if self.crossover > 0:  # Fast crosses above slow (Golden Cross)
                self.buy()
                print(f'{self.data.datetime.date()} BUY Signal at {self.data.close[0]:.2f}')

        else:  # In market
            if self.crossover < 0:  # Fast crosses below slow (Death Cross)
                self.sell()
                print(f'{self.data.datetime.date()} SELL Signal at {self.data.close[0]:.2f}')

    def notify_order(self, order):
        """Log order executions"""
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'  -> BUY EXECUTED at {order.executed.price:.2f}')
            elif order.issell():
                print(f'  -> SELL EXECUTED at {order.executed.price:.2f}')

    def notify_trade(self, trade):
        """Log trade P&L when closed"""
        if trade.isclosed:
            print(f'  -> TRADE CLOSED: P&L = {trade.pnl:.2f}')
