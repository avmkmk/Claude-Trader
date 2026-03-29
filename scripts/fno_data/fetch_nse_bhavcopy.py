"""
NSE F&O Bhavcopy Downloader
Downloads daily F&O bhavcopy ZIP files from NSE archives.
Filters for NIFTY and BANKNIFTY index options only.

Rate limiting: 1.5s between requests, exponential backoff on failures.
NSE blocks aggressive scrapers - respect their servers.

Usage:
    python scripts/fno_data/fetch_nse_bhavcopy.py
    python scripts/fno_data/fetch_nse_bhavcopy.py --start 2021-01-01 --end 2025-12-31
    python scripts/fno_data/fetch_nse_bhavcopy.py --symbols NIFTY BANKNIFTY
    python scripts/fno_data/fetch_nse_bhavcopy.py --resume  # Skip already downloaded days
"""

import os
import sys
import time
import zipfile
import io
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

import requests
import pandas as pd


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "fno"

# NSE archive URL pattern
NSE_BHAVCOPY_URL = (
    "https://archives.nseindia.com/content/historical/DERIVATIVES/{year}/{month}/fo{date_str}bhav.csv.zip"
)

# Month abbreviation mapping for NSE URLs
MONTH_MAP = {
    1: "JAN", 2: "FEB", 3: "MAR", 4: "APR",
    5: "MAY", 6: "JUN", 7: "JUL", 8: "AUG",
    9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"
}

# Rate limiting defaults
DEFAULT_DELAY_SECONDS = 1.5
MAX_RETRIES = 5
BACKOFF_FACTOR = 2
BACKOFF_CAP = 60  # Max backoff seconds


