"""
NagarajuGunda NSEIndexOptionsData Aggregator
=============================================
Processes Zerodha-format parquet tick data from NagarajuGunda repo.
Aggregates to 5min/15min OHLCV per option contract.

Usage:
    python scripts/fno_data/aggregate_nagaraju.py
    python scripts/fno_data/aggregate_nagaraju.py --year 2023 --symbol NIFTY
    python scripts/fno_data/aggregate_nagaraju.py --year 2023 --symbol BANKNIFTY --validate
"""

import sys
import os
import io
import re
import logging
import argparse
from pathlib import Path

import pandas as pd
import numpy as np

if sys.platform == 'win32' and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SOURCE_DIR = DATA_DIR / "community" / "NSEIndexOptionsData"
FNO_DIR = DATA_DIR / "fno"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def banner(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def is_option_ticker(ticker, symbol):
    """Check if a ticker is an option contract (has strike price)."""
    t = str(ticker).upper()
    if symbol == 'NIFTY':
        # NIFTY options: NIFTY05JAN23C15100 (has C or P followed by digits)
        return bool(re.match(r'^NIFTY\d{2}[A-Z]{3}\d{2}[CP]\d+$', t))
    elif symbol == 'BANKNIFTY':
        # BANKNIFTY options: BANKNIFTY05JAN23C43000
        return bool(re.match(r'^BANKNIFTY\d{2}[A-Z]{3}\d{2}[CP]\d+$', t))
    return False


def parse_option_ticker(ticker):
    """Parse option ticker to extract components.
    
    Format: NIFTY05JAN23C15100
    Returns: {expiry: '2023-01-05', option_type: 'CE', strike: 15100}
    """
    t = str(ticker).upper()
    
    # Find the option type letter (C or P) followed by digits
    match = re.search(r'(\d{2})([A-Z]{3})(\d{2})([CP])(\d+)$', t)
    if not match:
        return None
    
    day, mon, year, opt_type, strike = match.groups()
    
    month_map = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }
    
    full_year = 2000 + int(year)
    month_num = month_map.get(mon, 1)
    
    try:
        expiry = pd.Timestamp(year=full_year, month=month_num, day=int(day))
    except:
        return None
    
    ce_pe = 'CE' if opt_type == 'C' else 'PE'
    
    return {
        'expiry': expiry,
        'option_type': ce_pe,
        'strike': int(strike)
    }


def process_parquet_file(filepath, symbol):
    """Process a single parquet file and return filtered options data."""
    logger.info(f"  Loading {filepath.name}...")
    
    try:
        df = pd.read_parquet(filepath)
    except Exception as e:
        logger.warning(f"  Error reading {filepath}: {e}")
        return None
    
    if df is None or df.empty:
        return None
    
    # Parse datetime
    df['datetime'] = pd.to_datetime(df['Date/Time'], errors='coerce')
    df = df.dropna(subset=['datetime'])
    
    # Filter for option tickers only
    mask = df['Ticker'].apply(lambda x: is_option_ticker(x, symbol))
    filtered = df[mask].copy()
    
    if filtered.empty:
        logger.info(f"    No {symbol} option tickers found")
        return None
    
    # Parse ticker components
    filtered['parsed'] = filtered['Ticker'].apply(parse_option_ticker)
    filtered = filtered.dropna(subset=['parsed'])
    
    # Extract parsed fields
    filtered['expiry'] = filtered['parsed'].apply(lambda x: x['expiry'])
    filtered['option_type'] = filtered['parsed'].apply(lambda x: x['option_type'])
    filtered['strike'] = filtered['parsed'].apply(lambda x: x['strike'])
    
    # Set datetime index
    filtered = filtered.set_index('datetime')
    filtered.index = filtered.index.tz_localize('Asia/Kolkata', ambiguous='NaT', nonexistent='NaT')
    
    # Standardize columns
    filtered = filtered.rename(columns={
        'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close',
        'Volume': 'volume', 'Open Interest': 'open_interest'
    })
    
    filtered = filtered[['Ticker', 'open', 'high', 'low', 'close', 'volume', 'open_interest', 'expiry', 'option_type', 'strike']]
    filtered = filtered.dropna(subset=['open', 'high', 'low', 'close'])
    
    logger.info(f"    {len(filtered):,} option rows, {filtered['Ticker'].nunique()} unique contracts")
    return filtered


