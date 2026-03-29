"""
VSA (Volume Spread Analysis) Breakout Strategy

Strategy Logic:
- Detect "smart money" accumulation/distribution through volume-spread-price relationships
- Entry: High volume + narrow spread + close near high (accumulation) after selling climax
- Exit: Distribution signal OR 2x ATR stop OR 3x ATR target OR time exit
- Timeframe: 15min, 60min
- Target: Win rate 45-55%, R:R 1:2.5

Best Market Conditions: After selling climax / consolidation
Timeframe: 15min, 60min
"""

import backtrader as bt
import datetime


class VSABreakoutStrategy(bt.Strategy):
    """
    Volume Spread Analysis (VSA) Strategy
    
    Detects institutional activity through:
    - Volume: High volume indicates institutional buying/selling
    - Spread: Wide spread = strong move, Narrow spread = weak move
    - Close position: Where price closed relative to range
    
    Entry signals:
    - Accumulation: High volume + narrow spread + close near high
    - After Selling Climax: Previous bar was high volume + wide spread + close near low
    """

    params = (
        ('volume_period', 20),
        ('spread_period', 20),
        ('atr_period', 14),
        ('atr_stop_mult', 2.0),
        ('atr_target_mult', 3.0),
        ('volume_threshold', 1.3),      # Volume must be 1.3x avg
        ('spread_threshold', 0.7),     # Spread must be < 0.7x avg
        ('max_hold_bars', 60),
    )

    def __init__(self):
        """Initialize indicators"""
        
        # Volume indicators
        self.volume_sma = bt.indicators.SimpleMovingAverage(
            self.data.volume,
            period=self.params.volume_period
        )
        
        # Spread (High - Low) / Close as percentage - add small epsilon to avoid division by zero
        self.spread = (self.data.high - self.data.low) / (self.data.close + 0.0001)
        self.spread_sma = bt.indicators.SimpleMovingAverage(
            self.spread,
            period=self.params.spread_period
        )
        
        # Close position: (Close - Low) / (High - Low)
        # 0 = close at low, 1 = close at high - add small epsilon
        self.close_position = (self.data.close - self.data.low) / (self.data.high - self.data.low + 0.0001)
        
        # ATR for stops
        self.atr = bt.indicators.ATR(
            self.data,
            period=self.params.atr_period
        )
        
        # Track entry details
        self.entry_bar = None
        self.entry_price = None
        self.stop_loss = None
        self.target = None
        
        # Track previous bar for selling climax detection
        self.prev_was_selling_climax = False

    def next(self):
        """
        Trading logic called for each candle
        """
        
        # Need enough data
        if len(self) < max(self.params.volume_period, self.params.spread_period) + 2:
            return
        
        # Time filter: Only trade during liquid hours (9:45 AM - 2:30 PM IST)
        current_time = self.data.datetime.time()
        if (current_time < datetime.time(9, 45) or 
            current_time > datetime.time(14, 30)):
            return
        
        # === DETECT SELLING CLIMAX (for next bar) ===
        # Selling climax: High volume + wide spread + close near low
        # Add small epsilon to avoid division by zero
        current_range = self.data.high[0] - self.data.low[0]
        if current_range < 0.0001:
            current_range = 0.0001
            
        current_volume_ratio = self.data.volume[0] / (self.volume_sma[0] + 0.0001)
        current_spread_ratio = self.spread[0] / (self.spread_sma[0] + 0.0001)
        
        is_selling_climax = (
            current_volume_ratio > 1.5 and
            current_spread_ratio > 1.3 and
            self.close_position[0] < 0.3
        )
        
        # === DETECT ACCUMULATION (Entry Signal) ===
        # Accumulation: High volume + narrow spread + close near high
        is_accumulation = (
            current_volume_ratio > self.params.volume_threshold and
            current_spread_ratio < self.params.spread_threshold and
            self.close_position[0] > 0.7
        )
        
        # === ENTRY LOGIC ===
        if not self.position:
            # Entry after selling climax (smart money accumulating)
            if is_accumulation and self.prev_was_selling_climax:
                self.buy()
                self.entry_bar = len(self)
                self.entry_price = self.data.close[0]
                
                # Set stop loss (ATR-based)
                self.stop_loss = self.entry_price - (self.atr[0] * self.params.atr_stop_mult)
                
                # Set target
                self.target = self.entry_price + (self.atr[0] * self.params.atr_target_mult)
                
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'BUY (VSA Accumulation) at {self.data.close[0]:.2f} '
                      f'(Vol: {current_volume_ratio:.1f}x, Spread: {current_spread_ratio:.1f}x, '
                      f'ClosePos: {self.close_position[0]:.1f}, '
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
            
            # Distribution signal: High volume + narrow spread + close near low
            # This indicates smart money distributing (selling)
            is_distribution = (
                current_volume_ratio > self.params.volume_threshold and
                current_spread_ratio < self.params.spread_threshold and
                self.close_position[0] < 0.3
            )
            
            if is_distribution:
                self.sell()
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'SELL (Distribution) at {self.data.close[0]:.2f}')
                self.entry_bar = None
                return
        
        # Update previous bar state for next iteration
        self.prev_was_selling_climax = is_selling_climax

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
    runner.load_data('path/to/15min/data.csv', 'RELIANCE')

    # Add strategy with default parameters
    runner.add_strategy(VSABreakoutStrategy)

    # Or customize:
    # runner.add_strategy(VSABreakoutStrategy,
    #                    volume_threshold=1.5,  # Higher volume confirmation
    #                    atr_target_mult=2.5,
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
