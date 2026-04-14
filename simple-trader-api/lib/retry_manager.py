"""
Retry Manager

Handles retry logic for failed stocks with exponential backoff.
"""

import logging
import time
from typing import List
from lib.data_fetcher import DataFetcher

logger = logging.getLogger(__name__)


class RetryManager:
    """Handles retry logic for failed stocks"""

    def __init__(self, metadata_db, nubra_handler, csv_base_path: str,
                 max_retries: int = 3, backoff_schedule: List[int] = None):
        """
        Initialize retry manager.

        Args:
            metadata_db: UpdateMetadataDB instance
            nubra_handler: NubraAPIHandler instance
            csv_base_path: Base path to CSV files
            max_retries: Maximum retry attempts
            backoff_schedule: Wait times between retries (seconds)
        """
        self.db = metadata_db
        self.nubra = nubra_handler
        self.csv_base_path = csv_base_path
        self.max_retries = max_retries
        self.backoff_schedule = backoff_schedule or [5, 10, 20]

    def retry_failed_stocks(self):
        """
        Retry all stocks marked as 'failed' in database.

        Returns:
            Tuple of (success_count, failed_count)
        """
        failed_stocks = self.db.get_failed_stocks()

        if not failed_stocks:
            logger.info("No failed stocks to retry")
            return (0, 0)

        logger.info(f"Retrying {len(failed_stocks)} failed stocks...")

        success_count = 0
        failed_count = 0

        for symbol, from_date, to_date in failed_stocks:
            if self._retry_with_backoff(symbol, from_date, to_date):
                logger.info(f"✓ {symbol} succeeded on retry")
                success_count += 1
            else:
                logger.warning(f"✗ {symbol} failed after {self.max_retries} retries")
                failed_count += 1

        return (success_count, failed_count)

    def _retry_with_backoff(self, symbol: str, from_date: str, to_date: str) -> bool:
        """
        Retry a single stock with exponential backoff.

        Args:
            symbol: Stock symbol
            from_date: Start date
            to_date: End date

        Returns:
            True if succeeded, False if all retries failed
        """
        fetcher = DataFetcher(self.nubra, self.csv_base_path)

        for attempt in range(1, self.max_retries + 1):
            try:
                # Wait with exponential backoff (skip on first attempt)
                if attempt > 1:
                    wait_time = self.backoff_schedule[attempt - 2]
                    logger.debug(f"{symbol}: Waiting {wait_time}s before retry {attempt}")
                    time.sleep(wait_time)

                # Attempt fetch
                result = fetcher.fetch_and_append(symbol, from_date, to_date)

                if result['status'] == 'success':
                    self.db.update_stock_status(symbol, to_date, 'success')
                    return True

            except Exception as e:
                logger.warning(f"{symbol}: Retry attempt {attempt} failed: {e}")
                if attempt == self.max_retries:
                    self.db.update_stock_status(
                        symbol, None, 'failed', str(e)
                    )

        return False
