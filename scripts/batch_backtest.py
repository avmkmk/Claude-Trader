#!/usr/bin/env python3
"""
Batch Backtest Script

Runs multiple strategies on multiple stocks, collects results, outputs CSV.

Usage:
    python scripts/batch_backtest.py --strategy SMA_Crossover --stocks RELIANCE HDFCBANK INFY
    python scripts/batch_backtest.py --strategy ALL --stocks 20
    python scripts/batch_backtest.py --strategy RSI_MeanReversion --tune

Output:
    results/batch_backtests_YYYY-MM-DD/STRATEGY/results.csv
"""

import argparse
import sys
import os
import json
import importlib.util
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backtesting.backtest_runner import BacktestRunner

# Data directories
EOD2_DIR = PROJECT_ROOT.parent / "historical_Indian_equity_data" / "daily" / "eod2"
INTRADAY_CORRECTED_DIR = PROJECT_ROOT.parent / "historical_Indian_equity_data" / "intraday" / "corrected"

# Results directory
RESULTS_DIR = PROJECT_ROOT / "results" / "batch_backtests"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Test stock universe
NIFTY_50_STOCKS = [
    "RELIANCE", "HDFCBANK", "INFY", "TCS", "ICICIBANK", "BHARTIARTL", "ITC", 
    "TATASTEEL", "SBIN", "WIPRO", "HINDUNILVR", "LT", "AXISBANK", "KOTAKBANK", 
    "ASIANPAINT", "MARUTI", "BAJFINANCE", "SUNPHARMA", "TITAN", "ULTRACEMCO"
]

PILOT_STOCKS = ["RELIANCE", "HDFCBANK", "INFY", "TATASTEEL", "HINDUNILVR"]

# Strategy registry
STRATEGY_REGISTRY = {
    "SMA_Crossover": {
        "module": "strategies.sma_crossover",
        "class": "SMACrossoverStrategy",
        "params": {"fast_period": 10, "slow_period": 30},
        "data_type": "eod2_daily"
    },
    "EMA_Crossover": {
        "module": "strategies.ema_crossover",
        "class": "EMACrossoverStrategy",
        "params": {"fast_ema_period": 9, "slow_ema_period": 20, "sma_period": 200},
        "data_type": "eod2_daily"
    },
    "RSI_MeanReversion": {
        "module": "strategies.rsi_mean_reversion_india",
        "class": "RSIMeanReversionIndia",
        "params": {"rsi_period": 14, "rsi_oversold": 30, "rsi_exit": 50},
        "data_type": "eod2_daily"
    },
    "MeanReversion_Template": {
        "module": "strategies.templates.mean_reversion_template",
        "class": "MeanReversionStrategy",
        "params": {"rsi_period": 14, "rsi_oversold": 30, "rsi_exit": 50},
        "data_type": "intraday_15min"
    },
    "Momentum_Template": {
        "module": "strategies.templates.momentum_template",
        "class": "MomentumStrategy",
        "params": {"macd_fast": 12, "macd_slow": 26, "macd_signal": 9},
        "data_type": "intraday_15min"
    },
    "Breakout_Template": {
        "module": "strategies.templates.breakout_template",
        "class": "BreakoutStrategy",
        "params": {"channel_period": 20, "volume_threshold": 1.2},
        "data_type": "intraday_15min"
    },
    # Phase 2 New Strategies
    "VWAP_MeanReversion": {
        "module": "strategies.vwap_mean_reversion",
        "class": "VWAPMeanReversionStrategy",
        "params": {"deviation_threshold": 0.02, "rsi_oversold": 40},
        "data_type": "intraday_15min"
    },
    "VSA_Breakout": {
        "module": "strategies.vsa_breakout",
        "class": "VSABreakoutStrategy",
        "params": {"volume_threshold": 1.3, "atr_target_mult": 3.0},
        "data_type": "intraday_15min"
    },
    "NR7_Breakout": {
        "module": "strategies.nr7_breakout",
        "class": "NR7BreakoutStrategy",
        "params": {"nr7_period": 7, "volume_threshold": 1.2},
        "data_type": "intraday_15min"
    },
    # Phase 3 New Strategies
    "Supertrend": {
        "module": "strategies.supertrend_trend",
        "class": "SupertrendTrendStrategy",
        "params": {"supertrend_period": 10, "supertrend_multiplier": 3.0},
        "data_type": "eod2_daily"
    },
    "ADX_Trend": {
        "module": "strategies.adx_trend",
        "class": "ADXTrendStrategy",
        "params": {"adx_period": 14, "adx_threshold": 25},
        "data_type": "eod2_daily"
    },
    "Gap_Trading": {
        "module": "strategies.gap_trading",
        "class": "GapTradingStrategy",
        "params": {"min_gap_pct": 0.01, "max_gap_pct": 0.04},
        "data_type": "eod2_daily"
    }
}

