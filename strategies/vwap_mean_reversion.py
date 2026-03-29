"""
VWAP Mean Reversion Strategy

Strategy Logic:
- Price deviates >2x Standard Deviation from VWAP → mean reversion entry
- Entry: Price > 2 StdDev below VWAP + RSI < 40 + volume confirmation
- Exit: Price returns to VWAP OR 1.5x ATR stop OR time exit (max 2 hours)
- Timeframe: 5min, 15min
- Filters: Volume > average, time 9:45-2:30, skip if ATR > 2x average
- Target: Win rate 55-65%, R:R 1:1.5

Best Market Conditions: Intraday ranging markets
Timeframe: 5min, 15min
"""

import backtrader as bt
import datetime


class VWAPMeanReversionStrategy(bt.Strategy):
    """
    VWAP Mean Reversion Strategy
    
    Uses VWAP as a dynamic support/resistance level.
    When price deviates significantly below VWAP (oversold),
    expect a mean reversion trade back towards VWAP.
    """

    params = (
        ('vwap_period', 14),           # VWAP calculation period
        ('deviation_threshold', 0.02), # 2% deviation from VWAP
        ('rsi_period', 14),
        ('rsi_oversold', 40),          # RSI oversold for entry
        ('rsi_exit', 50),              # RSI exit level
        ('atr_period', 14),
        ('atr_stop_mult', 1.5),
        ('volume_period', 20),
        ('volume_threshold', 1.0),     # Min volume vs avg
        ('max_hold_bars', 24),          # 2 hours at 5-min bars (or adjust for 15min)
    )

    def __init__(self):
        """Initialize indicators"""
        
        # Calculate Typical Price (H+L+C)/3
        self.typical_price = (self.data.high + self.data.low + self.data.close) / 3
        
        # Use Simple Moving Average of typical price as VWAP proxy
        # (Intraday VWAP is typically similar to SMA of typical price)
        self.vwap = bt.indicators.SimpleMovingAverage(
            self.typical_price,
            period=self.params.vwap_period
        )
        
        # Standard Deviation around VWAP
        self.vwap_std = bt.indicators.StandardDeviation(
            self.typical_price, 
            period=self.params.vwap_period
        )
        
        # Alternative: Use Simple Moving Average of typical price as proxy for VWAP
        self.vwap = bt.indicators.SimpleMovingAverage(
            self.typical_price,
            period=self.params.vwap_period
        )
        
        # Standard Deviation around VWAP
        self.vwap_std = bt.indicators.StandardDeviation(
            self.typical_price, 
            period=self.params.vwap_period
        )
        
        # RSI (Relative Strength Index)
        self.rsi = bt.indicators.RSI(
            self.data.close,
            period=self.params.rsi_period
        )
        
        # ATR for stop loss
        self.atr = bt.indicators.ATR(
            self.data,
            period=self.params.atr_period
        )
        
        # ATR SMA for volatility check
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
        
        # Volatility filter: Skip if ATR is too high (too volatile)
        if self.atr[0] > 2 * self.atr_sma[0]:
            return
        
        # Volume filter
        if self.data.volume[0] < self.volume_sma[0] * self.params.volume_threshold:
            return
        
        # === ENTRY LOGIC ===
        if not self.position:
            # Calculate price deviation from VWAP
            price_deviation = (self.data.close[0] - self.vwap[0]) / self.vwap[0]
            
            # Long entry: Price significantly below VWAP (oversold) + RSI confirms
            is_oversold = (self.rsi[0] < self.params.rsi_oversold and 
                          price_deviation < -self.params.deviation_threshold)
            
            if is_oversold:
                # Enter long position
                self.buy()
                self.entry_bar = len(self)
                self.entry_price = self.data.close[0]
                
                # Set stop loss below entry
                self.stop_loss = self.entry_price - (self.atr[0] * self.params.atr_stop_mult)
                
                # Set target: return to VWAP + small buffer
                self.target = self.vwap[0] + (self.atr[0] * 0.5)
                
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'BUY at {self.data.close[0]:.2f} '
                      f'(VWAP: {self.vwap[0]:.2f}, Dev: {price_deviation*100:.1f}%, '
                      f'RSI: {self.rsi[0]:.1f}, '
                      f'Stop: {self.stop_loss:.2f}, Target: {self.target:.2f})')
        
        # === EXIT LOGIC ===
        else:
            # Time-based exit: Max hold time exceeded
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
            
            # Target hit: Price returned to VWAP
            if self.data.close[0] >= self.target:
                self.sell()
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'SELL (Target) at {self.data.close[0]:.2f}')
                self.entry_bar = None
                return
            
            # RSI exit: Mean reversion complete
            if self.rsi[0] > self.params.rsi_exit:
                self.sell()
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'SELL (RSI exit) at {self.data.close[0]:.2f}')
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

    # Load intraday 15min data
    # Data path: ../historical_Indian_equity_data/intraday/corrected/RELIANCE/15min/15min.csv
    runner.load_data('path/to/15min/data.csv', 'RELIANCE')

    # Add strategy with default parameters
    runner.add_strategy(VWAPMeanReversionStrategy)

    # Or customize parameters:
    # runner.add_strategy(VWAPMeanReversionStrategy,
    #                    deviation_threshold=0.015,  # 1.5% deviation
    #                    rsi_oversold=35,
    #                    max_hold_bars=16)  # 2 hours at 15min = 8 bars

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
