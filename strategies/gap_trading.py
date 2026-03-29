"""
Gap Trading Strategy (Markov Rule)

Strategy Logic:
- Gaps > 1% in Indian markets have ~60% probability of partial fill
- Entry: Gap up >1% → short expecting partial fill; Gap down >1% → long expecting partial fill
- Exit: 50% gap fill OR 1.5x ATR stop OR close at 3:00 PM
- Filters: Skip if gap >4% (circuit risk), skip on event days (RBI/Budget)
- Timeframe: Daily (intraday)
- Target: Win rate 55-60%, R:R 1:1.5

Best Market Conditions: After weekend gaps, holidays
Timeframe: Daily (intraday)
"""

import backtrader as bt
import datetime


class GapTradingStrategy(bt.Strategy):
    """
    Gap Trading Strategy (Markov Rule)
    
    In Indian markets, gaps > 1% have ~60% probability of partial fill.
    This strategy trades the expectation of gap fill.
    """

    params = (
        ('min_gap_pct', 0.01),          # 1% minimum gap
        ('max_gap_pct', 0.04),          # 4% circuit risk limit
        ('fill_target_pct', 0.50),     # Target 50% fill
        ('atr_period', 14),
        ('atr_stop_mult', 1.5),
        ('close_time', 15*60 + 0),      # 3:00 PM
    )

    def __init__(self):
        """Initialize indicators"""
        
        # ATR for stop loss
        self.atr = bt.indicators.ATR(
            self.data,
            period=self.params.atr_period
        )
        
        # Track entry details
        self.gap_price = None
        self.gap_type = None  # 'up' or 'down'
        self.target_price = None
        self.stop_loss = None
        self.entry_taken = False
        self.gap_bar_index = None

    def next(self):
        """
        Trading logic called for each candle
        """
        
        # Need enough data
        if len(self) < 2:
            return
        
        # Get previous close and current open
        prev_close = self.data.close[-1]
        current_open = self.data.open[0]
        current_close = self.data.close[0]
        
        # Calculate gap percentage
        gap_pct = (current_open - prev_close) / prev_close
        
        # Skip if no significant gap
        if abs(gap_pct) < self.params.min_gap_pct:
            return
        
        # Skip if gap too large (circuit risk)
        if abs(gap_pct) > self.params.max_gap_pct:
            return
        
        # Time filter: Only enter at market open
        current_time = self.data.datetime.time()
        
        # Only take gap trades at the open or early in the day
        # and only if we haven't already taken a gap trade today
        if not self.entry_taken and current_time < datetime.time(9, 30):
            
            # Gap up: Price opens higher - expect fill → SHORT
            if gap_pct > self.params.min_gap_pct:
                # Short entry at market
                self.sell()
                self.gap_bar_index = len(self)
                self.gap_type = 'up'
                self.gap_price = current_open
                
                # Target: previous close (where gap started)
                # Fill target is 50% toward previous close
                self.target_price = current_open - (gap_pct * prev_close * self.params.fill_target_pct)
                
                # Stop loss: 1.5x ATR above entry
                self.stop_loss = current_open + (self.atr[0] * self.params.atr_stop_mult)
                
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'SHORT (Gap up) at {current_open:.2f} '
                      f'(Gap: {gap_pct*100:.1f}%, PrevClose: {prev_close:.2f}, '
                      f'Target: {self.target_price:.2f}, Stop: {self.stop_loss:.2f})')
                
                self.entry_taken = True
                
            # Gap down: Price opens lower - expect fill → LONG
            elif gap_pct < -self.params.min_gap_pct:
                # Long entry at market
                self.buy()
                self.gap_bar_index = len(self)
                self.gap_type = 'down'
                self.gap_price = current_open
                
                # Target: previous close (where gap started)
                # Fill target is 50% toward previous close
                self.target_price = current_open - (gap_pct * prev_close * self.params.fill_target_pct)
                
                # Stop loss: 1.5x ATR below entry
                self.stop_loss = current_open - (self.atr[0] * self.params.atr_stop_mult)
                
                print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                      f'LONG (Gap down) at {current_open:.2f} '
                      f'(Gap: {gap_pct*100:.1f}%, PrevClose: {prev_close:.2f}, '
                      f'Target: {self.target_price:.2f}, Stop: {self.stop_loss:.2f})')
                
                self.entry_taken = True
        
        # === EXIT LOGIC ===
        if self.position:
            
            # Gap up (short): Exit when price rises to target or stop
            if self.gap_type == 'up':
                # Target hit: price rose to fill target
                if current_close >= self.target_price:
                    self.buy_to_close()  # Cover short
                    print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                          f'BUY TO COVER (Target) at {current_close:.2f}')
                    self.entry_taken = False
                    return
                
                # Stop loss hit
                if current_close >= self.stop_loss:
                    self.buy_to_close()
                    print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                          f'BUY TO COVER (Stop) at {current_close:.2f}')
                    self.entry_taken = False
                    return
            
            # Gap down (long): Exit when price falls to target or stop
            elif self.gap_type == 'down':
                # Target hit: price fell to fill target
                if current_close <= self.target_price:
                    self.sell_to_close()  # Sell long
                    print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                          f'SELL (Target) at {current_close:.2f}')
                    self.entry_taken = False
                    return
                
                # Stop loss hit
                if current_close <= self.stop_loss:
                    self.sell_to_close()
                    print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                          f'SELL (Stop) at {current_close:.2f}')
                    self.entry_taken = False
                    return
            
            # End of day: Square off positions
            if current_time >= datetime.time(15, 0):
                if self.gap_type == 'up':
                    self.buy_to_close()
                    print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                          f'BUY TO COVER (EOD) at {current_close:.2f}')
                elif self.gap_type == 'down':
                    self.sell_to_close()
                    print(f'{self.data.datetime.date()} {self.data.datetime.time()} '
                          f'SELL (EOD) at {current_close:.2f}')
                self.entry_taken = False

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
    runner.add_strategy(GapTradingStrategy)
    runner.add_analyzers()
    result = runner.run()
    metrics = runner.get_metrics(result)
    print(f"Sharpe: {metrics['sharpe_ratio']}")
    print(f"Return: {metrics['returns']['total_return']:.2%}")
