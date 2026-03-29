"""
ADX Trend Strength + DI Crossovers Strategy

Strategy Logic:
- ADX measures trend strength
- DI+/DI- give direction
- Entry: ADX > 25 (strong trend) AND DI+ crosses above DI-
- Exit: ADX drops below 20 OR DI- crosses above DI+ OR 2x ATR stop OR 2.5x ATR target
- Timeframe: Daily
- Target: Win rate 45-55%, R:R 1:2.5

Best Market Conditions: Strong trending markets
Timeframe: Daily
"""

import backtrader as bt
import datetime


class ADXTrendStrategy(bt.Strategy):
    """
    ADX Trend Strength + DI Crossovers Strategy
    
    Uses Average Directional Index (ADX) to measure trend strength
    and Directional Indicators (DI+/DI-) for entry direction.
    """

    params = (
        ('adx_period', 14),
        ('adx_threshold', 25),          # Minimum ADX for trend
        ('atr_period', 14),
        ('atr_stop_mult', 2.0),
        ('atr_target_mult', 2.5),
        ('volume_period', 20),
        ('volume_threshold', 1.0),
        ('max_hold_bars', 90),
    )

    def __init__(self):
        """Initialize indicators"""
        
        # ADX (Average Directional Index)
        self.adx = bt.indicators.ADX(
            self.data,
            period=self.params.adx_period
        )
        
        # DI+ (Directional Indicator Plus)
        self.di_plus = bt.indicators.PlusDI(
            self.data,
            period=self.params.adx_period
        )
        
        # DI- (Directional Indicator Minus)
        self.di_minus = bt.indicators.MinusDI(
            self.data,
            period=self.params.adx_period
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
        self.trend_direction = None

    def next(self):
        """
        Trading logic called for each candle
        """
        
        # Need enough data
        if len(self) < self.params.adx_period + 2:
            return
        
        # === CHECK TIME (skip for daily data) ===
        # For daily data, datetime.time() returns 00:00 which would fail the filter
        # So we only apply time filter if time is available and not midnight
        current_time = self.data.datetime.time()
        
        # Only apply time filter if it's not midnight (intraday data)
        is_midnight = (current_time == datetime.time(0, 0))
        
        if not is_midnight:
            if (current_time < datetime.time(9, 45) or 
                current_time > datetime.time(14, 30)):
                return
        
        # Volume filter
        if self.data.volume[0] < self.volume_sma[0] * self.params.volume_threshold:
            return
        
        # Current values
        adx_val = self.adx[0]
        di_plus_val = self.di_plus[0]
        di_minus_val = self.di_minus[0]
        
        # Previous values
        di_plus_prev = self.di_plus[-1]
        di_minus_prev = self.di_minus[-1]
        
        # === DETECT CROSSOVERS ===
        # Bullish: DI+ crosses above DI-
        bullish_crossover = (di_plus_prev <= di_minus_prev and di_plus_val > di_minus_val)
        
        # Bearish: DI- crosses above DI+
        bearish_crossover = (di_minus_prev <= di_plus_prev and di_minus_val > di_plus_val)
        
        # === CHECK TREND STRENGTH ===
        is_strong_trend = adx_val > self.params.adx_threshold
        trend_ending = adx_val < 20  # ADX below 20 = no trend
        
        # === ENTRY LOGIC ===
        if not self.position:
            # Long: ADX > threshold AND DI+ crosses above DI-
            if is_strong_trend and bullish_crossover:
                self.buy()
                self.entry_bar = len(self)
                self.entry_price = self.data.close[0]
                self.trend_direction = 1
                
                # Set stop loss
                self.stop_loss = self.entry_price - (self.atr[0] * self.params.atr_stop_mult)
                
                # Set target
                self.target = self.entry_price + (self.atr[0] * self.params.atr_target_mult)
                
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'BUY (ADX bullish) at {self.data.close[0]:.2f} '
                      f'(ADX: {adx_val:.1f}, DI+: {di_plus_val:.1f}, DI-: {di_minus_val:.1f}, '
                      f'Stop: {self.stop_loss:.2f}, Target: {self.target:.2f})')
        
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
            
            # Stop loss hit
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
            
            # Trend ending: ADX drops below 20
            if trend_ending:
                self.sell()
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'SELL (Trend ending) at {self.data.close[0]:.2f}')
                self.entry_bar = None
                return
            
            # DI- crosses above DI+ (trend reversal)
            if bearish_crossover:
                self.sell()
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'SELL (DI- crossover) at {self.data.close[0]:.2f}')
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
    from backtesting.backtest_runner import BacktestRunner

    runner = BacktestRunner(initial_cash=5000000)
    runner.load_data('path/to/daily/data.csv', 'RELIANCE')
    runner.add_strategy(ADXTrendStrategy)
    runner.add_analyzers()
    result = runner.run()
    metrics = runner.get_metrics(result)
    print(f"Sharpe: {metrics['sharpe_ratio']}")
    print(f"Return: {metrics['returns']['total_return']:.2%}")
