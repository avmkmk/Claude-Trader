"""
Breakout Strategy Template

Strategy Logic:
- BUY when price breaks above resistance with volume expansion AND ATR confirms volatility
- SELL when breakout fails (price returns below breakout level) OR target/stop hit
- Confirmation: Volume > 1.2x average, ATR expanding

Best Market Conditions: Ranging market before breakout, then volatility spike
Timeframe: 15-min to 1-hour
Win Rate Target: 45-55%
Risk:Reward: 1:2 to 1:3
"""

import backtrader as bt
import datetime


class BreakoutStrategy(bt.Strategy):
    """
    ATR + Volume Breakout Strategy
    Trades breakouts of consolidation ranges with volume confirmation
    """

    params = (
        ('channel_period', 20),      # Price channel lookback period
        ('atr_period', 14),          # ATR period
        ('atr_threshold', 1.2),      # Min ATR (multiplier of SMA)
        ('volume_period', 20),       # Volume moving average period
        ('volume_threshold', 1.2),   # Volume confirmation multiplier
        ('bb_period', 20),           # Bollinger Bands period
        ('bb_std', 2.0),             # Bollinger Bands standard deviation
        ('atr_stop_mult', 1.0),      # ATR multiplier for stop loss (below breakout)
        ('atr_target_mult', 2.5),    # ATR multiplier for target
        ('max_hold_bars', 60),       # Maximum hold time in bars
    )

    def __init__(self):
        """Initialize indicators"""

        # Highest/Lowest for breakout levels
        self.highest = bt.indicators.Highest(
            self.data.high,
            period=self.params.channel_period
        )
        self.lowest = bt.indicators.Lowest(
            self.data.low,
            period=self.params.channel_period
        )

        # ATR (Average True Range) for volatility
        self.atr = bt.indicators.ATR(
            self.data,
            period=self.params.atr_period
        )

        # ATR moving average (to detect expanding volatility)
        self.atr_sma = bt.indicators.SimpleMovingAverage(
            self.atr,
            period=self.params.atr_period
        )

        # Volume moving average
        self.volume_sma = bt.indicators.SimpleMovingAverage(
            self.data.volume,
            period=self.params.volume_period
        )

        # Bollinger Bands (for squeeze detection)
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_std
        )

        # Track entry details
        self.entry_bar = None
        self.entry_price = None
        self.breakout_level = None
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

        # === ENTRY LOGIC ===
        if not self.position:
            # Breakout level (20-period high)
            resistance = self.highest[-1]  # Previous highest (not including current bar)

            # Price breaks above resistance
            breakout = self.data.close[0] > resistance

            # Volume confirmation (expansion)
            volume_confirmed = (self.data.volume[0] >
                              self.volume_sma[0] * self.params.volume_threshold)

            # ATR expanding (volatility increasing)
            volatility_expanding = (self.atr[0] >
                                   self.atr_sma[0] * self.params.atr_threshold)

            # Candle closes above breakout level (not just wick)
            clean_breakout = self.data.close[0] > resistance

            if breakout and volume_confirmed and volatility_expanding and clean_breakout:
                # Enter long position
                self.buy()
                self.entry_bar = len(self)
                self.entry_price = self.data.close[0]
                self.breakout_level = resistance

                # Set stop loss just below breakout level
                self.stop_loss = self.breakout_level - (self.atr[0] * self.params.atr_stop_mult)

                # Set target based on ATR
                self.target = self.entry_price + (self.atr[0] * self.params.atr_target_mult)

                print(f'{self.data.datetime.date()} BUY at {self.data.close[0]:.2f} '
                      f'(Breakout: {resistance:.2f}, ATR: {self.atr[0]:.2f}, '
                      f'Vol: {self.data.volume[0]/self.volume_sma[0]:.2f}x, '
                      f'Stop: {self.stop_loss:.2f}, Target: {self.target:.2f})')

        # === EXIT LOGIC ===
        else:
            # Time-based exit: Max hold time exceeded
            bars_held = len(self) - self.entry_bar
            if bars_held >= self.params.max_hold_bars:
                self.sell()
                print(f'{self.data.datetime.date()} SELL (Time exit) at {self.data.close[0]:.2f}')
                return

            # Stop loss hit (breakout failed)
            if self.data.close[0] <= self.stop_loss:
                self.sell()
                print(f'{self.data.datetime.date()} SELL (Stop loss / Failed breakout) at {self.data.close[0]:.2f}')
                return

            # Target hit
            if self.data.close[0] >= self.target:
                self.sell()
                print(f'{self.data.datetime.date()} SELL (Target) at {self.data.close[0]:.2f}')
                return

            # Breakout invalidation: Price closes back below breakout level
            if self.data.close[0] < self.breakout_level:
                self.sell()
                print(f'{self.data.datetime.date()} SELL (Breakout invalidated) at {self.data.close[0]:.2f}')

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
    runner.add_strategy(BreakoutStrategy)

    # Or customize parameters:
    # runner.add_strategy(BreakoutStrategy,
    #                    channel_period=30,
    #                    volume_threshold=1.5,
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
