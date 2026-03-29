import os
import pandas as pd
import time
from datetime import datetime


class EquityDataScraper:
    """
    Scrapes historical equity data using NubraAPIHandler
    Respects Nubra API rate limit: 60 requests/minute
    
    New folder structure:
        data/SYMBOL_YYYY-MM-DD_HH-MM-SS/
            ├── 5min.csv
            ├── 15min.csv
            ├── 60min.csv
            ├── 4hour.csv
            ├── daily.csv
            └── weekly.csv
    """

    TIMEFRAMES = ['5min', '15min', '60min', '4hour', 'daily', 'weekly']
    
    TIMEFRAME_INTERVAL_MAP = {
        '5min': '5m',
        '15min': '15m',
        '60min': '1h',
        '4hour': '4h',
        'daily': '1d',
        'weekly': '1d'  # Weekly is aggregated from daily
    }
    
    FILENAME_MAP = {
        '5min': '5min.csv',
        '15min': '15min.csv',
        '60min': '60min.csv',
        '4hour': '4hour.csv',
        'daily': 'daily.csv',
        'weekly': 'weekly.csv'
    }

    def __init__(self, nubra_handler, min_request_interval=2.0):
        """
        Args:
            nubra_handler: Instance of NubraAPIHandler (from apis/nubra_api.py)
            min_request_interval: Minimum seconds between requests (default: 2.0 for 60 req/min)
        """
        self.nubra = nubra_handler
        self.min_request_interval = min_request_interval
        self.data_dir = os.path.join(os.getcwd(), 'data')
        self.scrape_timestamp = None

    def _generate_timestamp(self):
        """Generate timestamp string for folder naming."""
        return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    def _get_folder_name(self, symbol):
        """Generate folder name with symbol and timestamp."""
        if self.scrape_timestamp is None:
            self.scrape_timestamp = self._generate_timestamp()
        return f"{symbol}_{self.scrape_timestamp}"

    def _create_folder_structure(self, symbol):
        """Create folder structure for symbol data."""
        folder_name = self._get_folder_name(symbol)
        folder_path = os.path.join(self.data_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    def get_nse_equities(self, limit=50):
        """
        Filter security_id_list.csv for NSE equities

        Returns:
            List of symbol names from NSE equity instruments
        """
        try:
            csv_path = os.path.join(os.getcwd(), 'security_id_list.csv')

            if not os.path.exists(csv_path):
                print(f"Warning: security_id_list.csv not found at {csv_path}")
                return []

            df = pd.read_csv(csv_path)

            nse_equities = df[
                (df['SEM_EXM_EXCH_ID'] == 'NSE') &
                (df['SEM_EXCH_INSTRUMENT_TYPE'].isin(['ES', 'EQUITY']))
            ]

            symbols = nse_equities['SM_SYMBOL_NAME'].dropna().unique().tolist()
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
        df = df.copy()
        df['open'] = df['open'] / 100
        df['high'] = df['high'] / 100
        df['low'] = df['low'] / 100
        df['close'] = df['close'] / 100
        return df

    def _aggregate_weekly(self, df_daily):
        """
        Aggregate daily data to weekly timeframe.
        
        Args:
            df_daily: DataFrame with daily OHLCV data
            
        Returns:
            DataFrame with weekly OHLCV data
        """
        if df_daily is None or df_daily.empty:
            return None
            
        df = df_daily.copy()
        
        # Resample to weekly (W-MON means week starts on Monday)
        # Use the last trading day of each week as the anchor
        df_resampled = df.resample('W-FRI').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        # Drop rows with NaN values (incomplete weeks)
        df_resampled = df_resampled.dropna()
        
        return df_resampled

    def scrape_equity_timeframe(self, symbol, period_days, timeframe):
        """
        Fetch historical data for a single symbol and timeframe.
        
        Args:
            symbol: Trading symbol (e.g., 'RELIANCE', 'HDFCBANK')
            period_days: Number of days of historical data
            timeframe: Timeframe key ('5min', '15min', '60min', '4hour', 'daily')
            
        Returns:
            DataFrame with OHLCV + datetime index (prices in rupees), or None if failed
        """
        if timeframe not in self.TIMEFRAME_INTERVAL_MAP:
            print(f"Error: Unknown timeframe '{timeframe}'. Valid options: {self.TIMEFRAMES}")
            return None
            
        interval = self.TIMEFRAME_INTERVAL_MAP[timeframe]
        
        try:
            today = datetime.now()
            start = today - pd.Timedelta(days=period_days)
            from_date = start.strftime('%Y-%m-%d')
            to_date = today.strftime('%Y-%m-%d')
            
            df = self.nubra.get_historical_data(symbol, from_date, to_date, interval)
            
            if df is None or df.empty:
                print(f"No data returned for {symbol} ({timeframe})")
                return None
            
            # Convert prices from paise to rupees
            df = self.convert_paise_to_rupees(df)
            
            # For weekly, aggregate from daily
            if timeframe == 'weekly':
                df = self._aggregate_weekly(df)
            
            return df
            
        except Exception as e:
            print(f"Error fetching {symbol} ({timeframe}): {e}")
            return None

    def save_to_csv_timeframe(self, df, symbol, timeframe):
        """
        Save DataFrame to data/SYMBOL_TIMESTAMP/TIMEFRAME.csv
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            timeframe: Timeframe key ('5min', '15min', etc.)
        """
        if df is None or df.empty:
            print(f"No data to save for {symbol} ({timeframe})")
            return
            
        try:
            folder_path = self._create_folder_structure(symbol)
            filename = self.FILENAME_MAP[timeframe]
            filepath = os.path.join(folder_path, filename)
            df.to_csv(filepath)
            print(f"  Saved {timeframe}: {filepath} ({len(df)} rows)")
            
        except Exception as e:
            print(f"Error saving {symbol} ({timeframe}) to CSV: {e}")

    def scrape_equity_all_timeframes(self, symbol, period_days=365):
        """
        Scrape all timeframes for a single symbol.
        
        Args:
            symbol: Trading symbol
            period_days: Number of days of historical data (default: 365)
            
        Returns:
            Dictionary with timeframe -> DataFrame mapping
        """
        results = {}
        
        print(f"\n Scraping all timeframes for {symbol}...")
        
        for timeframe in self.TIMEFRAMES:
            print(f"  Fetching {timeframe} data...")
            
            # Skip weekly here, we aggregate from daily
            if timeframe == 'weekly':
                continue
                
            df = self.scrape_equity_timeframe(symbol, period_days, timeframe)
            
            if df is not None and not df.empty:
                results[timeframe] = df
                self.save_to_csv_timeframe(df, symbol, timeframe)
            else:
                print(f"  Warning: No data for {symbol} ({timeframe})")
            
            # Rate limiting between requests
            time.sleep(self.min_request_interval)
        
        # Aggregate weekly from daily
        if 'daily' in results:
            print(f"  Aggregating weekly data...")
            weekly_df = self._aggregate_weekly(results['daily'])
            if weekly_df is not None and not weekly_df.empty:
                results['weekly'] = weekly_df
                self.save_to_csv_timeframe(weekly_df, symbol, 'weekly')
        
        return results

    def scrape_equity(self, symbol, period_days=90):
        """
        Fetch historical daily data for a single symbol (legacy method).
        
        Args:
            symbol: Trading symbol (e.g., 'GRAPHITE', 'RELIANCE')
            period_days: Number of days of historical data (default: 90)

        Returns:
            DataFrame with OHLCV + datetime index (prices in rupees), or None if failed
        """
        return self.scrape_equity_timeframe(symbol, period_days, 'daily')

    def save_to_csv(self, df, symbol, period_days=90):
        """
        Save DataFrame to data/{symbol}_{period_days}days.csv (legacy method)

        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            period_days: Period in days (for filename)
        """
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            filename = f"{symbol}_{period_days}days.csv"
            filepath = os.path.join(self.data_dir, filename)
            df.to_csv(filepath)
            print(f"Saved {symbol} data to {filepath} ({len(df)} rows)")
        except Exception as e:
            print(f"Error saving {symbol} to CSV: {e}")

    def scrape_batch_all_timeframes(self, symbols, period_days=365, delay_seconds=2.0):
        """
        Scrape multiple symbols with all timeframes and rate limiting.
        
        Args:
            symbols: List of trading symbols
            period_days: Number of days of historical data (default: 365)
            delay_seconds: Delay between requests (default: 2.0 seconds)
        """
        self.min_request_interval = delay_seconds
        total = len(symbols)
        successful = 0
        failed = 0
        
        print(f"\n{'='*60}")
        print(f"Starting batch scrape of {total} symbols")
        print(f"Period: {period_days} days")
        print(f"Timeframes: {', '.join(self.TIMEFRAMES)}")
        print(f"Rate limit: {delay_seconds} seconds between requests")
        print(f"{'='*60}")
        
        for idx, symbol in enumerate(symbols, 1):
            print(f"\n[{idx}/{total}] Scraping {symbol}...")
            
            try:
                results = self.scrape_equity_all_timeframes(symbol, period_days)
                
                if results and any(v is not None and not v.empty for v in results.values()):
                    successful += 1
                    print(f"[SUCCESS] {symbol}: {len(results)} timeframes scraped")
                else:
                    print(f"[WARNING] {symbol}: No data available")
                    failed += 1
                    
            except Exception as e:
                print(f"[ERROR] {symbol}: Failed - {str(e)}")
                failed += 1
            
            # Rate limiting between symbols (except after last)
            if idx < total:
                print(f"Waiting {delay_seconds} seconds (rate limit)...")
                time.sleep(delay_seconds)
        
        print(f"\n{'='*60}")
        print(f"Batch scraping complete!")
        print(f"[SUCCESS] Successful: {successful}/{total}")
        print(f"[FAILED] Failed: {failed}/{total}")
        print(f"[INFO] Data saved in data/ folder")
        print(f"{'='*60}")
        
        return {'successful': successful, 'failed': failed}

    def scrape_batch(self, symbols, delay_seconds=2, period_days=90):
        """
        Scrape multiple symbols with rate limiting (legacy method).
        
        Args:
            symbols: List of trading symbols
            delay_seconds: Delay between requests (default: 2 seconds)
            period_days: Number of days of historical data (default: 90)
        """
        self.min_request_interval = delay_seconds
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

            if idx < total:
                print(f"Waiting {delay_seconds} seconds (rate limit)...")
                time.sleep(delay_seconds)

        print("\n" + "=" * 60)
        print(f"Batch scraping complete!")
        print(f"[SUCCESS] Successful: {successful}")
        print(f"[FAILED] Failed: {failed}")
        print(f"[INFO] Check data/ folder for CSV files")
