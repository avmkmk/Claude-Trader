"""
ATH Reclaim Strategy - Batch Backtest Runner for NIFTY 500

Runs the ATH Reclaim strategy across NIFTY 500 stocks with daily data.
Generates comprehensive results including trade logs and performance metrics.
"""

import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from backtesting.backtest_runner import BacktestRunner
from strategies.ath_reclaim_daily_v1 import ATHReclaimStrategy


# Configuration
INITIAL_CASH = 1000000  # 10 lakhs starting capital
DATA_DIR = Path(PROJECT_ROOT).parent / "SimpleTraderExternal" / "data" / "daily" / "eod2"
RESULTS_DIR = Path(PROJECT_ROOT).parent / "SimpleTraderExternal" / "backtest_results" / "ath_ema200_reclaim_codex" / datetime.now().strftime("%Y-%m-%d")
STOCK_LISTS_DIR = Path(PROJECT_ROOT).parent / "SimpleTraderExternal" / "data" / "stock_lists"


def get_nifty_500_symbols():
    """
    Get NIFTY 500 stock symbols.

    Since official NIFTY 500 list is not available locally, this function:
    1. Checks if a nifty_500_constituents.csv exists
    2. Falls back to taking first 500 stocks alphabetically from available data

    Returns:
        List of stock symbols
    """
    # Try to load official NIFTY 500 list if it exists
    nifty_500_path = STOCK_LISTS_DIR / "nifty_500_constituents.csv"

    if nifty_500_path.exists():
        df = pd.read_csv(nifty_500_path)
        symbols = df['Symbol'].tolist() if 'Symbol' in df.columns else df.iloc[:, 0].tolist()
        print(f"Loaded {len(symbols)} symbols from NIFTY 500 list")
        return symbols

    # Fallback: Get first 500 stocks from available data
    print("NIFTY 500 list not found. Using first 500 stocks from available data...")

    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Data directory not found: {DATA_DIR}")

    all_files = sorted([f.stem for f in DATA_DIR.glob("*.csv")])
    symbols = all_files[:500]

    print(f"Selected {len(symbols)} symbols from available data")
    return symbols


def run_single_backtest(symbol, verbose=False):
    """
    Run backtest for a single symbol.

    Args:
        symbol: Stock symbol
        verbose: Print trade logs

    Returns:
        Dictionary with backtest results, or None if failed
    """
    try:
        csv_path = DATA_DIR / f"{symbol}.csv"

        if not csv_path.exists():
            print(f"  WARN - Data file not found: {symbol}")
            return None

        # Initialize backtest runner
        runner = BacktestRunner(initial_cash=INITIAL_CASH)

        # Load data
        runner.load_eod2_data(str(csv_path), symbol)

        # Add strategy (verbose only for selected stocks)
        runner.add_strategy(ATHReclaimStrategy, verbose=verbose)

        # Add analyzers
        runner.add_analyzers()

        # Run backtest (suppress output)
        import io
        import contextlib

        with contextlib.redirect_stdout(io.StringIO()):
            result = runner.run()

        # Extract metrics
        metrics = runner.get_metrics(result)
        final_value = runner.cerebro.broker.getvalue()

        # Calculate returns
        total_return = ((final_value - INITIAL_CASH) / INITIAL_CASH) * 100

        # Extract trade stats
        trades = metrics.get('trades', {})
        total_trades = trades.get('total_trades', 0)
        won_trades = trades.get('won_trades', 0)
        lost_trades = trades.get('lost_trades', 0)
        win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0

        pnl_net = trades.get('pnl_net_total', 0)
        pnl_avg = trades.get('pnl_net_average', 0)

        sharpe = metrics.get('sharpe_ratio')
        max_dd = metrics.get('drawdown', {}).get('max_drawdown')

        return {
            'symbol': symbol,
            'initial_cash': INITIAL_CASH,
            'final_value': final_value,
            'total_return_pct': round(total_return, 2),
            'total_trades': total_trades,
            'won_trades': won_trades,
            'lost_trades': lost_trades,
            'win_rate_pct': round(win_rate, 2),
            'net_pnl': round(pnl_net, 2),
            'avg_pnl': round(pnl_avg, 2),
            'sharpe_ratio': round(sharpe, 3) if sharpe else None,
            'max_drawdown_pct': round(max_dd, 2) if max_dd else None,
        }

    except Exception as e:
        print(f"  ERROR - {symbol}: {str(e)}")
        return None