# Default backtest parameters
DEFAULT_START_DATE = "2023-01-01"
DEFAULT_END_DATE = "2026-03-27"
DEFAULT_INITIAL_CASH = 5000000
DEFAULT_COMMISSION = 0.001


def format_metric(value, metric_type='float', decimal_places=2):
    """Format metric value for display."""
    if value is None or pd.isna(value):
        return "N/A"
    if metric_type == 'percent':
        return f"{float(value)*100:.{decimal_places}f}%"
    else:
        return f"{float(value):.{decimal_places}f}"


def load_strategy_class(module_name, class_name):
    """Dynamically load a strategy class."""
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def get_data_path(symbol, data_type):
    """Get the data file path for a symbol and data type."""
    if data_type == "eod2_daily":
        path = EOD2_DIR / f"{symbol.lower()}.csv"
        return str(path) if path.exists() else None
    elif data_type == "intraday_15min":
        path = INTRADAY_CORRECTED_DIR / symbol / "15min" / "15min.csv"
        return str(path) if path.exists() else None
    return None


def run_single_backtest(symbol, strategy_info, params, start_date, end_date, 
                        initial_cash, commission, verbose=False):
    """Run a single backtest and return metrics."""
    
    strategy_module = strategy_info["module"]
    strategy_class_name = strategy_info["class"]
    data_type = strategy_info["data_type"]
    
    # Get data path
    data_path = get_data_path(symbol, data_type)
    if not data_path:
        return {
            "status": "DATA_NOT_FOUND",
            "error": f"Data file not found for {symbol} ({data_type})"
        }
    
    # Load strategy class
    try:
        StrategyClass = load_strategy_class(strategy_module, strategy_class_name)
    except Exception as e:
        return {
            "status": "STRATEGY_LOAD_ERROR",
            "error": f"Failed to load {strategy_class_name}: {e}"
        }
    
    # Create runner
    runner = BacktestRunner(initial_cash=initial_cash)
    runner.cerebro.broker.setcommission(commission=commission)
    
    # Load data
    try:
        if data_type == "eod2_daily":
            runner.load_eod2_data_filtered(data_path, symbol, start_date, end_date)
        else:
            runner.load_data(data_path, symbol)
    except Exception as e:
        return {
            "status": "DATA_LOAD_ERROR",
            "error": f"Failed to load data: {e}"
        }
    
    # Add strategy
    runner.add_strategy(StrategyClass, **params)
    runner.add_analyzers()
    
    # Run backtest
    try:
        strategy_result = runner.run()
    except Exception as e:
        return {
            "status": "BACKTEST_ERROR",
            "error": f"Backtest failed: {e}"
        }
    
    # Get metrics
    try:
        metrics = runner.get_metrics(strategy_result)
    except Exception as e:
        return {
            "status": "METRICS_ERROR",
            "error": f"Failed to get metrics: {e}"
        }
    
    # Extract key metrics
    sharpe = metrics.get('sharpe_ratio')
    total_return = metrics.get('returns', {}).get('total_return', 0)
    max_dd = metrics.get('drawdown', {}).get('max_drawdown', 0)
    trades = metrics.get('trades', {})
    total_trades = trades.get('total_trades', 0)
    won_trades = trades.get('won_trades', 0)
    lost_trades = trades.get('lost_trades', 0)
    win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0
    pnl_total = trades.get('pnl_net_total', 0)
    pnl_avg = trades.get('pnl_net_average', 0)
    
    # Determine status
    if total_trades == 0:
        status = "NO_TRADES"
    elif sharpe is None or sharpe < 0:
        status = "NEGATIVE_SHARPE"
    elif sharpe < 0.5:
        status = "TUNE_NEEDED"
    elif sharpe >= 1.0 and abs(max_dd) < 15:
        status = "OK"
    else:
        status = "ACCEPTABLE"
    
    return {
        "status": status,
        "sharpe_ratio": sharpe,
        "total_return_pct": total_return * 100 if total_return else 0,
        "max_drawdown_pct": max_dd,
        "total_trades": total_trades,
        "won_trades": won_trades,
        "lost_trades": lost_trades,
        "win_rate_pct": win_rate,
        "pnl_total": pnl_total,
        "pnl_avg": pnl_avg,
        "data_path": data_path,
        "data_type": data_type
    }


