"""
RSI Mean Reversion Strategy - Optimized for Indian Equity Markets

Strategy Logic:
- BUY when price is oversold (RSI < 30) AND price touches lower Bollinger Band
- SELL when price returns to mean (RSI > 50) OR price touches upper Bollinger Band
- Confirmation: Volume must be reasonable (>0.8x average) and > 5 lakh daily

Indian Market Adaptations:
- Circuit breaker filter: Skip trading if intraday change > ±4%
- Daily volume filter: Minimum 5 lakh (500,000) shares
- Daily timeframe: max_hold_bars = 5 days (not 60 bars for intraday)
- Removed intraday time filter (9:45-14:30) as we use daily OHLC data

Best Market Conditions: Ranging Nifty 50 large-caps
Timeframe: Daily candles
Win Rate Target: 55-65%
Risk:Reward: 1:1.5 to 1:2
"""

import backtrader as bt


class RSIMeanReversionIndia(bt.Strategy):
    """
    RSI + Bollinger Bands Mean Reversion Strategy
    Optimized for Indian equity markets (NSE/BSE)
    """

    params = (
        ('rsi_period', 14),          # RSI period
        ('rsi_oversold', 30),        # RSI oversold level
        ('rsi_exit', 50),            # RSI exit level (return to mean)
        ('bb_period', 20),           # Bollinger Bands period
        ('bb_std', 2.0),             # Bollinger Bands standard deviation
        ('volume_period', 20),       # Volume moving average period
        ('volume_threshold', 0.8),   # Minimum volume (% of average, stricter for Indian markets)
        ('max_hold_bars', 5),        # Maximum hold time in days (daily candles)
        ('circuit_threshold', 0.04), # Circuit breaker filter (±4%)
        ('min_daily_volume', 500000),# Minimum daily volume (5 lakh)
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
        self.order = None

    def next(self):
        """
        Trading logic called for each daily candle
        """

        # Skip if order pending
        if self.order:
            return

        # INDIAN MARKET FILTER 1: Circuit breaker check
        # Skip if stock moved >±4% intraday (approaching circuit limit)
        intraday_change = abs(
            (self.data.close[0] - self.data.open[0]) / self.data.open[0]
        )
        if intraday_change > self.params.circuit_threshold:
            return  # Skip if approaching circuit limit (±5%)

        # INDIAN MARKET FILTER 2: Daily volume check
        # Skip if volume below 5 lakh (liquidity requirement)
        if self.data.volume[0] < self.params.min_daily_volume:
            return

        # INDIAN MARKET FILTER 3: Volume quality check
        # Skip if volume below threshold relative to average
        if self.data.volume[0] < (self.volume_sma[0] * self.params.volume_threshold):
            return

        # === ENTRY LOGIC ===
        if not self.position:
            # Check for oversold condition + lower BB touch
            if (self.rsi[0] < self.params.rsi_oversold and
                self.data.close[0] <= self.bb.lines.bot[0]):

                # Enter long position
                self.order = self.buy()
                self.entry_bar = len(self)
                self.entry_price = self.data.close[0]

        # === EXIT LOGIC ===
        else:
            # Time-based exit: Max hold time exceeded
            bars_held = len(self) - self.entry_bar
            if bars_held >= self.params.max_hold_bars:
                self.order = self.sell()
                self.entry_bar = None
                self.entry_price = None
                return

            # Target exit conditions
            rsi_exit = self.rsi[0] > self.params.rsi_exit
            bb_exit = self.data.close[0] >= self.bb.lines.top[0]

            if rsi_exit or bb_exit:
                self.order = self.sell()
                self.entry_bar = None
                self.entry_price = None

    def notify_order(self, order):
        """Log order executions"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED: Price={order.executed.price:.2f}, '
                        f'RSI={self.rsi[0]:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED: Price={order.executed.price:.2f}, '
                        f'RSI={self.rsi[0]:.2f}')
            self.order = None

    def notify_trade(self, trade):
        """Log trade results when closed"""
        if trade.isclosed:
            self.log(f'TRADE PROFIT: Net={trade.pnl:.2f}, '
                    f'Commission={trade.commission:.2f}')

    def log(self, txt):
        """Logging function with date"""
        dt = self.data.datetime.date(0)
        print(f'{dt.isoformat()} | {txt}')


# === USAGE EXAMPLE ===
if __name__ == '__main__':
    """
    Example of how to use this strategy with 365-day historical data
    """
    from backtesting.backtest_runner import BacktestRunner

    print("=" * 70)
    print("RSI Mean Reversion Strategy (India) - Backtest")
    print("=" * 70)

    # Create runner with initial capital
    runner = BacktestRunner(initial_cash=100000)

    # Load 365-day historical data
    try:
        runner.load_data('data/RELIANCE_365days.csv', 'RELIANCE')
    except FileNotFoundError:
        print("\nERROR: data/RELIANCE_365days.csv not found")
        print("Please run: python scripts/batch_data_scraper.py")
        print("Or manually scrape data before running this strategy")
        exit(1)

    # Add strategy with default parameters
    runner.add_strategy(RSIMeanReversionIndia)

    # Or customize parameters:
    # runner.add_strategy(RSIMeanReversionIndia,
    #                    rsi_oversold=25,    # More conservative
    #                    rsi_exit=55,        # Hold longer
    #                    max_hold_bars=3)    # Shorter hold

    # Add performance analyzers
    runner.add_analyzers()

    print("\nRunning backtest...\n")

    # Run backtest
    result = runner.run()

    # Get metrics
    metrics = runner.get_metrics(result)

    print("\n" + "=" * 70)
    print("BACKTEST RESULTS - RSI Mean Reversion (India)")
    print("=" * 70)
    print(f"Symbol: RELIANCE")
    print(f"Period: 365 days")
    print(f"Initial Capital: Rs 1,00,000")
    print("-" * 70)

    # Handle None values gracefully
    sharpe = metrics.get('sharpe_ratio')
    total_return = metrics.get('returns', {}).get('total_return')
    max_dd = metrics.get('drawdown', {}).get('max_drawdown')

    sharpe_str = f"{sharpe:.2f}" if sharpe is not None else 'N/A'
    return_str = f"{total_return:.2%}" if total_return is not None else 'N/A'
    dd_str = f"{max_dd:.2f}" if max_dd is not None else 'N/A'

    print(f"Sharpe Ratio:     {sharpe_str}")
    print(f"Total Return:     {return_str}")
    print(f"Max Drawdown:     {dd_str}%")
    print(f"Total Trades:     {metrics.get('trades', {}).get('total_trades', 0)}")
    print(f"Won Trades:       {metrics.get('trades', {}).get('won_trades', 0)}")
    print(f"Lost Trades:      {metrics.get('trades', {}).get('lost_trades', 0)}")

    total_trades = metrics.get('trades', {}).get('total_trades', 0)
    if total_trades > 0:
        won_trades = metrics.get('trades', {}).get('won_trades', 0)
        win_rate = won_trades / total_trades
        print(f"Win Rate:         {win_rate:.1%}")

        pnl_total = metrics.get('trades', {}).get('pnl_net_total')
        pnl_avg = metrics.get('trades', {}).get('pnl_net_average')
        pnl_total_str = f"{pnl_total:.2f}" if pnl_total is not None else 'N/A'
        pnl_avg_str = f"{pnl_avg:.2f}" if pnl_avg is not None else 'N/A'
        print(f"Net P&L:          Rs {pnl_total_str}")
        print(f"Avg P&L/Trade:    Rs {pnl_avg_str}")
    print("=" * 70)

    # Success criteria check
    print("\nSuccess Criteria (Phase 1):")
    success_checks = []

    sharpe = metrics.get('sharpe_ratio')
    if sharpe is not None and sharpe >= 0.5:
        print("[PASS] Sharpe Ratio > 0.5")
        success_checks.append(True)
    else:
        sharpe_str = f"{sharpe:.2f}" if sharpe is not None else "N/A"
        print(f"[FAIL] Sharpe Ratio < 0.5 (got {sharpe_str})")
        success_checks.append(False)

    total_trades = metrics.get('trades', {}).get('total_trades', 0)
    if total_trades >= 20:
        print(f"[PASS] Total Trades >= 20 (got {total_trades})")
        success_checks.append(True)
    else:
        print(f"[FAIL] Total Trades < 20 (got {total_trades})")
        success_checks.append(False)

    max_dd = metrics.get('drawdown', {}).get('max_drawdown')
    if max_dd is not None and abs(max_dd) < 20:
        print(f"[PASS] Max Drawdown < 20% (got {abs(max_dd):.2f}%)")
        success_checks.append(True)
    else:
        dd_str = f"{abs(max_dd):.2f}" if max_dd is not None else "N/A"
        print(f"[FAIL] Max Drawdown >= 20% (got {dd_str}%)")
        success_checks.append(False)

    if all(success_checks):
        print("\n[PASS] Phase 1 SUCCESS: Strategy validation passed!")
    else:
        print("\n[WARN] Phase 1 PARTIAL: Some criteria not met - may need parameter tuning")

    print("\n" + "=" * 70)

    # Optionally display chart (requires matplotlib)
    # runner.plot()
