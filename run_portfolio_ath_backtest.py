"""
ATH Reclaim Portfolio Backtest with Monthly SIP and Compounding

Implements:
- Starting capital: Rs 50,000
- Monthly injection: Rs 50,000 (first of each month)
- Portfolio allocation across multiple stocks with ATH signals
- Compounding returns
- Exit on close below EMA 200 (existing strategy logic)
"""

import os
import sys
from pathlib import Path
from datetime import datetime, date
import pandas as pd
import backtrader as bt

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from backtesting.capital_manager import CapitalManager


class ATHReclaimPortfolioStrategy(bt.Strategy):
    """
    Portfolio version of ATH Reclaim strategy with CapitalManager integration

    Manages multiple stocks simultaneously with shared capital pool
    """

    params = (
        ('ema_period', 200),
        ('gap_tolerance', 0.001),
        ('position_pct', 0.10),  # 10% per position
        ('starting_cash', 50000),
        ('monthly_injection', 50000),
        ('verbose', True),
    )

    def __init__(self):
        """Initialize indicators and capital manager"""

        # Initialize capital manager
        self.capital_mgr = CapitalManager(
            start_date=self.datas[0].datetime.date(0),
            starting_cash=self.params.starting_cash,
            monthly_injection=self.params.monthly_injection
        )

        # Track indicators per data feed (stock)
        self.emas = {}
        self.ath_values = {}
        self.ath_dates = {}
        self.phases = {}  # 1, 2, or 3
        self.below_ema200_dates = {}
        self.prev_closes = {}
        self.entry_prices = {}
        self.entry_dates = {}

        # Initialize for each stock
        for i, d in enumerate(self.datas):
            self.emas[d] = bt.indicators.ExponentialMovingAverage(
                d.close, period=self.params.ema_period
            )
            self.ath_values[d] = None
            self.ath_dates[d] = None
            self.phases[d] = None
            self.below_ema200_dates[d] = None
            self.prev_closes[d] = None
            self.entry_prices[d] = None
            self.entry_dates[d] = None

        # Monthly injection tracking
        self.last_injection_log_month = None

    def log(self, message):
        """Log with date"""
        if self.params.verbose:
            dt = self.datas[0].datetime.date(0)
            print(f'{dt}: {message}')

    def prenext(self):
        """Called before all indicators have minimum data"""
        # Update capital manager date
        current_date = self.datas[0].datetime.date(0)
        self.capital_mgr.update_date(current_date)

        # Log monthly injections
        current_month = (current_date.year, current_date.month)
        if current_month != self.last_injection_log_month:
            if self.capital_mgr.total_injected > self.params.starting_cash:
                self.log(f'MONTHLY INJECTION: Rs {self.params.monthly_injection:,.0f} | Portfolio: Rs {self.capital_mgr.portfolio_value:,.0f}')
            self.last_injection_log_month = current_month

    def next(self):
        """Process each bar for all stocks"""

        # Update capital manager with current date
        current_date = self.datas[0].datetime.date(0)
        self.capital_mgr.update_date(current_date)

        # Log monthly injections
        current_month = (current_date.year, current_date.month)
        if current_month != self.last_injection_log_month:
            if self.capital_mgr.total_injected > self.params.starting_cash:
                self.log(f'MONTHLY INJECTION: Rs {self.params.monthly_injection:,.0f} | Portfolio: Rs {self.capital_mgr.portfolio_value:,.0f}')
            self.last_injection_log_month = current_month

        # Update broker cash to match capital manager
        self.broker.set_cash(self.capital_mgr.available_cash)

        # Process each stock
        for data in self.datas:
            self._process_stock(data, current_date)

    def _process_stock(self, data, current_date):
        """Process single stock (ATH Reclaim logic)"""

        # Skip if not enough data for EMA
        if len(data) < self.params.ema_period:
            return

        current_close = data.close[0]
        current_high = data.high[0]
        current_open = data.open[0]
        ema_value = self.emas[data][0]

        symbol = data._name

        # Get position for this stock
        position = self.getposition(data)

        # === PHASE 3: ATH Reclaim Entry ===
        if self.phases[data] == 2 and not position:
            if self.ath_values[data] is not None and current_close > self.ath_values[data]:
                # Check for gap up
                if self.prev_closes[data] is not None:
                    gap_up = current_open > (self.prev_closes[data] * (1 + self.params.gap_tolerance))
                    if not gap_up:
                        # Valid entry signal
                        self.phases[data] = 3

                        # Calculate position size using capital manager
                        shares = self.capital_mgr.calculate_position_size(current_close)

                        if shares >= 1:
                            # Execute buy
                            self.buy(data=data, size=shares)
                            self.entry_prices[data] = current_close
                            self.entry_dates[data] = current_date

                            # Update capital manager
                            self.capital_mgr.enter_trade(shares, current_close)

                            self.log(f'BUY {symbol}: {shares} shares @ Rs {current_close:.2f} | Total: Rs {shares * current_close:,.0f} | Cash: Rs {self.capital_mgr.available_cash:,.0f}')

        # === PHASE 1: Track ATH ===
        if self.ath_values[data] is None or current_high > self.ath_values[data]:
            self.ath_values[data] = current_high
            self.ath_dates[data] = current_date
            if self.phases[data] is None or self.phases[data] == 1:
                self.phases[data] = 1

        # === PHASE 2: Below EMA 200 ===
        if self.phases[data] == 1 and current_close < ema_value:
            self.phases[data] = 2
            self.below_ema200_dates[data] = current_date

        # === EXIT LOGIC ===
        if position and current_close < ema_value:
            # Sell position
            self.sell(data=data, size=position.size)

            # Calculate holding period
            hold_days = (current_date - self.entry_dates[data]).days if self.entry_dates[data] else 0

            # Update capital manager
            self.capital_mgr.exit_trade(
                position.size,
                self.entry_prices[data],
                current_close
            )

            # Calculate P&L
            pnl = position.size * (current_close - self.entry_prices[data])
            pnl_pct = (pnl / (position.size * self.entry_prices[data])) * 100

            self.log(f'SELL {symbol}: {position.size} shares @ Rs {current_close:.2f} | P&L: Rs {pnl:,.0f} ({pnl_pct:+.2f}%) | Hold: {hold_days} days | Cash: Rs {self.capital_mgr.available_cash:,.0f}')

            # Reset to Phase 1
            self.phases[data] = 1
            self.entry_prices[data] = None
            self.entry_dates[data] = None

        # Update previous close
        self.prev_closes[data] = current_close

    def notify_order(self, order):
        """Track order execution"""
        if order.status in [order.Completed]:
            if order.isbuy():
                pass  # Already logged in _process_stock
            elif order.issell():
                pass  # Already logged in _process_stock

    def stop(self):
        """Called at end of backtest"""
        final_value = self.capital_mgr.portfolio_value
        total_injected = self.capital_mgr.total_injected
        profit = final_value - total_injected
        profit_pct = (profit / total_injected) * 100

        self.log('=' * 80)
        self.log(f'BACKTEST COMPLETE')
        self.log(f'Total Injected: Rs {total_injected:,.0f}')
        self.log(f'Final Portfolio Value: Rs {final_value:,.0f}')
        self.log(f'Absolute Profit: Rs {profit:,.0f}')
        self.log(f'ROI: {profit_pct:+.2f}%')
        self.log('=' * 80)


