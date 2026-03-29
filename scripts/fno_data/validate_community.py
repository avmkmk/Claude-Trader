"""
Community Data Validator
========================
Validates community-sourced F&O intraday data against trusted ground truth.
Resamples community intraday to daily and compares OHLCV against yfinance.

Usage:
    python scripts/fno_data/validate_community.py
    python scripts/fno_data/validate_community.py --source banknifty_5min
    python scripts/fno_data/validate_community.py --tolerance 1.0

Validation:
    For each overlapping day:
    - Compare O, H, L, C against ground truth
    - Mark day as "match" if ALL 4 within tolerance
    - Target: >= 90% daily match rate
"""

import sys
import os
import io
import logging
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# ─── Fix Windows encoding ──────────────────────────────────────────────
if sys.platform == 'win32' and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
COMMUNITY_DIR = DATA_DIR / "community"
GROUND_TRUTH_DIR = DATA_DIR / "fno" / "validation" / "ground_truth"
VALIDATION_DIR = DATA_DIR / "fno" / "validation"

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


# ─── Data Loaders ──────────────────────────────────────────────────────

def load_ground_truth(symbol):
    """Load yfinance daily data as ground truth."""
    if symbol == 'NIFTY':
        path = GROUND_TRUTH_DIR / "nifty50_daily.csv"
    elif symbol == 'BANKNIFTY':
        path = GROUND_TRUTH_DIR / "banknifty_daily.csv"
    else:
        raise ValueError(f"Unknown symbol: {symbol}")

    if not path.exists():
        logger.error(f"Ground truth not found: {path}")
        return None

    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True).tz_convert('Asia/Kolkata')
    df.index = df.index.normalize()
    df.index.name = 'datetime'
    logger.info(f"Ground truth {symbol}: {len(df)} days, "
                f"{df.index[0].date()} to {df.index[-1].date()}")
    return df


def load_community_banknifty_5min():
    """Load sandeepkapri BankNifty 5min data."""
    path = COMMUNITY_DIR / "BankNifty-Data" / "bank-nifty-5m-data.csv"
    if not path.exists():
        logger.error(f"Community data not found: {path}")
        return None

    logger.info(f"Loading {path.name}...")
    df = pd.read_csv(path)

    # Parse Date + Time columns
    df['datetime'] = pd.to_datetime(
        df['Date'] + ' ' + df['Time'],
        format='%d-%m-%Y %H:%M:%S',
        errors='coerce'
    )
    df = df.dropna(subset=['datetime'])
    df = df.set_index('datetime')
    df.index = df.index.tz_localize('Asia/Kolkata', ambiguous='NaT', nonexistent='NaT')
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

    # Standardize columns
    df = df.rename(columns={
        'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'
    })
    df = df[['open', 'high', 'low', 'close']]

    logger.info(f"  Loaded: {len(df)} rows, {df.index[0]} to {df.index[-1]}")
    return df


def load_community_banknifty_15min():
    """Load sandeepkapri BankNifty 15min data."""
    path = COMMUNITY_DIR / "BankNifty-Data" / "bank-nifty-15m-data.csv"
    if not path.exists():
        logger.error(f"Community data not found: {path}")
        return None

    logger.info(f"Loading {path.name}...")
    df = pd.read_csv(path)

    df['datetime'] = pd.to_datetime(
        df['Date'] + ' ' + df['Time'],
        format='%d-%m-%Y %H:%M:%S',
        errors='coerce'
    )
    df = df.dropna(subset=['datetime'])
    df = df.set_index('datetime')
    df.index = df.index.tz_localize('Asia/Kolkata', ambiguous='NaT', nonexistent='NaT')
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

    df = df.rename(columns={
        'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'
    })
    df = df[['open', 'high', 'low', 'close']]

    logger.info(f"  Loaded: {len(df)} rows, {df.index[0]} to {df.index[-1]}")
    return df


def load_community_banknifty_1min():
    """Load sandeepkapri BankNifty 1min data."""
    path = COMMUNITY_DIR / "BankNifty-Data" / "bank-nifty-1m-data.csv"
    if not path.exists():
        logger.error(f"Community data not found: {path}")
        return None

    logger.info(f"Loading {path.name} (this is a large file, may take a moment)...")
    df = pd.read_csv(path)

    df['datetime'] = pd.to_datetime(
        df['Date'] + ' ' + df['Time'],
        format='%d-%m-%Y %H:%M:%S',
        errors='coerce'
    )
    df = df.dropna(subset=['datetime'])
    df = df.set_index('datetime')
    df.index = df.index.tz_localize('Asia/Kolkata', ambiguous='NaT', nonexistent='NaT')
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

    df = df.rename(columns={
        'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'
    })
    df = df[['open', 'high', 'low', 'close']]

    logger.info(f"  Loaded: {len(df)} rows, {df.index[0]} to {df.index[-1]}")
    return df