def run_batch_backtest():
    """
    Run batch backtest across all NIFTY 500 stocks.
    """
    print("=" * 80)
    print("ATH RECLAIM STRATEGY - NIFTY 500 BATCH BACKTEST")
    print("=" * 80)
    print(f"\nInitial Capital: Rs {INITIAL_CASH:,}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Results Directory: {RESULTS_DIR}")
    print()

    # Create results directory
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Get symbols
    symbols = get_nifty_500_symbols()
    total_symbols = len(symbols)

    print(f"\nRunning backtests for {total_symbols} symbols...")
    print("-" * 80)

    # Run backtests
    results = []
    successful = 0
    failed = 0

    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{total_symbols}] {symbol}...", end=" ")

        result = run_single_backtest(symbol, verbose=False)

        if result:
            results.append(result)
            successful += 1

            # Show quick stats
            trades = result['total_trades']
            return_pct = result['total_return_pct']
            win_rate = result['win_rate_pct']

            print(f"OK - {trades} trades | {return_pct:+.2f}% return | {win_rate:.1f}% win rate")
        else:
            failed += 1

    print("-" * 80)
    print(f"\nCompleted: {successful} successful, {failed} failed")

    # Convert to DataFrame
    if not results:
        print("No results to save!")
        return

    df = pd.DataFrame(results)

    # Sort by total return
    df = df.sort_values('total_return_pct', ascending=False)

    # Save detailed results
    results_file = RESULTS_DIR / "ath_reclaim_nifty500_detailed_results.csv"
    df.to_csv(results_file, index=False)
    print(f"\nDetailed results saved to: {results_file}")

    # Generate summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    profitable = df[df['total_return_pct'] > 0]
    losing = df[df['total_return_pct'] < 0]
    breakeven = df[df['total_return_pct'] == 0]

    print(f"\nPerformance Distribution:")
    print(f"  Profitable stocks: {len(profitable)} ({len(profitable)/len(df)*100:.1f}%)")
    print(f"  Losing stocks: {len(losing)} ({len(losing)/len(df)*100:.1f}%)")
    print(f"  Breakeven stocks: {len(breakeven)} ({len(breakeven)/len(df)*100:.1f}%)")

    print(f"\nReturn Statistics:")
    print(f"  Best return: {df['total_return_pct'].max():.2f}% ({df.iloc[0]['symbol']})")
    print(f"  Worst return: {df['total_return_pct'].min():.2f}% ({df.iloc[-1]['symbol']})")
    print(f"  Average return: {df['total_return_pct'].mean():.2f}%")
    print(f"  Median return: {df['total_return_pct'].median():.2f}%")

    traded_stocks = df[df['total_trades'] > 0]
    if len(traded_stocks) > 0:
        print(f"\nTrading Activity:")
        print(f"  Stocks with trades: {len(traded_stocks)} ({len(traded_stocks)/len(df)*100:.1f}%)")
        print(f"  Total trades: {df['total_trades'].sum()}")
        print(f"  Average trades per stock: {df['total_trades'].mean():.1f}")
        print(f"  Average win rate: {traded_stocks['win_rate_pct'].mean():.1f}%")

    # Top 10 performers
    print(f"\nTop 10 Performers:")
    print(df[['symbol', 'total_return_pct', 'total_trades', 'win_rate_pct', 'sharpe_ratio']].head(10).to_string(index=False))

    # Bottom 10 performers
    print(f"\nBottom 10 Performers:")
    print(df[['symbol', 'total_return_pct', 'total_trades', 'win_rate_pct', 'sharpe_ratio']].tail(10).to_string(index=False))

    # Save summary
    summary = {
        'total_stocks': len(df),
        'profitable_stocks': len(profitable),
        'losing_stocks': len(losing),
        'breakeven_stocks': len(breakeven),
        'best_return_pct': df['total_return_pct'].max(),
        'worst_return_pct': df['total_return_pct'].min(),
        'avg_return_pct': df['total_return_pct'].mean(),
        'median_return_pct': df['total_return_pct'].median(),
        'stocks_with_trades': len(traded_stocks),
        'total_trades': df['total_trades'].sum(),
        'avg_win_rate_pct': traded_stocks['win_rate_pct'].mean() if len(traded_stocks) > 0 else 0,
    }

    summary_file = RESULTS_DIR / "ath_reclaim_nifty500_summary.csv"
    pd.DataFrame([summary]).to_csv(summary_file, index=False)
    print(f"\nSummary saved to: {summary_file}")

    print("\n" + "=" * 80)
    print("BACKTEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    run_batch_backtest()
