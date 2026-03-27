"""
Validate scraped historical data
Usage: python scripts/validate_data.py
"""

import pandas as pd
import os

data_dir = 'data'
symbols = ['RELIANCE', 'INFY', 'HDFCBANK', 'TCS', 'ICICIBANK',
           'BHARTIARTL', 'ITC', 'TATASTEEL', 'SBIN', 'WIPRO']

def main():
    print("Data Validation Report")
    print("=" * 60)

    total_files = 0
    valid_files = 0
    missing_files = 0
    invalid_files = 0

    for symbol in symbols:
        filepath = os.path.join(data_dir, f'{symbol}_365days.csv')

        if not os.path.exists(filepath):
            print(f"❌ {symbol}: FILE MISSING")
            missing_files += 1
            continue

        total_files += 1

        try:
            df = pd.read_csv(filepath, index_col=0, parse_dates=True)

            # Checks
            row_count = len(df)
            has_nulls = df.isnull().any().any()
            required_cols = {'open', 'high', 'low', 'close', 'volume'}
            has_all_cols = required_cols.issubset(set(df.columns))

            if df.index.size > 0:
                date_range = f"{df.index[0].date()} to {df.index[-1].date()}"
            else:
                date_range = "EMPTY"

            # Validation
            is_valid = (240 <= row_count <= 270 and not has_nulls and has_all_cols)

            if is_valid:
                status = "✓"
                valid_files += 1
            else:
                status = "⚠"
                invalid_files += 1

            print(f"{status} {symbol}: {row_count} rows, {date_range}, nulls={has_nulls}, cols_ok={has_all_cols}")

        except Exception as e:
            print(f"❌ {symbol}: ERROR reading file - {str(e)}")
            invalid_files += 1

    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Total symbols checked: {len(symbols)}")
    print(f"  Valid files: {valid_files}")
    print(f"  Invalid/corrupted files: {invalid_files}")
    print(f"  Missing files: {missing_files}")

    if valid_files == len(symbols):
        print(f"\n✓ All data files validated successfully!")
    elif valid_files > 0:
        print(f"\n⚠ Some files have issues - review output above")
    else:
        print(f"\n❌ No valid data files found")

if __name__ == '__main__':
    main()
