"""
EMA Crossover Strategy with 200 SMA Macro Filter

Strategy Logic:
- BUY when fast EMA (9) crosses above slow EMA (20) AND price > 200 SMA (macro filter)
- SELL when fast EMA crosses below slow EMA OR ATR trailing stop hit

Best Market Conditions: Trending markets (upward)
Timeframe: 15-min to Daily
Win Rate Target: 50-60%
Risk:Reward: 1:2 to 1:3

Reference: Strategy 1 from docs/Indian Equity Algo Trading Strategies.md
"""

import backtrader as bt
import datetime


class EMACrossoverStrategy(bt.Strategy):
    """
    EMA Crossover with 200 SMA Macro Filter
    
    A trend-following strategy that:
    - Uses 9-period EMA as fast signal
    - Uses 20-period EMA as slow baseline
    - Filters signals with 200-period SMA (macro trend filter)
    - Uses ATR for trailing stop loss
    
    Entry Rules:
    - Long: 9 EMA crosses above 20 EMA AND price > 200 SMA
    
    Exit Rules:
    - 9 EMA crosses below 20 EMA, OR
    - ATR trailing stop hit
    """

    params = (
        ('fast_ema_period', 9),       # Fast EMA period (signal line)
        ('slow_ema_period', 20),      # Slow EMA period (baseline)
        ('sma_period', 200),          # 200-period SMA for macro filter
        ('atr_period', 14),           # ATR period for stops
        ('atr_stop_mult', 2.0),       # ATR multiplier for stop loss
        ('atr_target_mult', 3.0),     # ATR multiplier for target
        ('max_hold_bars', 120),       # Maximum hold time in bars
    )

    def __init__(self):
        """Initialize indicators."""
        
        # Fast EMA (signal line)
        self.fast_ema = bt.indicators.EMA(
            self.data.close,
            period=self.params.fast_ema_period
        )
        
        # Slow EMA (baseline)
        self.slow_ema = bt.indicators.EMA(
            self.data.close,
            period=self.params.slow_ema_period
        )
        
        # 200-period SMA for macro trend filter
        self.sma_200 = bt.indicators.SimpleMovingAverage(
            self.data.close,
            period=self.params.sma_period
        )
        
        # EMA Crossover indicator
        self.ema_crossover = bt.indicators.CrossOver(
            self.fast_ema,
            self.slow_ema
        )
        
        # ATR for stop loss and target
        self.atr = bt.indicators.ATR(
            self.data,
            period=self.params.atr_period
        )
        
        # Track entry details
        self.entry_bar = None
        self.entry_price = None
        self.stop_loss = None
        self.target = None
        
        # Track if in trend (price > 200 SMA)
        self.in_trend = False

    def next(self):
        """
        Trading logic called for each candle.
        
        Implements:
        - Time filter: 9:45 AM - 2:30 PM IST (liquid trading hours)
        - Macro filter: Only trade when price > 200 SMA
        - Entry: EMA bullish crossover in uptrend
        - Exit: EMA bearish crossover or stop/target hit
        """
        
        # Time filter: Only trade during liquid hours (9:45 AM - 2:30 PM IST)
        current_time = self.data.datetime.time()
        if (current_time < datetime.time(9, 45) or 
            current_time > datetime.time(14, 30)):
            return
        
        # Update trend status (price above 200 SMA)
        self.in_trend = self.data.close[0] > self.sma_200[0]
        
        # === ENTRY LOGIC ===
        if not self.position:
            # Check for bullish EMA crossover
            # Fast EMA crosses above Slow EMA
            bullish_crossover = self.ema_crossover > 0
            
            # Macro filter: Only trade in uptrend (price > 200 SMA)
            if bullish_crossover and self.in_trend:
                # Enter long position
                self.buy()
                self.entry_bar = len(self)
                self.entry_price = self.data.close[0]
                
                # Set stop loss (ATR-based, below entry)
                self.stop_loss = self.entry_price - (self.atr[0] * self.params.atr_stop_mult)
                
                # Set target (ATR-based, above entry)
                self.target = self.entry_price + (self.atr[0] * self.params.atr_target_mult)
                
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'BUY at {self.data.close[0]:.2f} '
                      f'(Fast EMA: {self.fast_ema[0]:.2f}, Slow EMA: {self.slow_ema[0]:.2f}, '
                      f'200 SMA: {self.sma_200[0]:.2f}, '
                      f'Stop: {self.stop_loss:.2f}, Target: {self.target:.2f})')
        
        # === EXIT LOGIC ===
        else:
            # Time-based exit: Max hold time exceeded
            bars_held = len(self) - self.entry_bar
            if bars_held >= self.params.max_hold_bars:
                self.sell()
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'SELL (Time exit) at {self.data.close[0]:.2f}')
                return
            
            # Stop loss hit
            if self.data.close[0] <= self.stop_loss:
                self.sell()
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'SELL (Stop loss) at {self.data.close[0]:.2f}')
                return
            
            # Target hit
            if self.data.close[0] >= self.target:
                self.sell()
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'SELL (Target) at {self.data.close[0]:.2f}')
                return
            
            # Signal-based exit: EMA bearish crossover
            if self.ema_crossover < 0:
                self.sell()
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'SELL (EMA cross down) at {self.data.close[0]:.2f}')

    def notify_order(self, order):
        """Log order executions."""
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'  -> BUY EXECUTED at {order.executed.price:.2f}')
            elif order.issell():
                print(f'  -> SELL EXECUTED at {order.executed.price:.2f}')

    def notify_trade(self, trade):
        """Log trade results when closed."""
        if trade.isclosed:
            print(f'  -> TRADE CLOSED: P&L = Rs {trade.pnl:.2f} '
                  f'({trade.pnlcomm:.2f} after commission)')


# === USAGE EXAMPLE ===
if __name__ == '__main__':
    """
    Example of how to use this strategy
    
    To run:
    1. First scrape data: python scripts/scrape_initial_stocks.py
    2. Then run backtest:
    
    from backtesting.backtest_runner import BacktestRunner
    from strategies.ema_crossover import EMACrossoverStrategy
    
    runner = BacktestRunner(initial_cash=100000)
    runner.load_data('data/RELIANCE_2026-03-27_14-45-30/daily.csv', 'RELIANCE')
    runner.add_strategy(EMACrossoverStrategy)
    runner.add_analyzers()
    result = runner.run()
    metrics = runner.get_metrics(result)
    print(f"Sharpe: {metrics['sharpe_ratio']}")
    print(f"Return: {metrics['returns']['total_return']:.2%}")
    print(f"Max DD: {metrics['drawdown']['max_drawdown']:.2f}%")
    """
    print("EMA Crossover Strategy loaded.")
    print("Usage: from strategies.ema_crossover import EMACrossoverStrategy")
