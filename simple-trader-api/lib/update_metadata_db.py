"""UpdateMetadataDB - Manages data update metadata tracking"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
import logging
import os
import pandas as pd

logger = logging.getLogger(__name__)


class UpdateMetadataDB:
    """Manages metadata tracking for daily data updates"""

    def __init__(self, db_path: str):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish database connection with Row factory"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def get_stocks_to_update(self) -> List[Tuple[str, str, str]]:
        """
        Get list of stocks that need updating (have gaps between last_updated_date and today)

        Returns:
            List of tuples: (symbol, from_date, to_date)
            - from_date: last_updated_date + 1 day
            - to_date: today's date
        """
        cursor = self.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')

        query = """
            SELECT symbol, last_updated_date
            FROM data_updates
            WHERE last_updated_date < ?
            ORDER BY symbol
        """

        cursor.execute(query, (today,))
        rows = cursor.fetchall()

        result = []
        for row in rows:
            symbol = row['symbol']
            last_updated_str = row['last_updated_date']

            # Parse last_updated_date
            last_updated = datetime.strptime(last_updated_str, '%Y-%m-%d')

            # Calculate from_date (last_updated + 1 day)
            from_date_dt = last_updated + timedelta(days=1)
            from_date = from_date_dt.strftime('%Y-%m-%d')

            result.append((symbol, from_date, today))

        return result

    def update_stock_status(
        self,
        symbol: str,
        new_date: Optional[str],
        status: str,
        error_message: Optional[str] = None
    ):
        """
        Update stock status and metadata

        Args:
            symbol: Stock symbol
            new_date: New last_updated_date (only updated on success)
            status: 'success' or 'failed'
            error_message: Error message if failed
        """
        cursor = self.conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if status == 'success' and new_date:
            # Update date, status, clear error
            cursor.execute("""
                UPDATE data_updates
                SET last_updated_date = ?,
                    last_run_timestamp = ?,
                    status = ?,
                    error_message = NULL
                WHERE symbol = ?
            """, (new_date, now, status, symbol))
        else:
            # Update status and error only, keep old date
            cursor.execute("""
                UPDATE data_updates
                SET last_run_timestamp = ?,
                    status = ?,
                    error_message = ?
                WHERE symbol = ?
            """, (now, status, error_message, symbol))

        self.conn.commit()

    def get_failed_stocks(self) -> List[Tuple[str, str, str]]:
        """
        Get list of stocks that failed in last update

        Returns:
            List of tuples: (symbol, from_date, to_date)
        """
        cursor = self.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')

        query = """
            SELECT symbol, last_updated_date
            FROM data_updates
            WHERE status = 'failed'
            ORDER BY symbol
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            symbol = row['symbol']
            last_updated_str = row['last_updated_date']

            # Parse last_updated_date
            last_updated = datetime.strptime(last_updated_str, '%Y-%m-%d')

            # Calculate from_date (last_updated + 1 day)
            from_date_dt = last_updated + timedelta(days=1)
            from_date = from_date_dt.strftime('%Y-%m-%d')

            result.append((symbol, from_date, today))

        return result

    def get_run_statistics(self) -> Dict[str, int]:
        """
        Get statistics about current state

        Returns:
            Dict with counts:
                - total: Total stocks
                - up_to_date: Stocks with last_updated_date == today
                - needs_update: Stocks with gaps
                - failed: Stocks with failed status
        """
        cursor = self.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')

        # Total stocks
        cursor.execute("SELECT COUNT(*) as count FROM data_updates")
        total = cursor.fetchone()['count']

        # Up to date
        cursor.execute(
            "SELECT COUNT(*) as count FROM data_updates WHERE last_updated_date = ?",
            (today,)
        )
        up_to_date = cursor.fetchone()['count']

        # Needs update
        cursor.execute(
            "SELECT COUNT(*) as count FROM data_updates WHERE last_updated_date < ?",
            (today,)
        )
        needs_update = cursor.fetchone()['count']

        # Failed
        cursor.execute(
            "SELECT COUNT(*) as count FROM data_updates WHERE status = 'failed'"
        )
        failed = cursor.fetchone()['count']

        return {
            'total': total,
            'up_to_date': up_to_date,
            'needs_update': needs_update,
            'failed': failed
        }

    def bootstrap_from_csvs(self, csv_directory: str, symbols: List[str]):
        """
        Bootstrap metadata from existing CSV files

        Args:
            csv_directory: Path to directory containing CSV files
            symbols: List of symbols to bootstrap
        """
        cursor = self.conn.cursor()

        for symbol in symbols:
            csv_path = os.path.join(csv_directory, f"{symbol}.csv")

            if not os.path.exists(csv_path):
                logger.warning(f"CSV not found for {symbol}: {csv_path}")
                continue

            try:
                # Read CSV to find last date
                df = pd.read_csv(csv_path)
                if len(df) == 0:
                    logger.warning(f"Empty CSV for {symbol}")
                    continue

                # Assume 'Date' column exists
                last_date = df['Date'].max()

                # Insert or update
                cursor.execute("""
                    INSERT INTO data_updates (symbol, last_updated_date, status)
                    VALUES (?, ?, 'success')
                    ON CONFLICT(symbol) DO UPDATE SET
                        last_updated_date = excluded.last_updated_date,
                        status = 'success',
                        error_message = NULL
                """, (symbol, last_date))

                logger.info(f"Bootstrapped {symbol} with last_date={last_date}")

            except Exception as e:
                logger.error(f"Failed to bootstrap {symbol}: {e}")
                continue

        self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
