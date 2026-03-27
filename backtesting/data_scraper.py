import os
import pandas as pd
import time
from datetime import datetime


class EquityDataScraper:
    """
    Scrapes historical equity data using NubraAPIHandler
    Respects Nubra API rate limit: 60 requests/minute
    """

    def __init__(self, nubra_handler):
        """
        Args:
            nubra_handler: Instance of NubraAPIHandler (from apis/nubra_api.py)
        """
        self.nubra = nubra_handler

    def get_nse_equities(self, limit=50):
        """
        Filter security_id_list.csv for NSE equities

        Returns:
            List of symbol names from NSE equity instruments
        """
        try:
            # Read security_id_list.csv
            csv_path = os.path.join(os.getcwd(), 'security_id_list.csv')

            if not os.path.exists(csv_path):
                print(f"Warning: security_id_list.csv not found at {csv_path}")
                return []

            df = pd.read_csv(csv_path)

            # Filter for NSE equities only
            # SEM_EXM_EXCH_ID == 'NSE' AND SEM_EXCH_INSTRUMENT_TYPE in ['ES', 'EQUITY']
            nse_equities = df[
                (df['SEM_EXM_EXCH_ID'] == 'NSE') &
                (df['SEM_EXCH_INSTRUMENT_TYPE'].isin(['ES', 'EQUITY']))
            ]

            # Extract symbol names and remove duplicates
            symbols = nse_equities['SM_SYMBOL_NAME'].dropna().unique().tolist()

            # Return limited number of symbols
            return symbols[:limit]

        except Exception as e:
            print(f"Error reading security_id_list.csv: {e}")
            return []

    def convert_paise_to_rupees(self, df):
        """
        Convert OHLC prices from paise (integers) to rupees (decimals).
        Nubra API returns prices in paise (100 paise = 1 rupee).
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with prices converted to rupees (divided by 100)
        """
        df['open'] = df['open'] / 100
        df['high'] = df['high'] / 100
        df['low'] = df['low'] / 100
        df['close'] = df['close'] / 100
        # Volume stays unchanged (measured in shares, not paise)
        return df

    def scrape_equity(self, symbol, period_days=90):
        """
        Fetch historical data for a single symbol

        Args:
            symbol: Trading symbol (e.g., 'GRAPHITE', 'RELIANCE')
            period_days: Number of days of historical data (default: 90)

        Returns:
            DataFrame with OHLCV + datetime index (prices in rupees), or None if failed
        """
        try:
            # Choose appropriate method based on period
            if period_days <= 90:
                df = self.nubra.get_3months_equity(symbol)
            else:
                # Use 1-year method for longer periods (365 days)
                df = self.nubra.get_1year_equity(symbol)

            if df is None or df.empty:
                print(f"No data returned for {symbol}")
                return None

            # Convert prices from paise to rupees for backtesting
            df = self.convert_paise_to_rupees(df)
            
            return df

        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None

    def save_to_csv(self, df, symbol, period_days=90):
        """
        Save DataFrame to data/{symbol}_{period_days}days.csv

        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            period_days: Period in days (for filename)
        """
        try:
            # Create data directory if it doesn't exist
            data_dir = os.path.join(os.getcwd(), 'data')
            os.makedirs(data_dir, exist_ok=True)

            # Save to CSV
            filename = f"{symbol}_{period_days}days.csv"
            filepath = os.path.join(data_dir, filename)
            df.to_csv(filepath)

            print(f"Saved {symbol} data to {filepath} ({len(df)} rows)")

        except Exception as e:
            print(f"Error saving {symbol} to CSV: {e}")

    def scrape_batch(self, symbols, delay_seconds=2, period_days=90):
        """
        Scrape multiple symbols with rate limiting
        Default 2-second delay respects Nubra's 60 requests/minute limit

        Args:
            symbols: List of trading symbols
            delay_seconds: Delay between requests (default: 2 seconds)
            period_days: Number of days of historical data (default: 90)
        """
        total = len(symbols)
        successful = 0
        failed = 0

        print(f"\nStarting batch scrape of {total} symbols...")
        print(f"Period: {period_days} days")
        print(f"Rate limit: {delay_seconds} seconds between requests")
        print("=" * 60)

        for idx, symbol in enumerate(symbols, 1):
            print(f"\n[{idx}/{total}] Scraping {symbol}...")

            try:
                df = self.scrape_equity(symbol, period_days=period_days)

                if df is not None and not df.empty:
                    self.save_to_csv(df, symbol, period_days=period_days)
                    successful += 1
                else:
                    print(f"[WARNING] {symbol}: No data available")
                    failed += 1

            except Exception as e:
                print(f"[ERROR] {symbol}: Failed - {str(e)}")
                failed += 1

            # Rate limiting: wait between requests (except after last symbol)
            if idx < total:
                print(f"Waiting {delay_seconds} seconds (rate limit)...")
                time.sleep(delay_seconds)

        print("\n" + "=" * 60)
        print(f"Batch scraping complete!")
        print(f"[SUCCESS] Successful: {successful}")
        print(f"[FAILED] Failed: {failed}")
        print(f"[INFO] Check data/ folder for CSV files")
