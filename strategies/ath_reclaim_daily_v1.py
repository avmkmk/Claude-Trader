"""
ATH Reclaim Daily Strategy V1

Long-term trend-following strategy:
1. Stock makes ATH (Phase 1)
2. Consolidates below EMA 200 (Phase 2)
3. Breaks above ATH → ENTRY (Phase 3)
4. Hold until close below EMA 200 → EXIT

Position sizing: 10% of portfolio
Hold time: Months to years
"""
import backtrader as bt
from datetime import date

class ATHReclaimStrategy(bt.Strategy):
    """
    ATH Reclaim strategy with 3-phase state machine
    """

    params = (
        ('ema_period', 200),          # EMA period for trend
        ('gap_tolerance', 0.001),     # Gap detection tolerance (0.1%)
        ('position_pct', 0.10),       # Position size (10% of portfolio)
        ('verbose', True),            # Print trade logs
    )

    def __init__(self):
        """Initialize indicators and state tracking"""

        # Indicators
        self.ema_200 = bt.indicators.ExponentialMovingAverage(
            self.data.close,
            period=self.params.ema_period
        )

        # ATH tracking - manually track instead of using Highest indicator
        # (Highest has fixed lookback, we need all-time tracking)
        self.ath_value = None
        self.ath_date = None

        # State tracking per stock
        self.current_phase = None  # 1, 2, or 3
        self.below_ema200_date = None
        self.entry_price = None
        self.entry_date = None
        self.position_size = None

        # Track previous close for gap detection
        self.prev_close = None

    def log(self, message):
        """Log message with date"""
        if self.params.verbose:
            dt = self.data.datetime.date(0)
            print(f'{dt}: {message}')

    def next(self):
        """
        Called for each new bar
        """
        current_date = self.data.datetime.date(0)
        current_close = self.data.close[0]
        current_high = self.data.high[0]
        current_open = self.data.open[0]

        # Update ATH if new high
        if self.ath_value is None or current_high > self.ath_value:
            self.ath_value = current_high
            self.ath_date = current_date
            if self.current_phase is None:
                self.current_phase = 1
                self.log(f'Phase 1: ATH {self.ath_value:.2f}')

        # Update previous close for next iteration
        self.prev_close = current_close

    def notify_order(self, order):
        """Called when order status changes"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED: {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED: {order.executed.price:.2f}')

    def notify_trade(self, trade):
        """Called when trade closes"""
        if trade.isclosed:
            self.log(f'TRADE CLOSED: P&L = {trade.pnl:.2f}')
