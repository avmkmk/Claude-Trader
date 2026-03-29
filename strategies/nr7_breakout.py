"""
NR7 + Inside Bar Breakout Strategy

Strategy Logic:
- Volatility compression (NR7 = Narrowest Range in 7 bars) often precedes explosive moves
- Inside Bar: Current bar's range is within previous bar's range
- Entry: Place buy stop above NR7 high, sell stop below NR7 low
- Exit: Trailing stop 1x ATR OR target 2.5x ATR OR time exit (60 bars)
- Timeframe: Daily, 60min
- Target: Win rate 45-55%, R:R 1:2.5

Best Market Conditions: After consolidation / volatility compression
Timeframe: Daily, 60min
"""

import backtrader as bt
import datetime


class NR7BreakoutStrategy(bt.Strategy):
    """
    NR7 + Inside Bar Breakout Strategy
    
    Trades breakouts from volatility compression patterns:
    - NR7: Narrowest range in last 7 bars (consolidation)
    - Inside Bar: Current bar inside previous bar's range
    
    Entry on breakout above NR7 high or below NR7 low with volume confirmation.
    """

    params = (
        ('nr7_period', 7),              # Lookback for narrowest range
        ('atr_period', 14),
        ('atr_stop_mult', 1.0),
        ('atr_target_mult', 2.5),
        ('volume_period', 20),
        ('volume_threshold', 1.2),
        ('atr_expansion_threshold', 1.1),
        ('max_hold_bars', 60),
    )

    def __init__(self):
        """Initialize indicators"""
        
        # Calculate true range for each bar
        self.true_range = bt.indicators.TrueRange(self.data)
        
        # Calculate bar ranges (high - low)
        self.bar_range = self.data.high - self.data.low
        
        # Highest and lowest for channel
        self.highest = bt.indicators.Highest(
            self.data.high,
            period=self.params.nr7_period
        )
        self.lowest = bt.indicators.Lowest(
            self.data.low,
            period=self.params.nr7_period
        )
        
        # ATR for stops
        self.atr = bt.indicators.ATR(
            self.data,
            period=self.params.atr_period
        )
        
        # ATR SMA for expansion detection
        self.atr_sma = bt.indicators.SimpleMovingAverage(
            self.atr,
            period=self.params.atr_period
        )
        
        # Volume moving average
        self.volume_sma = bt.indicators.SimpleMovingAverage(
            self.data.volume,
            period=self.params.volume_period
        )
        
        # Track entry details
        self.entry_bar = None
        self.entry_price = None
        self.breakout_level = None
        self.stop_loss = None
        self.target = None
        self.breakout_direction = None  # 1 for long, -1 for short

    def next(self):
        """
        Trading logic called for each candle
        """
        
        # Need enough data for indicators
        if len(self) < self.params.nr7_period + 2:
            return
        
        # Time filter: Only trade during liquid hours (9:45 AM - 2:30 PM IST)
        current_time = self.data.datetime.time()
        if (current_time < datetime.time(9, 45) or 
            current_time > datetime.time(14, 30)):
            return
        
        # === DETECT NR7 (Narrowest Range in 7 bars) ===
        current_range = self.bar_range[0]
        nr7_range = self.highest[0] - self.lowest[0]
        
        # Find actual NR7 by checking all bars in lookback
        ranges_list = [self.bar_range[-i] for i in range(1, self.params.nr7_period + 1)]
        nr7_actual = min(ranges_list)
        nr7_index = ranges_list.index(nr7_actual) + 1  # How many bars back
        
        is_nr7 = (current_range <= nr7_actual * 1.1)  # Within 10% of NR7
        
        # === DETECT INSIDE BAR ===
        # Current bar inside previous bar's range
        is_inside = (
            self.data.high[0] < self.data.high[-1] and
            self.data.low[0] > self.data.low[-1]
        )
        
        # === BREAKOUT LEVELS ===
        # Use the NR7 bar's high/low as breakout levels
        nr7_high = self.data.high[-nr7_index]
        nr7_low = self.data.low[-nr7_index]
        
        # === CONFIRMATION ===
        volume_confirmed = self.data.volume[0] > self.volume_sma[0] * self.params.volume_threshold
        atr_expanding = self.atr[0] > self.atr_sma[0] * self.params.atr_expansion_threshold
        
        # === ENTRY LOGIC ===
        if not self.position:
            # Bullish breakout: Price breaks above NR7 high
            bullish_breakout = self.data.close[0] > nr7_high
            
            # Bearish breakout: Price breaks below NR7 low
            bearish_breakout = self.data.close[0] < nr7_low
            
            if (is_nr7 or is_inside) and volume_confirmed:
                if bullish_breakout:
                    self.buy()
                    self.entry_bar = len(self)
                    self.entry_price = self.data.close[0]
                    self.breakout_level = nr7_high
                    self.breakout_direction = 1
                    
                    # Stop below breakout level
                    self.stop_loss = self.breakout_level - (self.atr[0] * self.params.atr_stop_mult)
                    
                    # Target
                    self.target = self.entry_price + (self.atr[0] * self.params.atr_target_mult)
                    
                    print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                          f'BUY (NR7 Breakout) at {self.data.close[0]:.2f} '
                          f'(Breakout: {nr7_high:.2f}, ATR: {self.atr[0]:.2f}, '
                          f'Vol: {self.data.volume[0]/self.volume_sma[0]:.1f}x, '
                          f'Stop: {self.stop_loss:.2f}, Target: {self.target:.2f})')
                    
                elif bearish_breakout:
                    # For now, we only trade long (can add short later)
                    pass
        
        # === EXIT LOGIC ===
        else:
            # Time-based exit
            bars_held = len(self) - self.entry_bar
            if bars_held >= self.params.max_hold_bars:
                self.sell()
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'SELL (Time exit) at {self.data.close[0]:.2f}')
                self.entry_bar = None
                return
            
            # Stop loss hit (breakout failed)
            if self.data.close[0] <= self.stop_loss:
                self.sell()
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'SELL (Stop loss) at {self.data.close[0]:.2f}')
                self.entry_bar = None
                return
            
            # Target hit
            if self.data.close[0] >= self.target:
                self.sell()
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'SELL (Target) at {self.data.close[0]:.2f}')
                self.entry_bar = None
                return
            
            # Breakout invalidated: Price closes back below breakout level
            if self.breakout_direction == 1 and self.data.close[0] < self.breakout_level:
                self.sell()
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'SELL (Breakout invalidated) at {self.data.close[0]:.2f}')
                self.entry_bar = None
                return

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
    runner = BacktestRunner(initial_cash=5000000)

    # Load daily data
    runner.load_data('path/to/daily/data.csv', 'RELIANCE')

    # Add strategy with default parameters
    runner.add_strategy(NR7BreakoutStrategy)

    # Or customize:
    # runner.add_strategy(NR7BreakoutStrategy,
    #                    nr7_period=10,  # Look back 10 bars
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
