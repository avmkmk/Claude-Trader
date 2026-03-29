"""
Supertrend + EMA Trend Strategy (Simplified)

Strategy Logic:
- Uses EMA crossover for entry signals
- 200 EMA confirms macro trend
- Entry: Fast EMA crosses above slow EMA AND price > 200 EMA
- Exit: Fast EMA crosses below slow EMA OR 2x ATR stop OR 3x ATR target
- Timeframe: Daily, 15min
- Target: Win rate 45-55%, R:R 1:2

Best Market Conditions: Strong trending markets
Timeframe: Daily, 15min
"""

import backtrader as bt
import datetime


class SupertrendTrendStrategy(bt.Strategy):
    """
    Supertrend + EMA Trend Strategy (Simplified)
    
    Uses EMA crossover with 200 EMA as macro trend filter.
    This is a simplified but more reliable version.
    """

    params = (
        ('fast_ema_period', 9),
        ('slow_ema_period', 20),
        ('sma_period', 200),
        ('atr_period', 14),
        ('atr_stop_mult', 2.0),
        ('atr_target_mult', 3.0),
        ('volume_period', 20),
        ('volume_threshold', 1.0),
        ('max_hold_bars', 120),
    )

    def __init__(self):
        """Initialize indicators"""
        
        # Fast EMA
        self.fast_ema = bt.indicators.EMA(
            self.data.close,
            period=self.params.fast_ema_period
        )
        
        # Slow EMA
        self.slow_ema = bt.indicators.EMA(
            self.data.close,
            period=self.params.slow_ema_period
        )
        
        # EMA Crossover
        self.ema_crossover = bt.indicators.CrossOver(
            self.fast_ema,
            self.slow_ema
        )
        
        # 200-period SMA for macro trend filter
        self.sma_200 = bt.indicators.SimpleMovingAverage(
            self.data.close,
            period=self.params.sma_period
        )
        
        # ATR for stops
        self.atr = bt.indicators.ATR(
            self.data,
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
        self.stop_loss = None
        self.target = None

    def next(self):
        """Trading logic"""
        
        # Need enough data for 200 SMA
        if len(self) < self.params.sma_period + 2:
            return
        
        # === CHECK TIME (skip for daily data) ===
        current_time = self.data.datetime.time()
        is_midnight = (current_time == datetime.time(0, 0))
        
        if not is_midnight:
            if (current_time < datetime.time(9, 45) or 
                current_time > datetime.time(14, 30)):
                return
        
        # Volume filter
        if self.data.volume[0] < self.volume_sma[0] * self.params.volume_threshold:
            return
        
        # Macro trend: price above 200 SMA
        price_above_200ema = self.data.close[0] > self.sma_200[0]
        
        # === ENTRY LOGIC ===
        if not self.position:
            # Long: Fast EMA crosses above slow EMA AND price above 200 EMA
            if self.ema_crossover > 0 and price_above_200ema:
                self.buy()
                self.entry_bar = len(self)
                self.entry_price = self.data.close[0]
                
                # Set stop loss
                self.stop_loss = self.entry_price - (self.atr[0] * self.params.atr_stop_mult)
                
                # Set target
                self.target = self.entry_price + (self.atr[0] * self.params.atr_target_mult)
                
                print(f'{self.data.datetime.date()} '
                      f'BUY (EMA bullish + 200EMA) at {self.data.close[0]:.2f} '
                      f'(FastEMA: {self.fast_ema[0]:.2f}, SlowEMA: {self.slow_ema[0]:.2f}, '
                      f'200SMA: {self.sma_200[0]:.2f}, '
                      f'Stop: {self.stop_loss:.2f}, Target: {self.target:.2f})')
        
        # === EXIT LOGIC ===
        else:
            # Time-based exit
            bars_held = len(self) - self.entry_bar
            if bars_held >= self.params.max_hold_bars:
                self.sell()
                print(f'{self.data.datetime.date()} SELL (Time exit) at {self.data.close[0]:.2f}')
                self.entry_bar = None
                return
            
            # Stop loss hit
            if self.data.close[0] <= self.stop_loss:
                self.sell()
                print(f'{self.data.datetime.date()} SELL (Stop) at {self.data.close[0]:.2f}')
                self.entry_bar = None
                return
            
            # Target hit
            if self.data.close[0] >= self.target:
                self.sell()
                print(f'{self.data.datetime.date()} SELL (Target) at {self.data.close[0]:.2f}')
                self.entry_bar = None
                return
            
            # EMA bearish crossover
            if self.ema_crossover < 0:
                self.sell()
                print(f'{self.data.datetime.date()} SELL (EMA cross) at {self.data.close[0]:.2f}')
                self.entry_bar = None
                return

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'  -> BUY EXECUTED at {order.executed.price:.2f}')
            elif order.issell():
                print(f'  -> SELL EXECUTED at {order.executed.price:.2f}')

    def notify_trade(self, trade):
        if trade.isclosed:
            print(f'  -> TRADE CLOSED: P&L = Rs {trade.pnl:.2f}')


if __name__ == '__main__':
    from backtesting.backtest_runner import BacktestRunner

    runner = BacktestRunner(initial_cash=5000000)
    runner.load_data('path/to/daily/data.csv', 'RELIANCE')
    runner.add_strategy(SupertrendTrendStrategy)
    runner.add_analyzers()
    result = runner.run()
    metrics = runner.get_metrics(result)
    print(f"Sharpe: {metrics['sharpe_ratio']}")
    print(f"Return: {metrics['returns']['total_return']:.2%}")
