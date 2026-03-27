#!/usr/bin/env python3
"""
Generic Strategy Comparison CLI

Compares any trading strategy across multiple timeframes for any symbol.
This is the main entry point for backtesting strategies on historical data.

Usage:
    python scripts/compare_strategy.py \
        --symbol <SYMBOL> \
        --strategy-module <PATH> \
        --strategy-class <CLASS_NAME>

Examples:
    # SMA Crossover on HDFCBANK (all timeframes)
    python scripts/compare_strategy.py \
        --symbol HDFCBANK \
        --strategy-module strategies/sma_crossover.py \
        --strategy-class SMACrossoverStrategy

    # RSI Mean Reversion on RELIANCE (custom params)
    python scripts/compare_strategy.py \
        --symbol RELIANCE \
        --strategy-module strategies/rsi_mean_reversion_india.py \
        --strategy-class RSIMeanReversionIndia \
        --strategy-params '{"rsi_period": 21, "rsi_oversold": 25}'

    # Test single timeframe
    python scripts/compare_strategy.py \
        --symbol INFY \
        --strategy-module strategies/sma_crossover.py \
        --strategy-class SMACrossoverStrategy \
        --intervals 1d
"""

import argparse
import sys
import json
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.strategy_comparator import run_strategy_comparison


def main():
    parser = argparse.ArgumentParser(
        description='Compare any strategy across multiple timeframes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # SMA Crossover on HDFCBANK (all timeframes: 15m, 1h, 4h, 1d)
  python scripts/compare_strategy.py \\
    --symbol HDFCBANK \\
    --strategy-module strategies/sma_crossover.py \\
    --strategy-class SMACrossoverStrategy

  # RSI Mean Reversion with custom parameters
  python scripts/compare_strategy.py \\
    --symbol RELIANCE \\
    --strategy-module strategies/rsi_mean_reversion_india.py \\
    --strategy-class RSIMeanReversionIndia \\
    --strategy-params '{"rsi_period": 21, "rsi_oversold": 25}'

  # Test single timeframe only
  python scripts/compare_strategy.py \\
    --symbol INFY \\
    --strategy-module strategies/sma_crossover.py \\
    --strategy-class SMACrossoverStrategy \\
    --intervals 1d

  # Custom capital and commission
  python scripts/compare_strategy.py \\
    --symbol TCS \\
    --strategy-module strategies/sma_crossover.py \\
    --strategy-class SMACrossoverStrategy \\
    --initial-cash 1000000 \\
    --commission 0.0015

Available Strategies:
  - strategies/sma_crossover.py (SMACrossoverStrategy)
  - strategies/rsi_mean_reversion_india.py (RSIMeanReversionIndia)

Data Requirements:
  Data files should be in: scripts/data/{symbol}_365days_{interval}.csv
  Where interval is one of: 15m, 1h, 4h, 1d
"""
    )

    # REQUIRED arguments (no defaults)
    parser.add_argument(
        '--symbol',
        required=True,
        help='Trading symbol (e.g., HDFCBANK, RELIANCE, INFY, TCS)'
    )
    parser.add_argument(
        '--strategy-module',
        required=True,
        help='Path to strategy Python file (e.g., strategies/sma_crossover.py)'
    )
    parser.add_argument(
        '--strategy-class',
        required=True,
        help='Strategy class name (e.g., SMACrossoverStrategy)'
    )

    # OPTIONAL arguments (with sensible defaults)
    parser.add_argument(
        '--intervals',
        nargs='+',
        default=['15m', '1h', '4h', '1d'],
        help='Timeframes to test (default: 15m 1h 4h 1d)'
    )
    parser.add_argument(
        '--strategy-params',
        default='{}',
        help='JSON string of strategy parameters (default: {}). Example: \'{"fast_period": 5}\''
    )
    parser.add_argument(
        '--initial-cash',
        type=float,
        default=5000000.0,
        help='Initial capital in Rs (default: 5000000 = 50 lakhs)'
    )
    parser.add_argument(
        '--commission',
        type=float,
        default=0.001,
        help='Commission rate per trade (default: 0.001 = 0.1%%)'
    )

    args = parser.parse_args()

    # Parse JSON strategy parameters
    try:
        # Handle potential shell quoting issues
        params_str = args.strategy_params
        if params_str.startswith("'") and params_str.endswith("'"):
            params_str = params_str[1:-1]  # Remove outer single quotes

        strategy_params = json.loads(params_str)
    except json.JSONDecodeError as e:
        print(f"\nERROR: Invalid JSON in --strategy-params")
        print(f"Got: {args.strategy_params}")
        print(f"Error: {e}")
        print("\nExample: --strategy-params '{\"fast_period\": 10, \"slow_period\": 30}'")
        sys.exit(1)

    # Build absolute paths
    strategy_module_path = str(PROJECT_ROOT / args.strategy_module)
    data_path_template = str(PROJECT_ROOT / "scripts/data/{symbol}_365days_{interval}.csv")

    # Run strategy comparison
    try:
        run_strategy_comparison(
            symbol=args.symbol,
            data_path_template=data_path_template,
            strategy_module_path=strategy_module_path,
            strategy_class_name=args.strategy_class,
            intervals=args.intervals,
            strategy_params=strategy_params,
            initial_cash=args.initial_cash,
            commission=args.commission
        )
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: Strategy comparison failed")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n[DEBUG] Strategy comparison completed successfully")


if __name__ == '__main__':
    main()
