"""
Validate data availability for ATH Reclaim backtest
"""
import os
import pandas as pd
from pathlib import Path


def validate_data_availability(symbols_file, data_dir, min_days=200):
    """
    Check which symbols have sufficient historical data

    Args:
        symbols_file: Path to CSV with Symbol column
        data_dir: Path to daily data directory
        min_days: Minimum days of data required (default 200 for EMA 200)

    Returns:
        dict with 'valid', 'invalid', 'missing' symbol lists
    """
    # Read symbol list
    symbols_df = pd.read_csv(symbols_file)
    symbols = symbols_df['Symbol'].tolist()

    valid = []
    invalid = []
    missing = []

    for symbol in symbols:
        # Data files are in lowercase
        data_path = os.path.join(data_dir, f'{symbol.lower()}.csv')

        if not os.path.exists(data_path):
            missing.append(symbol)
            continue

        try:
            df = pd.read_csv(data_path)
            if len(df) >= min_days:
                valid.append(symbol)
                print(f"[OK] {symbol}: {len(df)} days")
            else:
                invalid.append(symbol)
                print(f"[FAIL] {symbol}: Only {len(df)} days (need {min_days})")
        except Exception as e:
            invalid.append(symbol)
            print(f"[ERROR] {symbol}: {e}")

    print(f"\nSummary:")
    print(f"  Valid: {len(valid)}/{len(symbols)}")
    print(f"  Insufficient data: {len(invalid)}")
    print(f"  Missing files: {len(missing)}")

    return {
        'valid': valid,
        'invalid': invalid,
        'missing': missing
    }


if __name__ == '__main__':
    # Determine paths based on current working directory
    # Handle being run from either the project root or scripts directory
    cwd = os.getcwd()

    # Find the project root (where data/ and scripts/ directories are)
    if os.path.basename(cwd) == 'scripts':
        project_root = os.path.dirname(cwd)
    else:
        project_root = cwd

    symbols_file = os.path.join(project_root, 'data', 'nifty_300_list.csv')

    # Historical data is a sibling to SimpleTrader
    # From .worktrees/ath-reclaim-strategy, go up 3 levels to Personal Software Projects
    psp_root = Path(project_root).parent.parent.parent
    data_dir = os.path.join(psp_root, 'historical_Indian_equity_data', 'daily', 'eod2')

    result = validate_data_availability(symbols_file, data_dir)

    # Save valid symbols for backtest
    if result['valid']:
        valid_df = pd.DataFrame({'Symbol': result['valid']})
        output_file = os.path.join(project_root, 'data', 'nifty_300_valid.csv')
        valid_df.to_csv(output_file, index=False)
        print(f"\n[OK] Saved {len(result['valid'])} valid symbols to {output_file}")
