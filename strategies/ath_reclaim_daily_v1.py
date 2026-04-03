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
        Called for each new bar - implements phase state machine
        """
        current_date = self.data.datetime.date(0)
        current_close = self.data.close[0]
        current_high = self.data.high[0]
        current_open = self.data.open[0]
        ema_value = self.ema_200[0]

        # Skip if not enough data for EMA
        if len(self.data) < self.params.ema_period:
            return

        # === PHASE 3: ATH Reclaim (Entry Signal) ===
        # Check BEFORE updating ATH so we compare against previous ATH
        # Only check if we're in Phase 2 and not already in a position
        if self.current_phase == 2 and not self.position:
            # Check if close > ATH (from previous bars)
            if self.ath_value is not None and current_close > self.ath_value:
                # Check for gap up
                if self.prev_close is not None:
                    gap_up = current_open > (self.prev_close * (1 + self.params.gap_tolerance))
                    if gap_up:
                        self.log(f'Phase 3 SKIPPED: Gap up detected (open={current_open:.2f}, prev_close={self.prev_close:.2f})')
                    else:
                        # Valid entry signal!
                        self.current_phase = 3

                        # Calculate position size (10% of portfolio)
                        portfolio_value = self.broker.getvalue()
                        target_value = portfolio_value * self.params.position_pct
                        shares = int(target_value / current_close)

                        # Check affordability
                        if shares < 1:
                            self.log(f'Phase 3 SKIPPED: Stock too expensive (price={current_close:.2f}, portfolio={portfolio_value:.2f})')
                        else:
                            # Check cash availability
                            available_cash = self.broker.getcash()
                            required_cash = shares * current_close

                            if required_cash > available_cash:
                                # Scale down to available cash
                                shares = int(available_cash / current_close)

                            if shares >= 1:
                                self.buy(size=shares)
                                self.entry_price = current_close
                                self.entry_date = current_date
                                self.position_size = shares
                                self.log(f'BUY ORDER: {shares} shares @ {current_close:.2f} (total: {shares * current_close:.2f})')
                            else:
                                self.log(f'Phase 3 SKIPPED: Insufficient cash (need {required_cash:.2f}, have {available_cash:.2f})')

        # === PHASE 1: Track ATH ===
        if self.ath_value is None or current_high > self.ath_value:
            self.ath_value = current_high
            self.ath_date = current_date
            if self.current_phase is None or self.current_phase == 1:
                self.current_phase = 1
                self.log(f'Phase 1: New ATH {self.ath_value:.2f}')

        # === PHASE 2: Below EMA 200 (Consolidation) ===
        if self.current_phase == 1 and current_close < ema_value:
            self.current_phase = 2
            self.below_ema200_date = current_date
            self.log(f'Phase 2: Below EMA 200 (close={current_close:.2f}, ema={ema_value:.2f})')

        # === EXIT LOGIC ===
        # If in position, check for exit (close < EMA 200)
        if self.position and current_close < ema_value:
            self.sell(size=self.position.size)

            hold_days = (current_date - self.entry_date).days if self.entry_date else 0
            self.log(f'SELL ORDER: Close below EMA 200 (close={current_close:.2f}, ema={ema_value:.2f}, hold_days={hold_days})')

            # Reset to Phase 1 after exit (keep tracking ATH for re-entry)
            self.current_phase = 1
            self.entry_price = None
            self.entry_date = None
            self.position_size = None

        # Update previous close for gap detection
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