def aggregate_contract(df, target_tf='5min'):
    """Aggregate tick data to target timeframe OHLCV."""
    if df is None or df.empty:
        return None
    
    ohlc_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
    }
    if 'volume' in df.columns:
        ohlc_dict['volume'] = 'sum'
    if 'open_interest' in df.columns:
        ohlc_dict['open_interest'] = 'last'
    
    numeric_cols = {k: v for k, v in ohlc_dict.items() if k in df.columns}
    result = df.resample(target_tf).agg(numeric_cols)
    result = result.dropna(subset=['open', 'high', 'low', 'close'])
    return result


def process_year(year, symbol):
    """Process all parquet files for a year - vectorized groupby+resample."""
    year_dir = SOURCE_DIR / str(year) / symbol.lower()
    
    if not year_dir.exists():
        logger.error(f"Directory not found: {year_dir}")
        return
    
    parquet_files = sorted(year_dir.glob('*.parquet'))
    logger.info(f"Found {len(parquet_files)} parquet files for {year}")
    
    for tf_name, tf_freq in [('5min', '5min'), ('15min', '15min')]:
        output_dir = FNO_DIR / 'options' / symbol / tf_name
        output_dir.mkdir(parents=True, exist_ok=True)
    
    for pf in parquet_files:
        logger.info(f"\n  Processing {pf.name}...")
        data = process_parquet_file(pf, symbol)
        
        if data is None or data.empty:
            continue
        
        for tf_name, tf_freq in [('5min', '5min'), ('15min', '15min')]:
            output_dir = FNO_DIR / 'options' / symbol / tf_name
            
            logger.info(f"    Aggregating to {tf_name}...")
            try:
                resampled = data.groupby('Ticker').resample(tf_freq).agg({
                    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last',
                    'volume': 'sum', 'open_interest': 'last',
                    'expiry': 'first', 'option_type': 'first', 'strike': 'first'
                }).reset_index()
                resampled = resampled.dropna(subset=['open', 'high', 'low', 'close'])
            except Exception as e:
                logger.warning(f"    Aggregation error: {e}")
                continue
            
            logger.info(f"    Saving {resampled['Ticker'].nunique()} contracts...")
            saved = 0
            for ticker, group in resampled.groupby('Ticker'):
                if len(group) < 2:
                    continue
                try:
                    exp = group['expiry'].iloc[0]
                    ot = group['option_type'].iloc[0]
                    st = group['strike'].iloc[0]
                    exp_str = exp.strftime('%y%b').upper()
                    fname = f"{symbol}{exp_str}{st}{ot}_{tf_name}.csv"
                    g = group.set_index('datetime')[['open', 'high', 'low', 'close', 'volume', 'open_interest']]
                    
                    fpath = output_dir / fname
                    if fpath.exists():
                        existing = pd.read_csv(fpath, index_col=0, parse_dates=True)
                        combined = pd.concat([existing, g])
                        combined = combined[~combined.index.duplicated(keep='last')]
                        combined = combined.sort_index()
                        combined.to_csv(fpath)
                    else:
                        g.to_csv(fpath)
                    saved += 1
                except Exception:
                    continue
            
            logger.info(f"    Saved {saved} {tf_name} files")
        
        del data
    
    for tf_name in ['5min', '15min']:
        output_dir = FNO_DIR / 'options' / symbol / tf_name
        files = list(output_dir.glob(f'{symbol}*_{tf_name}.csv'))
        total_size = sum(f.stat().st_size for f in files) / (1024*1024)
        logger.info(f"\n  {tf_name}: {len(files)} contracts, {total_size:.1f} MB")


def main():
    parser = argparse.ArgumentParser(description='Aggregate NagarajuGunda options data')
    parser.add_argument('--year', type=str, default=None,
                       help='Year to process (default: all available)')
    parser.add_argument('--symbol', type=str, default='NIFTY',
                       choices=['NIFTY', 'BANKNIFTY'],
                       help='Symbol to process')
    
    args = parser.parse_args()
    
    banner("NAGARAJUGUNDA OPTIONS AGGREGATOR")
    
    if args.year:
        years = [int(args.year)]
    else:
        # Find available years
        years = []
        for d in sorted(SOURCE_DIR.iterdir()):
            if d.is_dir() and d.name.isdigit():
                years.append(int(d.name))
    
    logger.info(f"Processing {args.symbol} for years: {years}")
    
    for year in years:
        banner(f"{args.symbol} {year}")
        process_year(year, args.symbol)


if __name__ == '__main__':
    main()