def run_batch_backtest(strategy_name, symbols, params, start_date, end_date,
                       initial_cash, commission, verbose=False):
    """Run batch backtest for a strategy on multiple stocks."""
    
    print(f"\n{'='*80}")
    print(f"Running batch backtest: {strategy_name}")
    print(f"Stocks: {len(symbols)} | Params: {params}")
    print(f"{'='*80}")
    
    strategy_info = STRATEGY_REGISTRY.get(strategy_name)
    if not strategy_info:
        print(f"ERROR: Unknown strategy: {strategy_name}")
        return []
    
    # Merge params
    full_params = {**strategy_info["params"], **params}
    
    results = []
    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] Testing {symbol}...", end=" ", flush=True)
        
        result = run_single_backtest(
            symbol, strategy_info, full_params,
            start_date, end_date, initial_cash, commission, verbose
        )
        
        result["symbol"] = symbol
        result["strategy"] = strategy_name
        result["strategy_params"] = json.dumps(full_params)
        result["start_date"] = start_date
        result["end_date"] = end_date
        result["initial_cash"] = initial_cash
        
        if result["status"] == "OK":
            print(f"OK - Sharpe: {format_metric(result['sharpe_ratio'])}, "
                  f"Trades: {result['total_trades']}, "
                  f"Return: {format_metric(result['total_return_pct'], 'percent')}")
        elif result["status"] == "NO_TRADES":
            print(f"NO TRADES - Entry conditions not met")
        elif result["status"] == "NEGATIVE_SHARPE":
            print(f"NEGATIVE - Sharpe: {format_metric(result['sharpe_ratio'])}, "
                  f"Trades: {result['total_trades']}")
        elif result["status"] == "TUNE_NEEDED":
            print(f"TUNE - Sharpe: {format_metric(result['sharpe_ratio'])}, "
                  f"Trades: {result['total_trades']}")
        else:
            print(f"{result['status']}")
        
        results.append(result)
    
    return results


