"""
Mean Reversion Strategy Template

Strategy Logic:
- BUY when price is oversold (RSI < 30) AND price touches lower Bollinger Band
- SELL when price returns to mean (RSI > 50) OR price touches upper Bollinger Band
- Confirmation: Volume must be reasonable (>0.5x average)

Best Market Conditions: Ranging, choppy markets
Timeframe: 15-min to 1-hour
Win Rate Target: 55-65%
Risk:Reward: 1:1.5 to 1:2
"""

import backtrader as bt
import datetime


class MeanReversionStrategy(bt.Strategy):
    """
    RSI + Bollinger Bands Mean Reversion Strategy
    Buys oversold conditions, sells when returning to mean
    """

    params = (
        ('rsi_period', 14),          # RSI period
        ('rsi_oversold', 30),        # RSI oversold level
        ('rsi_exit', 50),            # RSI exit level
        ('bb_period', 20),           # Bollinger Bands period
        ('bb_std', 2),               # Bollinger Bands standard deviation
        ('volume_period', 20),       # Volume moving average period
        ('volume_threshold', 0.5),   # Minimum volume (% of average)
        ('max_hold_bars', 60),       # Maximum hold time in bars
    )

    def __init__(self):
        """Initialize indicators"""

        # RSI (Relative Strength Index)
        self.rsi = bt.indicators.RSI(
            self.data.close,
            period=self.params.rsi_period
        )

        # Bollinger Bands
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_std
        )

        # Volume moving average
        self.volume_sma = bt.indicators.SimpleMovingAverage(
            self.data.volume,
            period=self.params.volume_period
        )

        # Track entry details
        self.entry_bar = None
        self.entry_price = None

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
        if self.data.volume[0] < (self.volume_sma[0] * self.params.volume_threshold):
            return

        # === ENTRY LOGIC ===
        if not self.position:
            # Check for oversold condition
            if (self.rsi[0] < self.params.rsi_oversold and
                self.data.close[0] < self.bb.lines.bot[0]):

                # Enter long position
                self.buy()
                self.entry_bar = len(self)
                self.entry_price = self.data.close[0]

                print(f'{self.data.datetime.date()} BUY at {self.data.close[0]:.2f} '
                      f'(RSI: {self.rsi[0]:.2f}, BB Lower: {self.bb.lines.bot[0]:.2f})')

        # === EXIT LOGIC ===
        else:
            # Time-based exit: Max hold time exceeded
            bars_held = len(self) - self.entry_bar
            if bars_held >= self.params.max_hold_bars:
                self.sell()
                print(f'{self.data.datetime.date()} SELL (Time exit) at {self.data.close[0]:.2f}')
                return

            # Target exit: RSI returns to neutral or price hits upper BB
            if (self.rsi[0] > self.params.rsi_exit or
                self.data.close[0] > self.bb.lines.top[0]):

                self.sell()
                print(f'{self.data.datetime.date()} SELL (Target) at {self.data.close[0]:.2f} '
                      f'(RSI: {self.rsi[0]:.2f})')

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
    runner.add_strategy(MeanReversionStrategy)

    # Or customize parameters:
    # runner.add_strategy(MeanReversionStrategy,
    #                    rsi_oversold=25,
    #                    rsi_exit=55,
    #                    max_hold_bars=40)

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