def run_portfolio_backtest(symbols, start_date=None, end_date=None):
    """
    Run portfolio backtest with multiple stocks

    Args:
        symbols: List of stock symbols
        start_date: Optional start date 'YYYY-MM-DD'
        end_date: Optional end date 'YYYY-MM-DD'
    """

    DATA_DIR = Path(PROJECT_ROOT).parent / "SimpleTraderExternal" / "data" / "daily" / "eod2"

    print('=' * 80)
    print('ATH RECLAIM PORTFOLIO BACKTEST - MONTHLY SIP + COMPOUNDING')
    print('=' * 80)
    print(f'\nStarting Capital: Rs 50,000')
    print(f'Monthly Injection: Rs 50,000 (first of each month)')
    print(f'Position Size: 10% of portfolio per stock')
    print(f'Exit: Close below EMA 200')
    print(f'\nStocks in Portfolio: {len(symbols)}')
    print(f'Symbols: {", ".join(symbols[:10])}{"..." if len(symbols) > 10 else ""}')
    print('=' * 80)
    print()

    # Initialize Cerebro
    cerebro = bt.Cerebro()

    # Set initial cash (capital manager will handle actual cash)
    cerebro.broker.setcash(50000)
    cerebro.broker.setcommission(commission=0.001)  # 0.1%

    # Load data for each symbol
    loaded_count = 0
    for symbol in symbols:
        csv_path = DATA_DIR / f"{symbol}.csv"

        if not csv_path.exists():
            print(f'Warning: Data not found for {symbol}')
            continue

        try:
            # Load CSV
            df = pd.read_csv(csv_path, parse_dates=['Date'])
            df = df.set_index('Date')

            # Apply date filtering
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]

            # Map columns
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            df.columns = [c.lower() for c in df.columns]
            df = df.dropna()

            if len(df) < 200:
                print(f'Warning: Insufficient data for {symbol} ({len(df)} days)')
                continue

            # Create data feed
            data = bt.feeds.PandasData(
                dataname=df,
                datetime=None,
                open='open',
                high='high',
                low='low',
                close='close',
                volume='volume',
                openinterest=-1
            )

            cerebro.adddata(data, name=symbol)
            loaded_count += 1

        except Exception as e:
            print(f'Error loading {symbol}: {e}')

    print(f'Successfully loaded {loaded_count} stocks')
    print()

    # Add strategy
    cerebro.addstrategy(ATHReclaimPortfolioStrategy, verbose=True)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    # Run
    print('Starting backtest...\n')
    results = cerebro.run()
    strat = results[0]

    # Print analyzer results
    print('\n' + '=' * 80)
    print('PERFORMANCE METRICS')
    print('=' * 80)

    try:
        sharpe = strat.analyzers.sharpe.get_analysis()
        print(f"Sharpe Ratio: {sharpe.get('sharperatio', 'N/A')}")
    except:
        print("Sharpe Ratio: N/A")

    try:
        drawdown = strat.analyzers.drawdown.get_analysis()
        print(f"Max Drawdown: {drawdown.get('max', {}).get('drawdown', 'N/A'):.2f}%")
    except:
        print("Max Drawdown: N/A")

    try:
        trades = strat.analyzers.trades.get_analysis()
        total_trades = trades.get('total', {}).get('closed', 0)
        won = trades.get('won', {}).get('total', 0)
        lost = trades.get('lost', {}).get('total', 0)
        win_rate = (won / total_trades * 100) if total_trades > 0 else 0

        print(f"\nTotal Trades: {total_trades}")
        print(f"Won: {won} | Lost: {lost}")
        print(f"Win Rate: {win_rate:.1f}%")

        pnl_net = trades.get('pnl', {}).get('net', {}).get('total', 0)
        pnl_avg = trades.get('pnl', {}).get('net', {}).get('average', 0)
        print(f"Net P&L: Rs {pnl_net:,.0f}")
        print(f"Avg P&L per trade: Rs {pnl_avg:,.0f}")
    except:
        print("Trade statistics: N/A")

    print('=' * 80)

    return strat