class NSEBhavcopyDownloader:
    """
    Downloads NSE F&O bhavcopy files with rate limiting and retry logic.

    NSE archives follow this URL pattern:
    https://archives.nseindia.com/content/historical/DERIVATIVES/2024/MAR/fo01MAR2024bhav.csv.zip
    """

    def __init__(self, delay_seconds=DEFAULT_DELAY_SECONDS, target_symbols=None):
        """
        Args:
            delay_seconds: Minimum delay between requests (default: 1.5s)
            target_symbols: List of symbols to filter (default: ['NIFTY', 'BANKNIFTY'])
        """
        self.delay_seconds = delay_seconds
        self.target_symbols = target_symbols or ['NIFTY', 'BANKNIFTY']
        self.session = self._create_session()
        self.last_request_time = 0

        # Stats
        self.stats = {
            'downloaded': 0,
            'skipped': 0,
            'failed': 0,
            'rows_filtered': 0,
        }

    def _create_session(self):
        """Create a requests session with browser-like headers."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        return session

    def _rate_limit(self):
        """Enforce minimum delay between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay_seconds:
            sleep_time = self.delay_seconds - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _fetch_with_retry(self, url, max_retries=MAX_RETRIES):
        """
        Fetch a URL with exponential backoff retry logic.

        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts

        Returns:
            Response content bytes, or None if all retries failed
        """
        for attempt in range(max_retries):
            self._rate_limit()

            try:
                response = self.session.get(url, timeout=30)

                if response.status_code == 200:
                    return response.content

                elif response.status_code == 404:
                    # No data for this date (holiday, weekend, or not in archive)
                    logger.debug(f"404 Not Found: {url}")
                    return None

                elif response.status_code == 429:
                    # Rate limited - back off aggressively
                    wait_time = min(BACKOFF_FACTOR ** (attempt + 2), BACKOFF_CAP)
                    logger.warning(f"Rate limited (429). Waiting {wait_time}s before retry {attempt+1}/{max_retries}")
                    time.sleep(wait_time)
                    continue

                elif response.status_code >= 500:
                    # Server error - retry with backoff
                    wait_time = min(BACKOFF_FACTOR ** attempt, BACKOFF_CAP)
                    logger.warning(f"Server error ({response.status_code}). Retry {attempt+1}/{max_retries} in {wait_time}s")
                    time.sleep(wait_time)
                    continue

                else:
                    logger.warning(f"Unexpected status {response.status_code} for {url}")
                    return None

            except requests.exceptions.Timeout:
                wait_time = min(BACKOFF_FACTOR ** attempt, BACKOFF_CAP)
                logger.warning(f"Timeout. Retry {attempt+1}/{max_retries} in {wait_time}s")
                time.sleep(wait_time)

            except requests.exceptions.ConnectionError:
                wait_time = min(BACKOFF_FACTOR ** (attempt + 1), BACKOFF_CAP)
                logger.warning(f"Connection error. Retry {attempt+1}/{max_retries} in {wait_time}s")
                time.sleep(wait_time)

            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return None

        logger.error(f"All {max_retries} retries failed for {url}")
        return None

    def _build_url(self, date):
        """
        Build the NSE bhavcopy URL for a given date.

        Args:
            date: datetime.date object

        Returns:
            URL string
        """
        day = date.strftime('%d')
        month_str = MONTH_MAP[date.month]
        year = date.year
        date_str = f"{day}{month_str}{year}"

        return NSE_BHAVCOPY_URL.format(
            year=year,
            month=month_str,
            date_str=date_str
        )

    def _parse_bhavcopy(self, zip_content, target_date):
        """
        Parse a bhavcopy ZIP file and filter for target symbols.

        Args:
            zip_content: Raw ZIP file bytes
            target_date: Date string for logging

        Returns:
            Filtered DataFrame, or None if parsing failed
        """
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                # Find the CSV file inside the ZIP
                csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
                if not csv_files:
                    logger.warning(f"No CSV found in ZIP for {target_date}")
                    return None

                with zf.open(csv_files[0]) as csv_file:
                    df = pd.read_csv(csv_file)

            # Standard bhavcopy columns (may vary slightly across years)
            # Older format: SYMBOL, EXPIRY_DT, STRIKE_PR, OPTION_TYPE
            # Newer format: SYMBOL, EXPIRY_DT, STRIKE_PR, OPTION_TYP
            col_map_upper = {c.upper(): c for c in df.columns}

            # Build rename map to handle both OPTION_TYPE and OPTION_TYP
            rename_map = {}
            col_target_map = {
                'SYMBOL': 'symbol',
                'EXPIRY_DT': 'expiry_date',
                'STRIKE_PR': 'strike_price',
                'OPTION_TYPE': 'option_type',
                'OPTION_TYP': 'option_type',
                'OPEN': 'open',
                'HIGH': 'high',
                'LOW': 'low',
                'CLOSE': 'close',
                'SETTLE_PR': 'settle_price',
                'CONTRACTS': 'contracts',
                'VAL_INLAKH': 'value_lakh',
                'OPEN_INT': 'open_interest',
                'CHG_IN_OI': 'chg_in_oi',
                'TIMESTAMP': 'timestamp',
            }
            for original_col in df.columns:
                upper = original_col.upper()
                if upper in col_target_map:
                    rename_map[original_col] = col_target_map[upper]

            # Verify required columns exist
            renamed_set = set(rename_map.values())
            required = {'symbol', 'expiry_date', 'strike_price'}
            if not required.issubset(renamed_set):
                logger.warning(f"Missing required columns in {target_date}. "
                             f"Found: {list(df.columns)}")
                logger.warning(f"Missing required columns in {target_date}. "
                             f"Found: {list(df.columns)}")
                return None

            # Filter for target symbols (NIFTY, BANKNIFTY)
            symbol_col = rename_map.get('SYMBOL', rename_map.get(next(
                (k for k in rename_map if rename_map[k] == 'symbol'), None
            )))
            # Find the original column name that maps to 'symbol'
            orig_symbol_col = next((k for k, v in rename_map.items() if v == 'symbol'), None)
            if orig_symbol_col is None:
                logger.warning(f"No symbol column found in {target_date}")
                return None

            filtered = df[df[orig_symbol_col].isin(self.target_symbols)].copy()

            if filtered.empty:
                logger.debug(f"No {self.target_symbols} data in {target_date}")
                return None

            # Rename columns
            filtered = filtered.rename(columns=rename_map)

            # Parse dates and numerics
            if 'expiry_date' in filtered.columns:
                filtered['expiry_date'] = pd.to_datetime(filtered['expiry_date'], errors='coerce')
            if 'strike_price' in filtered.columns:
                filtered['strike_price'] = pd.to_numeric(filtered['strike_price'], errors='coerce')

            # Keep only relevant columns (those that exist after rename)
            keep_cols = [
                'symbol', 'expiry_date', 'strike_price', 'option_type',
                'open', 'high', 'low', 'close', 'settle_price',
                'contracts', 'value_lakh', 'open_interest', 'chg_in_oi',
                'timestamp',
            ]
            filtered = filtered[[c for c in keep_cols if c in filtered.columns]]

            self.stats['rows_filtered'] += len(filtered)
            return filtered

        except Exception as e:
            logger.error(f"Error parsing bhavcopy for {target_date}: {e}")
            return None

    def _get_output_path(self, symbol, year):
        """
        Get the output file path for a given symbol and year.

        Args:
            symbol: 'NIFTY' or 'BANKNIFTY'
            year: Year as integer

        Returns:
            Path object
        """
        return DATA_DIR / symbol / "daily" / f"{year}" / f"fo_bhav_{year}.csv"

    def _load_existing_data(self, symbol, year):
        """Load existing yearly data if it exists."""
        path = self.get_output_path(symbol, year)
        if path.exists():
            return pd.read_csv(path, parse_dates=['expiry_date'])
        return None

    def get_output_path(self, symbol, year):
        """Public accessor for output path."""
        return DATA_DIR / symbol / "daily" / f"{year}" / f"fo_bhav_{year}.csv"

    def _get_existing_dates(self, symbol, year):
        """
        Get set of dates already downloaded for a symbol/year.

        Returns:
            Set of date strings (YYYY-MM-DD) already in the file
        """
        path = self.get_output_path(symbol, year)
        if not path.exists():
            return set()

        try:
            df = pd.read_csv(path)
            if 'timestamp' in df.columns:
                return set(df['timestamp'].dropna().unique())
            return set()
        except Exception:
            return set()

    def download_date(self, date, resume=False):
        """
        Download and process bhavcopy for a single date.

        Args:
            date: datetime.date object
            resume: If True, skip dates already downloaded

        Returns:
            dict: {symbol: DataFrame} for symbols found, or empty dict
        """
        date_str = date.strftime('%Y-%m-%d')
        year = date.year

        # Check if already downloaded (resume mode)
        if resume:
            existing = self._get_existing_dates(self.target_symbols[0], year)
            if date_str in existing:
                self.stats['skipped'] += 1
                return {}

        url = self._build_url(date)
        content = self._fetch_with_retry(url)

        if content is None:
            # 404 or error - likely a holiday or not in archive
            self.stats['failed'] += 1
            return {}

        df = self._parse_bhavcopy(content, date_str)
        if df is None or df.empty:
            self.stats['skipped'] += 1
            return {}

        # Split by symbol and save
        results = {}
        for symbol in self.target_symbols:
            symbol_df = df[df['symbol'] == symbol].copy()
            if not symbol_df.empty:
                results[symbol] = symbol_df

        self.stats['downloaded'] += 1
        return results

    def save_yearly_data(self, accumulated_data):
        """
        Save accumulated data organized by symbol and year.

        Args:
            accumulated_data: dict of {symbol: {year: DataFrame}}
        """
        for symbol, year_data in accumulated_data.items():
            for year, df in year_data.items():
                output_path = self.get_output_path(symbol, year)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if output_path.exists():
                    # Append and deduplicate
                    existing = pd.read_csv(output_path, parse_dates=['expiry_date'])
                    combined = pd.concat([existing, df], ignore_index=True)
                    # Build dedup subset from available columns
                    dedup_cols = [c for c in ['symbol', 'expiry_date', 'strike_price',
                                               'option_type', 'timestamp'] if c in combined.columns]
                    if dedup_cols:
                        combined = combined.drop_duplicates(subset=dedup_cols, keep='last')
                    sort_cols = [c for c in ['timestamp', 'symbol', 'expiry_date',
                                             'strike_price'] if c in combined.columns]
                    if sort_cols:
                        combined = combined.sort_values(sort_cols)
                    combined.to_csv(output_path, index=False)
                    logger.info(f"Appended to {output_path}: +{len(df)} rows (total: {len(combined)})")
                else:
                    df = df.sort_values(
                        ['timestamp', 'symbol', 'expiry_date', 'strike_price', 'option_type']
                    )
                    df.to_csv(output_path, index=False)
                    logger.info(f"Saved {output_path}: {len(df)} rows")

    def download_range(self, start_date, end_date, resume=False, save_every=50):
        """
        Download bhavcopy for a date range.

        Args:
            start_date: Start date (datetime.date or str 'YYYY-MM-DD')
            end_date: End date (datetime.date or str 'YYYY-MM-DD')
            resume: Skip already downloaded dates
            save_every: Save to disk every N days (memory management)
        """
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Generate trading days (weekdays only, skip known holidays later via 404)
        current = start_date
        all_dates = []
        while current <= end_date:
            if current.weekday() < 5:  # Monday=0, Friday=4
                all_dates.append(current)
            current += timedelta(days=1)

        total = len(all_dates)
        logger.info(f"Downloading NSE F&O bhavcopy: {start_date} to {end_date}")
        logger.info(f"Target symbols: {self.target_symbols}")
        logger.info(f"Total weekdays to check: {total}")
        logger.info(f"Rate limit: {self.delay_seconds}s between requests")
        logger.info(f"Save interval: every {save_every} days")
        if resume:
            logger.info("Resume mode: ON (skipping existing dates)")
        logger.info("=" * 60)

        accumulated = {sym: {} for sym in self.target_symbols}

        for idx, date in enumerate(all_dates, 1):
            date_str = date.strftime('%Y-%m-%d')

            if idx % 100 == 0 or idx == 1:
                logger.info(f"[{idx}/{total}] Processing {date_str} "
                          f"(downloaded={self.stats['downloaded']}, "
                          f"skipped={self.stats['skipped']}, "
                          f"failed={self.stats['failed']})")

            results = self.download_date(date, resume=resume)

            for symbol, df in results.items():
                year = date.year
                if year not in accumulated[symbol]:
                    accumulated[symbol][year] = []
                accumulated[symbol][year].append(df)

            # Periodic save to manage memory
            if idx % save_every == 0:
                self._flush_accumulated(accumulated)
                accumulated = {sym: {} for sym in self.target_symbols}

            # Progress checkpoint every 250 days
            if idx % 250 == 0:
                logger.info(f"  Checkpoint [{idx}/{total}]: "
                          f"downloaded={self.stats['downloaded']}, "
                          f"skipped={self.stats['skipped']}, "
                          f"failed={self.stats['failed']}, "
                          f"rows={self.stats['rows_filtered']}")

        # Final flush
        self._flush_accumulated(accumulated)

        # Print summary
        logger.info("=" * 60)
        logger.info("Download complete!")
        logger.info(f"  Days downloaded: {self.stats['downloaded']}")
        logger.info(f"  Days skipped (holidays/weekends): {self.stats['skipped']}")
        logger.info(f"  Days failed: {self.stats['failed']}")
        logger.info(f"  Total option rows: {self.stats['rows_filtered']}")
        logger.info("=" * 60)

    def _flush_accumulated(self, accumulated):
        """Convert accumulated lists to DataFrames and save."""
        to_save = {}
        for symbol, year_data in accumulated.items():
            to_save[symbol] = {}
            for year, df_list in year_data.items():
                if df_list:
                    to_save[symbol][year] = pd.concat(df_list, ignore_index=True)

        if any(to_save.values()):
            self.save_yearly_data(to_save)