# ─── Resample to Daily ─────────────────────────────────────────────────

def resample_to_daily(df):
    """Resample intraday data to daily OHLCV."""
    if df is None or df.empty:
        return None

    daily = df.resample('D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
    })

    # Drop non-trading days
    daily = daily.dropna(subset=['open', 'high', 'low', 'close'])

    # Filter to weekdays only
    daily = daily[daily.index.weekday < 5]

    logger.info(f"Resampled to daily: {len(daily)} days")
    return daily


# ─── Validation Engine ──────────────────────────────────────────────────

def validate_daily_match(community_daily, ground_truth, tolerance_pct=0.5):
    """
    Compare community daily OHLC against ground truth.

    Returns:
        dict with match statistics
    """
    if community_daily is None or ground_truth is None:
        return {'status': 'error', 'reason': 'missing data'}

    # Align dates (remove timezone for comparison)
    comm_idx = community_daily.index.normalize()
    gt_idx = ground_truth.index.normalize()

    # Find common dates
    common_dates = comm_idx.intersection(gt_idx)

    if len(common_dates) == 0:
        return {'status': 'error', 'reason': 'no overlapping dates'}

    logger.info(f"Overlap period: {common_dates[0].date()} to {common_dates[-1].date()}")
    logger.info(f"Common trading days: {len(common_dates)}")

    tolerance = tolerance_pct / 100.0
    results = {
        'total_days': len(common_dates),
        'matched_days': 0,
        'open_matches': 0,
        'high_matches': 0,
        'low_matches': 0,
        'close_matches': 0,
        'details': [],
        'mismatches': [],
    }

    for date in common_dates:
        # Get community row for this date
        comm_row = community_daily[community_daily.index.normalize() == date]
        gt_row = ground_truth[ground_truth.index.normalize() == date]

        if comm_row.empty or gt_row.empty:
            continue

        c = comm_row.iloc[0]
        g = gt_row.iloc[0]

        day_match = True
        day_details = {'date': str(date.date())}

        for field in ['open', 'high', 'low', 'close']:
            c_val = float(c[field]) if pd.notna(c[field]) else None
            g_val = float(g[field]) if pd.notna(g[field]) else None

            if c_val is None or g_val is None or g_val == 0:
                day_match = False
                day_details[field] = {'status': 'null'}
                continue

            deviation = abs(c_val - g_val) / g_val
            within = deviation <= tolerance

            day_details[field] = {
                'community': round(c_val, 2),
                'ground_truth': round(g_val, 2),
                'deviation_pct': round(deviation * 100, 3),
                'match': within,
            }

            if within:
                results[f'{field}_matches'] += 1
            else:
                day_match = False

        if day_match:
            results['matched_days'] += 1
        else:
            results['mismatches'].append(day_details)

        results['details'].append(day_details)

    # Calculate rates
    total = results['total_days']
    if total > 0:
        results['open_match_rate'] = results['open_matches'] / total
        results['high_match_rate'] = results['high_matches'] / total
        results['low_match_rate'] = results['low_matches'] / total
        results['close_match_rate'] = results['close_matches'] / total
        results['all_match_rate'] = results['matched_days'] / total

    return results


def check_structural_sanity(df):
    """Run structural sanity checks on the data."""
    if df is None or df.empty:
        return {'status': 'no data'}

    results = {}

    # OHLC consistency
    violations = 0
    for _, row in df.iterrows():
        o, h, l, c = row.get('open'), row.get('high'), row.get('low'), row.get('close')
        if pd.isna(o) or pd.isna(h) or pd.isna(l) or pd.isna(c):
            continue
        if h < max(o, c) or l > min(o, c):
            violations += 1

    total = len(df)
    results['ohlc_consistency'] = {
        'passed': total - violations,
        'failed': violations,
        'pass_rate': (total - violations) / total if total > 0 else 0,
    }

    # No duplicates
    dup_count = df.index.duplicated().sum()
    results['no_duplicates'] = {
        'passed': total - dup_count,
        'failed': dup_count,
        'pass_rate': (total - dup_count) / total if total > 0 else 0,
    }

    # No nulls in OHLC
    null_counts = df[['open', 'high', 'low', 'close']].isnull().sum().sum()
    total_cells = total * 4
    results['no_nulls'] = {
        'passed': total_cells - null_counts,
        'failed': null_counts,
        'pass_rate': (total_cells - null_counts) / total_cells if total_cells > 0 else 0,
    }

    return results


# ─── Main ───────────────────────────────────────────────────────────────

SOURCES = {
    'banknifty_5min': {
        'loader': load_community_banknifty_5min,
        'symbol': 'BANKNIFTY',
        'name': 'sandeepkapri/BankNifty-Data (5min)',
    },
    'banknifty_15min': {
        'loader': load_community_banknifty_15min,
        'symbol': 'BANKNIFTY',
        'name': 'sandeepkapri/BankNifty-Data (15min)',
    },
    'banknifty_1min': {
        'loader': load_community_banknifty_1min,
        'symbol': 'BANKNIFTY',
        'name': 'sandeepkapri/BankNifty-Data (1min)',
    },
}


