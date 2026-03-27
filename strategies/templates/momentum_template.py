"""
Momentum Strategy Template

Strategy Logic:
- BUY when MACD crosses above signal line with increasing histogram AND volume confirms
- SELL when MACD crosses below signal line OR trailing stop hit
- Confirmation: RSI in healthy range (40-70), volume above average

Best Market Conditions: Trending markets (up or down)
Timeframe: 5-min to 30-min
Win Rate Target: 50-60%
Risk:Reward: 1:2 to 1:3
"""

import backtrader as bt
import datetime


class MomentumStrategy(bt.Strategy):
    """
    MACD + Volume Momentum Strategy
    Trades in direction of momentum with volume confirmation
    """

    params = (
        ('macd_fast', 12),           # MACD fast period
        ('macd_slow', 26),           # MACD slow period
        ('macd_signal', 9),          # MACD signal period
        ('rsi_period', 14),          # RSI period
        ('rsi_min', 40),             # Minimum RSI (avoid oversold)
        ('rsi_max', 70),             # Maximum RSI (avoid overbought)
        ('volume_period', 20),       # Volume moving average period
        ('volume_multiplier', 1.0),  # Minimum volume multiplier
        ('atr_period', 14),          # ATR period for stops
        ('atr_stop_mult', 1.5),      # ATR multiplier for stop loss
        ('atr_target_mult', 2.5),    # ATR multiplier for target
        ('max_hold_bars', 120),      # Maximum hold time in bars
    )

    def __init__(self):
        """Initialize indicators"""

        # MACD (Moving Average Convergence Divergence)
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal
        )

        # RSI (Relative Strength Index)
        self.rsi = bt.indicators.RSI(
            self.data.close,
            period=self.params.rsi_period
        )

        # Volume moving average
        self.volume_sma = bt.indicators.SimpleMovingAverage(
            self.data.volume,
            period=self.params.volume_period
        )

        # ATR (Average True Range) for stop loss/target
        self.atr = bt.indicators.ATR(
            self.data,
            period=self.params.atr_period
        )

        # Track entry details
        self.entry_bar = None
        self.entry_price = None
        self.stop_loss = None
        self.target = None

    def next(self):
        """
        Trading logic called for each candle
        """

        # Time filter: Only trade during liquid hours (9:45 AM - 2:30 PM IST)
        current_time = self.data.datetime.time()
        if (current_time < datetime.time(9, 45) or
            current_time > datetime.time(14, 30)):
            return

        # Volume filter: Skip if volume too low
        if self.data.volume[0] < (self.volume_sma[0] * self.params.volume_multiplier):
            return

        # === ENTRY LOGIC ===
        if not self.position:
            # Check for bullish momentum
            # MACD line > Signal line AND histogram increasing
            macd_bullish = (self.macd.macd[0] > self.macd.signal[0] and
                           self.macd.histo[0] > self.macd.histo[-1])

            # RSI in healthy range (not overbought, not oversold)
            rsi_healthy = (self.params.rsi_min < self.rsi[0] < self.params.rsi_max)

            # Volume confirmation
            volume_confirmed = (self.data.volume[0] > self.volume_sma[0])

            if macd_bullish and rsi_healthy and volume_confirmed:
                # Enter long position
                self.buy()
                self.entry_bar = len(self)
                self.entry_price = self.data.close[0]

                # Set stop loss and target based on ATR
                self.stop_loss = self.entry_price - (self.atr[0] * self.params.atr_stop_mult)
                self.target = self.entry_price + (self.atr[0] * self.params.atr_target_mult)

                print(f'{self.data.datetime.date()} BUY at {self.data.close[0]:.2f} '
                      f'(MACD: {self.macd.macd[0]:.2f}, RSI: {self.rsi[0]:.2f}, '
                      f'Stop: {self.stop_loss:.2f}, Target: {self.target:.2f})')

        # === EXIT LOGIC ===
        else:
            # Time-based exit: Max hold time exceeded
            bars_held = len(self) - self.entry_bar
            if bars_held >= self.params.max_hold_bars:
                self.sell()
                print(f'{self.data.datetime.date()} SELL (Time exit) at {self.data.close[0]:.2f}')
                return

            # Stop loss hit
            if self.data.close[0] <= self.stop_loss:
                self.sell()
                print(f'{self.data.datetime.date()} SELL (Stop loss) at {self.data.close[0]:.2f}')
                return

            # Target hit
            if self.data.close[0] >= self.target:
                self.sell()
                print(f'{self.data.datetime.date()} SELL (Target) at {self.data.close[0]:.2f}')
                return

            # Signal-based exit: MACD bearish crossover
            if self.macd.macd[0] < self.macd.signal[0]:
                self.sell()
                print(f'{self.data.datetime.date()} SELL (MACD cross) at {self.data.close[0]:.2f}')

    def notify_order(self, order):
        """Log order executions"""
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'  -> BUY EXECUTED at {order.executed.price:.2f}')
            elif order.issell():
                print(f'  -> SELL EXECUTED at {order.executed.price:.2f}')

    def notify_trade(self, trade):
        """Log trade results when closed"""
        if trade.isclosed:
            print(f'  -> TRADE CLOSED: P&L = Rs {trade.pnl:.2f} '
                  f'({trade.pnlcomm:.2f} after commission)')


# === USAGE EXAMPLE ===
if __name__ == '__main__':
    """
    Example of how to use this strategy
    """
    from backtesting.backtest_runner import BacktestRunner

    # Create runner
    runner = BacktestRunner(initial_cash=100000)

    # Load data
    runner.load_data('data/GRAPHITE_90days.csv', 'GRAPHITE')

    # Add strategy with default parameters
    runner.add_strategy(MomentumStrategy)

    # Or customize parameters:
    # runner.add_strategy(MomentumStrategy,
    #                    rsi_min=45,
    #                    rsi_max=65,
    #                    atr_stop_mult=2.0,
    #                    atr_target_mult=3.0)

    # Add analyzers
    runner.add_analyzers()

    # Run backtest
    result = runner.run()

    # Get metrics
    metrics = runner.get_metrics(result)
    print('\n=== BACKTEST RESULTS ===')
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']}")
    print(f"Total Return: {metrics['returns']['total_return']:.2%}")
    print(f"Max Drawdown: {metrics['drawdown']['max_drawdown']:.2f}%")
    print(f"Win Rate: {metrics['trades']['won_trades']}/{metrics['trades']['total_trades']}")

    # Optionally display chart
    # runner.plot()