if __name__ == "__main__":
    # Get top performing stocks from previous backtest
    RESULTS_DIR = Path(PROJECT_ROOT).parent / "SimpleTraderExternal" / "backtest_results" / "ath_ema200_reclaim_codex" / "2026-04-13"
    results_file = RESULTS_DIR / "ath_reclaim_nifty500_detailed_results.csv"

    if results_file.exists():
        # Use top 50 performers from previous backtest
        df = pd.read_csv(results_file)
        top_stocks = df.nlargest(50, 'total_return_pct')['symbol'].tolist()
        print(f"Using top 50 stocks from previous backtest results")
    else:
        # Fallback to NIFTY 200
        nifty200_file = Path(PROJECT_ROOT).parent / "SimpleTraderExternal" / "data" / "stock_lists" / "nifty_200_constituents.csv"
        if nifty200_file.exists():
            df = pd.read_csv(nifty200_file)
            top_stocks = df['Symbol'].head(50).tolist()
            print("Using NIFTY 200 top 50 stocks")
        else:
            # Ultimate fallback
            top_stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
                         'BAJFINANCE', 'BHARTIARTL', 'SBIN', 'LT', 'HCLTECH']
            print("Using default top 10 stocks")

    # Run portfolio backtest
    run_portfolio_backtest(top_stocks)