def validate_source(source_key, tolerance_pct=0.5):
    """Run full validation on a community data source."""
    source = SOURCES[source_key]

    banner(f"Validating: {source['name']}")

    # 1. Load ground truth
    logger.info("Loading ground truth...")
    gt = load_ground_truth(source['symbol'])
    if gt is None:
        logger.error("Cannot proceed without ground truth")
        return None

    # 2. Load community data
    logger.info("Loading community data...")
    community = source['loader']()
    if community is None:
        logger.error("Cannot load community data")
        return None

    # 3. Structural sanity checks
    logger.info("Running structural sanity checks...")
    sanity = check_structural_sanity(community)
    for check, result in sanity.items():
        rate = result.get('pass_rate', 0)
        status = "PASS" if rate >= 0.99 else "WARN" if rate >= 0.95 else "FAIL"
        logger.info(f"  {check}: {status} ({rate:.1%})")

    # 4. Resample to daily
    logger.info("Resampling to daily...")
    community_daily = resample_to_daily(community)

    # 5. Cross-reference validation
    logger.info("Running cross-reference validation...")
    match_results = validate_daily_match(community_daily, gt, tolerance_pct)

    # 6. Print report
    banner("VALIDATION REPORT")
    print(f"Source:       {source['name']}")
    print(f"Ground Truth: yfinance {source['symbol']} daily")
    print(f"Tolerance:    {tolerance_pct}%")
    print()

    if 'all_match_rate' in match_results:
        total = match_results['total_days']
        print(f"Overlap Period: {community_daily.index[0].date()} to {community_daily.index[-1].date()}")
        print(f"Common Days:    {total}")
        print()
        print(f"OHLC Match Analysis:")
        print(f"  Open  match: {match_results['open_matches']}/{total} "
              f"({match_results['open_match_rate']:.1%})")
        print(f"  High  match: {match_results['high_matches']}/{total} "
              f"({match_results['high_match_rate']:.1%})")
        print(f"  Low   match: {match_results['low_matches']}/{total} "
              f"({match_results['low_match_rate']:.1%})")
        print(f"  Close match: {match_results['close_matches']}/{total} "
              f"({match_results['close_match_rate']:.1%})")
        print()
        all_rate = match_results['all_match_rate']
        print(f"  All-4 match:  {match_results['matched_days']}/{total} "
              f"({all_rate:.1%})", end="")

        if all_rate >= 0.90:
            print("  ✓ OVER 90%")
            verdict = "VALID - Safe for backtesting"
        elif all_rate >= 0.80:
            print("  ⚠ BELOW 90%")
            verdict = "FAIR - Review flagged days"
        else:
            print("  ✗ BELOW 80%")
            verdict = "SUSPECT - Do not use without review"

        print()
        print(f"VERDICT: {verdict}")

        # Show some mismatches
        if match_results['mismatches']:
            print(f"\nSample Mismatches (first 5):")
            for m in match_results['mismatches'][:5]:
                print(f"  {m['date']}:")
                for field in ['open', 'high', 'low', 'close']:
                    if field in m and 'community' in m[field]:
                        d = m[field]
                        print(f"    {field}: community={d['community']}, "
                              f"ground_truth={d['ground_truth']}, "
                              f"dev={d['deviation_pct']}%")

        # Save report
        VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
        report_path = VALIDATION_DIR / f"{source_key}_validation.csv"
        summary = pd.DataFrame([{
            'source': source['name'],
            'ground_truth': f"yfinance {source['symbol']}",
            'tolerance_pct': tolerance_pct,
            'total_days': total,
            'open_match_rate': match_results['open_match_rate'],
            'high_match_rate': match_results['high_match_rate'],
            'low_match_rate': match_results['low_match_rate'],
            'close_match_rate': match_results['close_match_rate'],
            'all_match_rate': all_rate,
            'verdict': verdict,
        }])
        summary.to_csv(report_path, index=False)
        logger.info(f"Report saved: {report_path}")

        return match_results
    else:
        print(f"ERROR: {match_results.get('reason', 'unknown')}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Validate community F&O data')
    parser.add_argument('--source', type=str, default=None,
                       choices=list(SOURCES.keys()),
                       help='Specific source to validate')
    parser.add_argument('--tolerance', type=float, default=0.5,
                       help='OHLC tolerance in %% (default: 0.5)')

    args = parser.parse_args()

    banner("COMMUNITY DATA VALIDATOR")

    if args.source:
        validate_source(args.source, args.tolerance)
    else:
        # Validate all sources
        for source_key in SOURCES:
            validate_source(source_key, args.tolerance)


if __name__ == '__main__':
    main()