def run_parameter_tuning(strategy_name, symbol, base_params, tuning_config,
                        start_date, end_date, initial_cash, commission):
    """Run parameter tuning for a strategy on a single stock."""
    
    print(f"\n{'='*80}")
    print(f"Parameter Tuning: {strategy_name} on {symbol}")
    print(f"Base Params: {base_params}")
    print(f"Tuning Config: {tuning_config}")
    print(f"{'='*80}")
    
    strategy_info = STRATEGY_REGISTRY.get(strategy_name)
    if not strategy_info:
        print(f"ERROR: Unknown strategy: {strategy_name}")
        return []
    
    results = []
    
    # Test base params first
    print(f"\n[BASELINE] Testing default parameters...")
    result = run_single_backtest(
        symbol, strategy_info, base_params,
        start_date, end_date, initial_cash, commission
    )
    result["test_id"] = "BASELINE"
    result["params_tested"] = json.dumps(base_params)
    results.append(result)
    
    # Test each parameter variation
    for param_name, test_values in tuning_config.items():
        for test_value in test_values:
            test_params = base_params.copy()
            test_params[param_name] = test_value
            
            print(f"\n[TUNING] {param_name} = {test_value}...", end=" ", flush=True)
            
            result = run_single_backtest(
                symbol, strategy_info, test_params,
                start_date, end_date, initial_cash, commission
            )
            
            result["test_id"] = f"{param_name}_{test_value}"
            result["params_tested"] = json.dumps(test_params)
            results.append(result)
            
            if result["status"] == "OK":
                print(f"OK - Sharpe: {format_metric(result['sharpe_ratio'])}")
            elif result["status"] == "NO_TRADES":
                print("NO TRADES")
            else:
                print(f"{result['status']} - Sharpe: {format_metric(result['sharpe_ratio'])}")
    
    return results


