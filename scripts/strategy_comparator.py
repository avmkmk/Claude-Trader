import importlib.util
import sys
import pandas as pd
import tempfile
import os
from pathlib import Path

# Assume BacktestRunner is available in the execution environment
from backtesting.backtest_runner import BacktestRunner

def format_metric(value, metric_type='float', decimal_places=2):
    """Format metric value for display."""
    if value is None or pd.isna(value):
        return "N/A"
    
    if metric_type == 'percent':
        return f"{float(value)*100:.{decimal_places}f}%"
    else:
        return f"{float(value):.{decimal_places}f}"

def run_strategy_comparison(
    symbol: str,
    data_path_template: str,
    strategy_module_path: str,
    strategy_class_name: str,
    intervals: list[str],
    strategy_params: dict,
    initial_cash: float = 5000000,
    commission: float = 0.001
):
    """
    Runs backtests for a given strategy across multiple intervals and prints a summary.

    Args:
        symbol (str): The trading symbol (e.g., 'HDFCBANK').
        data_path_template (str): Template for data file paths. Use '{symbol}' and '{interval}'.
                                  Example: 'data/{symbol}_{interval}_365days.csv'.
        strategy_module_path (str): Path to the Python file containing the strategy class.
        strategy_class_name (str): The name of the strategy class to instantiate.
        intervals (list[str]): List of intervals to test (e.g., ['15m', '1h', '4h', '1d']).
        strategy_params (dict): Parameters to pass to the strategy class.
        initial_cash (float): Initial cash for the backtester.
        commission (float): Commission rate for trades.
    """
    print("" + "=" * 100)
    print(f"STRATEGY COMPARISON: {strategy_class_name} for {symbol}")
    print("=" * 100)
    print(f"Symbol: {symbol}")
    print(f"Strategy Parameters: {strategy_params}")
    print(f"Capital: Rs. {initial_cash:,.2f}")
    print(f"Commission: {commission}")
    print(f"Data Path Template: {data_path_template}")
    print("")

    results = {}
    
    # Dynamically load the strategy class
    try:
        # Add the directory of the strategy module to sys.path if not already present
        strategy_dir = os.path.dirname(strategy_module_path)
        if strategy_dir not in sys.path:
            sys.path.insert(0, strategy_dir)

        # Import the module
        spec = importlib.util.spec_from_file_location("strategy_module", strategy_module_path)
        strategy_module = importlib.util.module_from_spec(spec)
        sys.modules['strategy_module'] = strategy_module  # Register in sys.modules for backtrader
        spec.loader.exec_module(strategy_module)
        
        # Get the class
        StrategyClass = getattr(strategy_module, strategy_class_name)
        print(f"Successfully loaded strategy '{strategy_class_name}' from '{strategy_module_path}'")

    except FileNotFoundError:
        print(f"ERROR: Strategy module not found at {strategy_module_path}")
        return
    except AttributeError:
        print(f"ERROR: Strategy class '{strategy_class_name}' not found in {strategy_module_path}")
        return
    except Exception as e:
        print(f"ERROR loading strategy: {e}")
        return

    for interval in intervals:
        print(f"[{interval}] ", end="", flush=True)

        # Construct data file path
        data_filepath = data_path_template.format(symbol=symbol, interval=interval)
        
        if not os.path.exists(data_filepath):
            print(f"Data file not found: {data_filepath}")
            results[interval] = None
            continue
        
        print(f"Loading data '{data_filepath}'...", end=" ", flush=True)
        
        try:
            df = pd.read_csv(data_filepath, index_col=0, parse_dates=True)
            if df.empty:
                print("FAILED (empty data)")
                results[interval] = None
                continue
            print(f"OK ({len(df)} rows)", flush=True)

            print("Running backtest...", end=" ", flush=True)
            
            # Use tempfile for the CSV data to avoid issues with in-memory dataframes
            temp_dir = tempfile.gettempdir()
            temp_csv_path = os.path.join(temp_dir, f"{symbol}_{interval}_temp.csv")
            df.to_csv(temp_csv_path)

            runner = BacktestRunner(initial_cash=initial_cash)
            runner.load_data(temp_csv_path, symbol)
            
            # Add the dynamically loaded strategy
            runner.add_strategy(StrategyClass, **strategy_params)
            runner.add_analyzers()
            
            strategy_result = runner.run()
            metrics = runner.get_metrics(strategy_result)
            
            # Clean up temporary file
            if os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)
            
            results[interval] = {
                'data_rows': len(df),
                'data_start': df.index[0],
                'data_end': df.index[-1],
                'metrics': metrics
            }
            
            total_trades = metrics.get('trades', {}).get('total_trades', 0)
            total_return = metrics.get('returns', {}).get('total_return', 0)
            sharpe = metrics.get('sharpe_ratio', 0)
            max_dd = metrics.get('drawdown', {}).get('max_drawdown', 0)
            
            print("OK")
            print(f"    Trades: {int(total_trades)}, Return: {format_metric(total_return, 'percent')}, "
                  f"Sharpe: {format_metric(sharpe)}, MaxDD: {format_metric(max_dd, 'percent')}")
            
        except Exception as e:
            print(f"FAILED ({e})")
            results[interval] = None
            # Clean up temp file if it exists and an error occurred
            if 'temp_csv_path' in locals() and os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)

    # Print Summary
    print("" + "=" * 100)
    print(f"BACKTEST SUMMARY - {symbol} ({strategy_class_name})")
    print("=" * 100 + "")
    
    print(f"{'Interval':<10} {'Trades':<8} {'Return':<12} {'Sharpe':<10} {'MaxDD':<10} {'Win%':<8} {'Status':<10}")
    print("-" * 100)
    
    best_interval = None
    best_sharpe = -999
    
    for interval in intervals:
        result = results.get(interval)
        
        if result is None:
            print(f"{interval:<10} {'—':<8} {'—':<12} {'—':<10} {'—':<10} {'—':<8} {'FAILED':<10}")
            continue
        
        metrics = result['metrics']
        trades = metrics.get('trades', {}).get('total_trades', 0)
        total_return = metrics.get('returns', {}).get('total_return', 0)
        sharpe = metrics.get('sharpe_ratio', 0)
        max_dd = metrics.get('drawdown', {}).get('max_drawdown', 0)
        won = metrics.get('trades', {}).get('won_trades', 0)
        
        win_rate = (won / trades * 100) if trades > 0 else 0
        
        if sharpe and sharpe > best_sharpe:
            best_sharpe = sharpe
            best_interval = interval
        
        return_str = format_metric(total_return, 'percent')
        sharpe_str = format_metric(sharpe)
        dd_str = format_metric(max_dd, 'percent')
        wr_str = f"{win_rate:.1f}%"
        
        status = "OK" if trades > 0 else "NO_TRADES"
        
        print(f"{interval:<10} {int(trades):<8} {return_str:<12} {sharpe_str:<10} {dd_str:<10} {wr_str:<8} {status:<10}")
    
    print("-" * 100)
    
    print("CONCLUSION:")
    if best_interval and best_sharpe > -999:
        print(f"  BEST INTERVAL: {best_interval.upper()} with Sharpe ratio {best_sharpe:.2f}")
        print(f"        Recommended for parameter optimization and live trading")
    
    print("DETAILS:")
    for interval in intervals:
        result = results.get(interval)
        if result is None:
            continue
        
        metrics = result['metrics']
        print(f"{interval.upper()}:")
        
        trades_info = metrics.get('trades', {})
        if trades_info:
            print(f"    Total: {trades_info.get('total_trades', 0)} trades, "
                  f"Won: {trades_info.get('won_trades', 0)}, "
                  f"Lost: {trades_info.get('lost_trades', 0)}")
            if trades_info.get('pnl_net_total'):
                print(f"    P&L: Rs. {trades_info.get('pnl_net_total', 0):,.2f}, "
                      f"Avg: Rs. {trades_info.get('pnl_net_average', 0):,.2f}/trade")
    
    print("" + "=" * 100 + "")