def generate_trading_days(start_date, end_date):
    """Generate list of trading days (weekdays) between two dates."""
    current = start_date
    days = []
    while current <= end_date:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def main():
    parser = argparse.ArgumentParser(description='Download NSE F&O Bhavcopy data')
    parser.add_argument('--start', type=str, default='2021-01-01',
                       help='Start date (YYYY-MM-DD), default: 2021-01-01')
    parser.add_argument('--end', type=str, default=None,
                       help='End date (YYYY-MM-DD), default: yesterday')
    parser.add_argument('--symbols', nargs='+', default=['NIFTY', 'BANKNIFTY'],
                       help='Symbols to filter, default: NIFTY BANKNIFTY')
    parser.add_argument('--delay', type=float, default=1.5,
                       help='Delay between requests in seconds, default: 1.5')
    parser.add_argument('--resume', action='store_true',
                       help='Skip already downloaded dates')
    parser.add_argument('--save-every', type=int, default=50,
                       help='Save to disk every N days, default: 50')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable debug logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    start_date = datetime.strptime(args.start, '%Y-%m-%d').date()
    end_date = (
        datetime.strptime(args.end, '%Y-%m-%d').date()
        if args.end
        else (datetime.now().date() - timedelta(days=1))
    )

    downloader = NSEBhavcopyDownloader(
        delay_seconds=args.delay,
        target_symbols=args.symbols,
    )

    downloader.download_range(
        start_date=start_date,
        end_date=end_date,
        resume=args.resume,
        save_every=args.save_every,
    )


if __name__ == '__main__':
    main()
