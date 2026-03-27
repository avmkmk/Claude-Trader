#!/usr/bin/env python3
"""
Multi-timeframe scraper for HDFCBANK - 365 days of data.

Fetches data for multiple timeframes (15m, 1h, 4h, 1d) with intelligent rate limiting:
- 60 requests/minute limit from Nubra API
- Wait 1 second after every 50 requests to stay under limit
- Handles chunking for intraday intervals (split into smaller date ranges)

Usage:
    python scripts/hdfc_multi_timeframe_scraper.py [--days DAYS] [--chunk DAYS]

Examples:
    python scripts/hdfc_multi_timeframe_scraper.py                    # 365 days
    python scripts/hdfc_multi_timeframe_scraper.py --days 90          # 90 days
    python scripts/hdfc_multi_timeframe_scraper.py --chunk 7          # 7-day chunks
"""

import os
import sys
import datetime
import pandas as pd
import time
import argparse
from pathlib import Path
from typing import List, Tuple
from dateutil.relativedelta import relativedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from apis.nubra_api import NubraAPIHandler
from dotenv import load_dotenv


class MultiTimeframeDataScraper:
    """Scrapes historical data for multiple timeframes with rate limiting"""
    
    def __init__(self):
        load_dotenv()
        self.nubra = NubraAPIHandler()
        if not self.nubra.initialize_sdk():
            raise RuntimeError("Failed to initialize Nubra SDK")
        
        self.request_count = 0
        self.last_rate_limit_check = time.time()
        print("✓ Nubra SDK initialized successfully")
    
    def rate_limit_check(self, check_every=50):
        """
        Rate limiting: Wait 1 second after every 50 requests.
        Nubra limit: 60 requests/minute = 1 request/second allowed.
        
        Args:
            check_every: Number of requests before checking/waiting
        """
        self.request_count += 1
        
        if self.request_count % check_every == 0:
            elapsed = time.time() - self.last_rate_limit_check
            wait_time = max(0, 1.0 - elapsed)  # Ensure minimum 1 sec per 50 requests
            
            if wait_time > 0:
                print(f"  [RATE LIMIT] Request count: {self.request_count}, waiting {wait_time:.2f}s...")
                time.sleep(wait_time)
            
            self.last_rate_limit_check = time.time()
    
    def get_date_chunks(self, start_date, end_date, chunk_days):
        """
        Split a date range into chunks for API requests.
        
        Args:
            start_date: datetime object
            end_date: datetime object
            chunk_days: Number of days per chunk
            
        Returns:
            List of tuples: [(start_date, end_date), ...]
        """
        chunks = []
        current_start = start_date
        
        while current_start < end_date:
            current_end = min(
                current_start + datetime.timedelta(days=chunk_days),
                end_date
            )
            chunks.append((current_start, current_end))
            current_start = current_end
        
        return chunks
    
    def fetch_data_for_interval(self, symbol, from_date, to_date, interval, chunk_days=7):
        """
        Fetch historical data for a specific interval, chunking the date range.
        
        Args:
            symbol: Stock symbol (e.g., 'HDFCBANK')
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            interval: Timeframe ('15m', '1h', '4h', '1d')
            chunk_days: Days per chunk (default: 7, appropriate for intraday)
            
        Returns:
            DataFrame with all data concatenated, or None if failed
        """
        dfs = []
        
        # Parse dates
        start = datetime.datetime.strptime(from_date, '%Y-%m-%d')
        end = datetime.datetime.strptime(to_date, '%Y-%m-%d')
        
        # Get date chunks (daily candles can use larger chunks)
        if interval == '1d':
            chunks = [(start, end)]  # Single chunk for daily
        else:
            # Intraday data needs smaller chunks due to data volume
            chunks = self.get_date_chunks(start, end, chunk_days)
        
        print(f"  Fetching {interval} candles: {len(chunks)} chunk(s)")
        
        for chunk_idx, (chunk_start, chunk_end) in enumerate(chunks, 1):
            from_str = chunk_start.strftime('%Y-%m-%d')
            to_str = chunk_end.strftime('%Y-%m-%d')
            
            print(f"    [{chunk_idx}/{len(chunks)}] {from_str} to {to_str}...", end=' ', flush=True)
            
            try:
                # Apply rate limiting before request
                self.rate_limit_check(check_every=50)
                
                # Fetch data using raw interval string (not legacy mapping)
                df = self.nubra.get_historical_data(symbol, from_str, to_str, interval)
                
                if df is not None and not df.empty:
                    dfs.append(df)
                    print(f"✓ {len(df)} rows")
                else:
                    print("⊘ No data")
                
            except Exception as e:
                print(f"✗ Error: {str(e)[:60]}")
                continue
        
        if not dfs:
            return None
        
        # Concatenate all chunks and remove duplicates
        combined_df = pd.concat(dfs, axis=0)
        combined_df = combined_df[~combined_df.index.duplicated(keep='first')]
        combined_df = combined_df.sort_index()
        
        return combined_df
    
    def convert_paise_to_rupees(self, df):
        """Convert OHLC prices from paise to rupees."""
        df['open'] = df['open'] / 100
        df['high'] = df['high'] / 100
        df['low'] = df['low'] / 100
        df['close'] = df['close'] / 100
        return df
    
    def save_to_csv(self, df, symbol, interval, days=365):
        """Save DataFrame to CSV file."""
        try:
            data_dir = Path(__file__).parent / 'data'
            data_dir.mkdir(exist_ok=True)
            
            filename = f"{symbol}_{days}days_{interval}.csv"
            filepath = data_dir / filename
            
            # Convert paise to rupees
            df = self.convert_paise_to_rupees(df)
            df.to_csv(filepath)
            
            print(f"    ✓ Saved to {filename} ({len(df)} rows)")
            return filepath
            
        except Exception as e:
            print(f"    ✗ Error saving: {e}")
            return None
    
    def scrape_all_timeframes(self, symbol, from_date, to_date, days=365):
        """
        Scrape all timeframes for a symbol.
        
        Args:
            symbol: Stock symbol
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            days: Number of days for naming convention
        """
        intervals = ['15m', '1h', '4h', '1d']
        results = {}
        
        print(f"\n{'='*80}")
        print(f"SCRAPING {symbol} - {days} DAYS ACROSS TIMEFRAMES")
        print(f"{'='*80}")
        print(f"Date range: {from_date} to {to_date}\n")
        
        for interval in intervals:
            print(f"[{interval.upper():>3}] Fetching {interval} candles...")
            
            try:
                # Determine chunk size based on interval
                if interval == '1d':
                    chunk_days = 365  # Daily can handle large chunks
                elif interval == '4h':
                    chunk_days = 30   # 4h: ~180 candles per 30 days
                elif interval == '1h':
                    chunk_days = 14   # 1h: ~336 candles per 14 days
                else:  # '15m'
                    chunk_days = 7    # 15m: ~384 candles per 7 days
                
                df = self.fetch_data_for_interval(symbol, from_date, to_date, interval, chunk_days=chunk_days)
                
                if df is not None and not df.empty:
                    filepath = self.save_to_csv(df, symbol, interval, days=days)
                    results[interval] = {
                        'status': 'success',
                        'rows': len(df),
                        'filepath': str(filepath),
                        'date_range': f"{df.index[0]} to {df.index[-1]}"
                    }
                else:
                    results[interval] = {'status': 'failed', 'error': 'No data returned'}
                    print(f"    ✗ No data returned")
                
            except Exception as e:
                results[interval] = {'status': 'error', 'error': str(e)}
                print(f"    ✗ Error: {e}")
        
        # Print summary
        self.print_summary(symbol, results, days)
        
        return results
    
    def print_summary(self, symbol, results, days):
        """Print summary of scraping results."""
        print(f"\n{'='*80}")
        print(f"SCRAPING SUMMARY - {symbol} ({days} days)")
        print(f"{'='*80}\n")
        
        print(f"Total requests made: {self.request_count}")
        print(f"Rate limit checks performed: {self.request_count // 50}\n")
        
        print(f"{'Interval':<10} {'Status':<12} {'Rows':<10} {'Details':<50}")
        print("-" * 80)
        
        for interval, result in results.items():
            status = result['status'].upper()
            rows = result.get('rows', 0)
            details = result.get('date_range', result.get('error', 'N/A'))
            
            status_icon = "✓" if status == "SUCCESS" else "✗"
            print(f"{interval:<10} {status_icon} {status:<10} {rows:<10} {details:<50}")
        
        print(f"\n{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape HDFCBANK data across multiple timeframes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='Number of days to scrape (default: 365)'
    )
    parser.add_argument(
        '--chunk',
        type=int,
        help='Override chunk size for date ranges (days)',
        dest='chunk_days'
    )
    
    args = parser.parse_args()
    
    try:
        scraper = MultiTimeframeDataScraper()
        
        # Calculate date range
        to_date = datetime.datetime.now().date()
        from_date = to_date - datetime.timedelta(days=args.days)
        
        # Scrape all timeframes
        results = scraper.scrape_all_timeframes(
            symbol='HDFCBANK',
            from_date=from_date.strftime('%Y-%m-%d'),
            to_date=to_date.strftime('%Y-%m-%d'),
            days=args.days
        )
        
        # Exit with success code if we got any data
        successful = sum(1 for r in results.values() if r['status'] == 'success')
        sys.exit(0 if successful > 0 else 1)
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
