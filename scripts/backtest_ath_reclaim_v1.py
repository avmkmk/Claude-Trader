#!/usr/bin/env python3
"""
Single-symbol backtest runner for ATH Reclaim Strategy V1

Usage:
    python scripts/backtest_ath_reclaim_v1.py --symbol RELIANCE
    python scripts/backtest_ath_reclaim_v1.py --symbol TCS --start-date 2020-01-01 --end-date 2023-12-31
"""
import argparse
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backtesting.backtest_runner import BacktestRunner
from strategies.ath_reclaim_daily_v1 import ATHReclaimStrategy


def run_backtest(symbol, start_date=None, end_date=None, verbose=True):
    """
    Run backtest for a single symbol

    Args:
        symbol: Stock symbol (e.g., 'RELIANCE')
        start_date: Optional start date 'YYYY-MM-DD'
        end_date: Optional end date 'YYYY-MM-DD'
        verbose: Print strategy logs

    Returns:
        dict with metrics or None if failed
    """
    # Historical data path (eod2 format)
    # Note: Files are lowercase in eod2 directory
    # Path is in: D:\Professional Journey\Personal Software Projects\historical_Indian_equity_data
    base_path = Path('D:/Professional Journey/Personal Software Projects/historical_Indian_equity_data')
    data_path = base_path / 'daily' / 'eod2' / f'{symbol.lower()}.csv'

    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}")
        return None

    try:
        # Initialize backtest runner with 50 lakhs starting capital
        runner = BacktestRunner(initial_cash=5000000)

        # Load data (with optional date filtering)
        if start_date or end_date:
            runner.load_eod2_data_filtered(
                str(data_path),
                symbol,
                start_date=start_date,
                end_date=end_date
            )
        else:
            runner.load_eod2_data(str(data_path), symbol)

        # Add strategy
        runner.add_strategy(
            ATHReclaimStrategy,
            verbose=verbose,
            ema_period=200,
            gap_tolerance=0.001,
            position_pct=0.10
        )

        # Add analyzers
        runner.add_analyzers()

        # Run backtest
        print(f"\n{'='*60}")
        print(f"Running backtest for {symbol}")
        if start_date or end_date:
            print(f"Date range: {start_date or 'earliest'} to {end_date or 'latest'}")
        print(f"{'='*60}\n")

        result = runner.run()

        # Get metrics
        metrics = runner.get_metrics(result)

        # Print summary
        print(f"\n{'='*60}")
        print(f"BACKTEST RESULTS - {symbol}")
        print(f"{'='*60}")

        print(f"\nReturns:")
        print(f"  Total Return:   {metrics['returns'].get('total_return', 0)*100:.2f}%")
        print(f"  Sharpe Ratio:   {metrics.get('sharpe_ratio', 'N/A')}")

        print(f"\nDrawdown:")
        print(f"  Max Drawdown:   {metrics['drawdown'].get('max_drawdown', 0):.2f}%")

        print(f"\nTrades:")
        trade_stats = metrics.get('trades', {})
        total_trades = trade_stats.get('total_trades', 0)
        won_trades = trade_stats.get('won_trades', 0)
        lost_trades = trade_stats.get('lost_trades', 0)
        win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0

        print(f"  Total Trades:   {total_trades}")
        print(f"  Won:            {won_trades}")
        print(f"  Lost:           {lost_trades}")
        print(f"  Win Rate:       {win_rate:.1f}%")
        print(f"  Net P&L:        Rs {trade_stats.get('pnl_net_total', 0):,.2f}")
        print(f"  Avg P&L/Trade:  Rs {trade_stats.get('pnl_net_average', 0):,.2f}")

        print(f"\n{'='*60}\n")

        # Return metrics with symbol
        return {
            'symbol': symbol,
            'total_return': metrics['returns'].get('total_return', 0),
            'sharpe_ratio': metrics.get('sharpe_ratio'),
            'max_drawdown': metrics['drawdown'].get('max_drawdown', 0),
            'total_trades': total_trades,
            'won_trades': won_trades,
            'lost_trades': lost_trades,
            'win_rate': win_rate,
            'net_pnl': trade_stats.get('pnl_net_total', 0),
            'avg_pnl': trade_stats.get('pnl_net_average', 0),
        }

    except Exception as e:
        print(f"ERROR running backtest for {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Run ATH Reclaim Strategy backtest on a single symbol'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        required=True,
        help='Stock symbol (e.g., RELIANCE)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date YYYY-MM-DD (optional)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date YYYY-MM-DD (optional)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress strategy logs'
    )

    args = parser.parse_args()

    # Run backtest
    result = run_backtest(
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        verbose=not args.quiet
    )

    # Exit with status code
    if result is None:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
