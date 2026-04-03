#!/usr/bin/env python3
"""
Multi-symbol backtest runner for ATH Reclaim Strategy V1

Runs backtests on multiple symbols from a CSV file and aggregates results.

Usage:
    python scripts/backtest_ath_reclaim_multi.py --symbols-file data/nifty_300_valid.csv --output results/ath_reclaim_results.csv
"""
import argparse
import csv
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backtest_ath_reclaim_v1 import run_backtest


def load_symbols(csv_file):
    """Load symbols from CSV file"""
    symbols = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row.get('Symbol', '').strip()
            if symbol:
                symbols.append(symbol)
    return symbols


def aggregate_results(results):
    """
    Aggregate results and determine verdict

    Args:
        results: List of result dicts from run_backtest()

    Returns:
        dict with aggregate metrics and verdict
    """
    if not results:
        return {
            'total_symbols': 0,
            'successful_backtests': 0,
            'profitable': 0,
            'unprofitable': 0,
            'profit_rate': 0.0,
            'verdict': 'NO DATA'
        }

    total = len(results)
    profitable = sum(1 for r in results if r['net_pnl'] > 0)
    unprofitable = total - profitable
    profit_rate = (profitable / total) * 100 if total > 0 else 0

    # Determine verdict
    if profit_rate >= 60:
        verdict = 'SUCCESS'
    elif profit_rate >= 40:
        verdict = 'PROMISE'
    else:
        verdict = 'FAILED'

    # Calculate aggregate metrics
    total_pnl = sum(r['net_pnl'] for r in results)
    avg_pnl = total_pnl / total if total > 0 else 0
    avg_return = sum(r['total_return'] for r in results) / total if total > 0 else 0
    avg_trades = sum(r['total_trades'] for r in results) / total if total > 0 else 0
    avg_win_rate = sum(r['win_rate'] for r in results) / total if total > 0 else 0

    # Sharpe ratios (excluding None values)
    sharpe_values = [r['sharpe_ratio'] for r in results if r['sharpe_ratio'] is not None]
    avg_sharpe = sum(sharpe_values) / len(sharpe_values) if sharpe_values else None

    return {
        'total_symbols': total,
        'successful_backtests': total,
        'profitable': profitable,
        'unprofitable': unprofitable,
        'profit_rate': profit_rate,
        'verdict': verdict,
        'total_pnl': total_pnl,
        'avg_pnl': avg_pnl,
        'avg_return': avg_return,
        'avg_trades': avg_trades,
        'avg_win_rate': avg_win_rate,
        'avg_sharpe': avg_sharpe,
    }


def save_results(results, output_file):
    """Save results to CSV file"""
    # Create output directory if needed
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write results
    fieldnames = [
        'symbol', 'total_return', 'sharpe_ratio', 'max_drawdown',
        'total_trades', 'won_trades', 'lost_trades', 'win_rate',
        'net_pnl', 'avg_pnl'
    ]

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Run ATH Reclaim Strategy backtest on multiple symbols'
    )
    parser.add_argument(
        '--symbols-file',
        type=str,
        required=True,
        help='CSV file with symbols (must have Symbol column)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/ath_reclaim_results.csv',
        help='Output CSV file for results'
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

    args = parser.parse_args()

    # Load symbols
    print(f"Loading symbols from: {args.symbols_file}")
    symbols = load_symbols(args.symbols_file)
    print(f"Found {len(symbols)} symbols")

    if not symbols:
        print("ERROR: No symbols found in CSV file")
        sys.exit(1)

    # Run backtests
    print(f"\n{'='*60}")
    print(f"RUNNING MULTI-SYMBOL BACKTEST")
    print(f"{'='*60}\n")

    results = []
    failed_symbols = []

    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] Processing {symbol}...")

        result = run_backtest(
            symbol=symbol,
            start_date=args.start_date,
            end_date=args.end_date,
            verbose=False  # Suppress logs for multi-symbol runs
        )

        if result:
            results.append(result)
        else:
            failed_symbols.append(symbol)

    # Aggregate results
    agg = aggregate_results(results)

    # Print summary
    print(f"\n{'='*60}")
    print(f"MULTI-SYMBOL BACKTEST SUMMARY")
    print(f"{'='*60}\n")

    print(f"Symbols Tested:     {len(symbols)}")
    print(f"Successful Runs:    {agg['successful_backtests']}")
    print(f"Failed Runs:        {len(failed_symbols)}")

    if failed_symbols:
        print(f"\nFailed Symbols:     {', '.join(failed_symbols)}")

    print(f"\n{'='*60}")
    print(f"PROFITABILITY ANALYSIS")
    print(f"{'='*60}\n")

    print(f"Profitable:         {agg['profitable']} ({agg['profit_rate']:.1f}%)")
    print(f"Unprofitable:       {agg['unprofitable']} ({100 - agg['profit_rate']:.1f}%)")

    print(f"\n{'='*60}")
    print(f"AGGREGATE METRICS")
    print(f"{'='*60}\n")

    print(f"Total P&L:          Rs {agg['total_pnl']:,.2f}")
    print(f"Avg P&L/Symbol:     Rs {agg['avg_pnl']:,.2f}")
    print(f"Avg Return:         {agg['avg_return']*100:.2f}%")
    print(f"Avg Win Rate:       {agg['avg_win_rate']:.1f}%")
    print(f"Avg Trades/Symbol:  {agg['avg_trades']:.1f}")
    if agg['avg_sharpe'] is not None:
        print(f"Avg Sharpe Ratio:   {agg['avg_sharpe']:.2f}")

    print(f"\n{'='*60}")
    print(f"VERDICT: {agg['verdict']}")
    print(f"{'='*60}\n")

    # Interpretation
    print("Interpretation:")
    if agg['verdict'] == 'SUCCESS':
        print("  > 60% profitable = Strategy shows strong promise")
        print("  Proceed to optimization and live testing")
    elif agg['verdict'] == 'PROMISE':
        print("  40-60% profitable = Strategy has potential")
        print("  Consider parameter tuning or filter refinement")
    else:
        print("  < 40% profitable = Strategy needs major revision")
        print("  Re-examine core logic or discard")

    # Save results
    if results:
        save_results(results, args.output)

    # Exit with status based on verdict
    if agg['verdict'] == 'SUCCESS':
        sys.exit(0)
    elif agg['verdict'] == 'PROMISE':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