def save_results_csv(results, strategy_name):
    """Save results to CSV file."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    strategy_dir = RESULTS_DIR / timestamp / strategy_name
    strategy_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = strategy_dir / "results.csv"
    df = pd.DataFrame(results)
    df.to_csv(filepath, index=False)
    
    print(f"\nResults saved to: {filepath}")
    return filepath


def print_summary(results):
    """Print summary of batch results."""
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    # Group by status
    status_counts = {}
    for r in results:
        status = r.get("status", "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\nStatus Distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    # Calculate averages for successful tests
    valid_results = [r for r in results if r.get("sharpe_ratio") is not None]
    if valid_results:
        avg_sharpe = sum(r["sharpe_ratio"] for r in valid_results) / len(valid_results)
        avg_return = sum(r["total_return_pct"] for r in valid_results) / len(valid_results)
        avg_dd = sum(r["max_drawdown_pct"] for r in valid_results) / len(valid_results)
        avg_trades = sum(r["total_trades"] for r in valid_results) / len(valid_results)
        
        print(f"\nAverages (valid tests):")
        print(f"  Sharpe Ratio: {avg_sharpe:.2f}")
        print(f"  Total Return: {avg_return:.2f}%")
        print(f"  Max Drawdown: {avg_dd:.2f}%")
        print(f"  Total Trades: {avg_trades:.1f}")
    
    print(f"{'='*80}")


def main():
    parser = argparse.ArgumentParser(
        description='Batch Backtest Script for SimpleTrader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test SMA Crossover on 5 pilot stocks
  python scripts/batch_backtest.py --strategy SMA_Crossover --stocks PILOT

  # Test all strategies on 5 pilot stocks
  python scripts/batch_backtest.py --strategy ALL --stocks PILOT

  # Test RSI Mean Reversion on 20 Nifty 50 stocks
  python scripts/batch_backtest.py --strategy RSI_MeanReversion --stocks 20

  # Run parameter tuning on RELIANCE
  python scripts/batch_backtest.py --strategy RSI_MeanReversion --tune --symbol RELIANCE

Available Strategies:
  SMA_Crossover, EMA_Crossover, RSI_MeanReversion,
  MeanReversion_Template, Momentum_Template, Breakout_Template

Stock Options:
  PILOT - 5 stocks (RELIANCE, HDFCBANK, INFY, TATASTEEL, HINDUNILVR)
  10 - First 10 Nifty 50 stocks
  20 - All 20 Nifty 50 stocks
  Or specify individual symbols: RELIANCE HDFCBANK INFY
"""
    )
    
    parser.add_argument(
        '--strategy', '-s',
        required=True,
        help='Strategy name or ALL'
    )
    parser.add_argument(
        '--stocks', '-n',
        default='PILOT',
        help='Stock universe: PILOT (5), 10, 20, or space-separated symbols'
    )
    parser.add_argument(
        '--symbol',
        help='Single symbol for tuning'
    )
    parser.add_argument(
        '--tune',
        action='store_true',
        help='Run parameter tuning'
    )
    parser.add_argument(
        '--params', '-p',
        default='{}',
        help='JSON string of additional parameters'
    )
    parser.add_argument(
        '--start-date',
        default=DEFAULT_START_DATE,
        help=f'Start date (default: {DEFAULT_START_DATE})'
    )
    parser.add_argument(
        '--end-date',
        default=DEFAULT_END_DATE,
        help=f'End date (default: {DEFAULT_END_DATE})'
    )
    parser.add_argument(
        '--initial-cash',
        type=float,
        default=DEFAULT_INITIAL_CASH,
        help=f'Initial cash (default: {DEFAULT_INITIAL_CASH})'
    )
    parser.add_argument(
        '--commission',
        type=float,
        default=DEFAULT_COMMISSION,
        help=f'Commission rate (default: {DEFAULT_COMMISSION})'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Parse stock list
    if args.stocks == 'PILOT':
        stocks = PILOT_STOCKS
    elif args.stocks == '10':
        stocks = NIFTY_50_STOCKS[:10]
    elif args.stocks == '20':
        stocks = NIFTY_50_STOCKS
    else:
        stocks = args.stocks.split()
    
    # Parse strategy params
    try:
        extra_params = json.loads(args.params)
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in --params: {args.params}")
        sys.exit(1)
    
    # Parse additional args
    if args.symbol:
        stocks = [args.symbol]
    
    # Run tests
    if args.strategy == "ALL":
        # Run all strategies
        for strategy_name in STRATEGY_REGISTRY.keys():
            results = run_batch_backtest(
                strategy_name, stocks, extra_params,
                args.start_date, args.end_date,
                args.initial_cash, args.commission, args.verbose
            )
            if results:
                save_results_csv(results, strategy_name)
                print_summary(results)
    elif args.tune and args.symbol:
        # Run parameter tuning
        strategy_info = STRATEGY_REGISTRY.get(args.strategy)
        if not strategy_info:
            print(f"ERROR: Unknown strategy: {args.strategy}")
            sys.exit(1)
        
        base_params = strategy_info["params"]
        
        # Define tuning config based on strategy
        tuning_config = {}
        if args.strategy == "RSI_MeanReversion":
            tuning_config = {
                "rsi_oversold": [25, 35, 40],
                "rsi_exit": [45, 55],
                "volume_threshold": [0.5, 0.6, 0.7]
            }
        elif args.strategy == "SMA_Crossover":
            tuning_config = {
                "fast_period": [5, 7, 15, 20],
                "slow_period": [15, 20, 40, 50]
            }
        elif args.strategy == "EMA_Crossover":
            tuning_config = {
                "fast_ema_period": [5, 7, 12],
                "slow_ema_period": [15, 18, 25],
                "atr_stop_mult": [1.5, 2.5]
            }
        
        results = run_parameter_tuning(
            args.strategy, args.symbol, base_params, tuning_config,
            args.start_date, args.end_date, args.initial_cash, args.commission
        )
        
        if results:
            save_results_csv(results, f"{args.strategy}_TUNING")
            print_summary(results)
    else:
        # Run single strategy
        results = run_batch_backtest(
            args.strategy, stocks, extra_params,
            args.start_date, args.end_date,
            args.initial_cash, args.commission, args.verbose
        )
        
        if results:
            save_results_csv(results, args.strategy)
            print_summary(results)


if __name__ == "__main__":
    main()
