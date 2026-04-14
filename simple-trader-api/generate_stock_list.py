#!/usr/bin/env python3
"""
Generate nifty_750.csv from NIFTY 500, Midcap 150, and Smallcap 100 CSVs.

Combines the three index constituent files and deduplicates to create
a master list of 750 stocks for daily data updates.
"""

import pandas as pd
import os

# Input files
input_files = [
    'data/data/MW-NIFTY-500-14-Apr-2026.csv',
    'data/data/MW-NIFTY-MIDCAP-150-14-Apr-2026.csv',
    'data/data/MW-NIFTY-SMALLCAP-100-14-Apr-2026.csv'
]

# Output file
output_file = 'data/nifty_750.csv'

# Collect all symbols
all_symbols = set()

for file_path in input_files:
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found, skipping...")
        continue

    try:
        # Read CSV (handle various encodings and formats)
        df = pd.read_csv(file_path, encoding='utf-8-sig')

        # Find the symbol column (might have different names or formatting)
        symbol_col = None
        for col in df.columns:
            if 'SYMBOL' in col.upper():
                symbol_col = col
                break

        if symbol_col is None:
            print(f"Warning: No SYMBOL column found in {file_path}, skipping...")
            continue

        # Extract symbols and clean them
        symbols = df[symbol_col].dropna().astype(str).str.strip()

        # Filter out empty strings and add to set
        symbols = symbols[symbols != '']
        all_symbols.update(symbols)

        print(f"[OK] Loaded {len(symbols)} symbols from {os.path.basename(file_path)}")

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        continue

# Convert to sorted list
sorted_symbols = sorted(all_symbols)

# Create output DataFrame
output_df = pd.DataFrame({'symbol': sorted_symbols})

# Create output directory if it doesn't exist
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# Save to CSV
output_df.to_csv(output_file, index=False)

print("\n" + "="*60)
print(f"Generated {output_file}")
print(f"Total unique symbols: {len(sorted_symbols)}")
print("="*60)

# Show first and last 10 symbols as verification
print("\nFirst 10 symbols:")
for symbol in sorted_symbols[:10]:
    print(f"  {symbol}")

print("\nLast 10 symbols:")
for symbol in sorted_symbols[-10:]:
    print(f"  {symbol}")

print(f"\nStock list saved to: {output_file}")
