"""DataFetcher - Fetches and validates historical stock data"""

import os
import pandas as pd
from datetime import datetime
from typing import Dict
from filelock import FileLock
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetches data from Nubra API, validates it, and appends to CSV files with file locking"""

    def __init__(self, nubra_handler, csv_base_path: str):
        """
        Initialize DataFetcher

        Args:
            nubra_handler: Instance of NubraAPIHandler for API calls
            csv_base_path: Base directory path for CSV files
        """
        self.nubra_handler = nubra_handler
        self.csv_base_path = csv_base_path

    def fetch_and_append(self, symbol: str, from_date: str, to_date: str) -> Dict:
        """
        Fetch historical data for a symbol and append to CSV file

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            from_date: Start date in 'YYYY-MM-DD' format
            to_date: End date in 'YYYY-MM-DD' format

        Returns:
            Dict with keys:
                - status: 'success' or 'failed'
                - rows_added: Number of rows appended (0 if failed)
                - error: Error message if failed, None if success
        """
        try:
            # Fetch data from Nubra API
            logger.info(f"Fetching data for {symbol} from {from_date} to {to_date}")
            df = self.nubra_handler.get_historical_data(symbol, from_date, to_date, '1d')

            if df is None or df.empty:
                error_msg = f"No data returned from API for {symbol}"
                logger.warning(error_msg)
                return {
                    'status': 'failed',
                    'rows_added': 0,
                    'error': error_msg
                }

            # Validate data
            is_valid, validation_error = self._validate_data(df, from_date, to_date)
            if not is_valid:
                logger.error(f"Validation failed for {symbol}: {validation_error}")
                return {
                    'status': 'failed',
                    'rows_added': 0,
                    'error': validation_error
                }

            # Prepare CSV path
            csv_path = os.path.join(self.csv_base_path, f"{symbol}.csv")

            # Append to CSV with file locking
            rows_added = self._append_to_csv(csv_path, df)

            logger.info(f"Successfully appended {rows_added} rows for {symbol}")
            return {
                'status': 'success',
                'rows_added': rows_added,
                'error': None
            }

        except Exception as e:
            error_msg = f"Unexpected error fetching data for {symbol}: {str(e)}"
            logger.error(error_msg)
            return {
                'status': 'failed',
                'rows_added': 0,
                'error': error_msg
            }

    def _validate_data(self, df: pd.DataFrame, from_date: str, to_date: str) -> tuple[bool, str]:
        """
        Validate OHLCV data quality

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
            from_date: Expected start date (YYYY-MM-DD)
            to_date: Expected end date (YYYY-MM-DD)

        Returns:
            Tuple of (is_valid: bool, error_message: str or None)
        """
        try:
            # Check required columns exist (case-insensitive)
            df_columns_lower = [col.lower() for col in df.columns]
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df_columns_lower:
                    return False, f"Missing required column: {col}"

            # Normalize column names to lowercase for validation
            df_normalized = df.copy()
            df_normalized.columns = [col.lower() for col in df.columns]

            # Check for negative or zero prices
            price_cols = ['open', 'high', 'low', 'close']
            for col in price_cols:
                if (df_normalized[col] <= 0).any():
                    return False, f"Invalid {col} price: found negative or zero values"

            # Check price relationships: high >= low, high >= open, high >= close
            if (df_normalized['high'] < df_normalized['low']).any():
                return False, "Invalid price data: high < low"

            if (df_normalized['high'] < df_normalized['open']).any():
                return False, "Invalid price data: high < open"

            if (df_normalized['high'] < df_normalized['close']).any():
                return False, "Invalid price data: high < close"

            # Check low <= open and low <= close
            if (df_normalized['low'] > df_normalized['open']).any():
                return False, "Invalid price data: low > open"

            if (df_normalized['low'] > df_normalized['close']).any():
                return False, "Invalid price data: low > close"

            # All validations passed
            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _append_to_csv(self, csv_path: str, df: pd.DataFrame) -> int:
        """
        Append data to CSV file with thread-safe file locking

        Args:
            csv_path: Full path to CSV file
            df: DataFrame to append (index is datetime, columns are OHLCV)

        Returns:
            Number of rows appended
        """
        lock_path = f"{csv_path}.lock"
        lock = FileLock(lock_path, timeout=10)

        try:
            with lock:
                # Prepare data for writing
                df_to_write = df.copy()

                # Reset index to make datetime a column and format as YYYY-MM-DD
                df_to_write = df_to_write.reset_index()
                df_to_write.iloc[:, 0] = pd.to_datetime(df_to_write.iloc[:, 0]).dt.strftime('%Y-%m-%d')

                # Capitalize column names: Date, Open, High, Low, Close, Volume
                column_mapping = {
                    df_to_write.columns[0]: 'Date',  # First column is the datetime index
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                }

                # Rename columns (case-insensitive matching)
                new_columns = []
                for col in df_to_write.columns:
                    col_lower = col.lower()
                    if col_lower in column_mapping:
                        new_columns.append(column_mapping[col_lower])
                    else:
                        # First column (index) gets renamed to 'Date'
                        new_columns.append(column_mapping.get(col, col))

                df_to_write.columns = new_columns

                # Ensure correct column order
                df_to_write = df_to_write[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

                # Check if file exists
                file_exists = os.path.exists(csv_path)

                # Append to CSV (or create new if doesn't exist)
                df_to_write.to_csv(
                    csv_path,
                    mode='a' if file_exists else 'w',
                    header=not file_exists,
                    index=False
                )

                return len(df_to_write)

        except Exception as e:
            logger.error(f"Error appending to CSV {csv_path}: {str(e)}")
            raise
