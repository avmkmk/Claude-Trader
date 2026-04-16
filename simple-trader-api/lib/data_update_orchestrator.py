"""
Data Update Orchestrator

Manages parallel execution of data updates across multiple workers.
"""

import logging
import multiprocessing as mp
from typing import List, Tuple, Dict
from lib.data_fetcher import DataFetcher

logger = logging.getLogger(__name__)


class DataUpdateOrchestrator:
    """Manages parallel execution of data updates"""

    def __init__(self, metadata_db, nubra_handler, csv_base_path: str, num_workers: int = 5):
        """
        Initialize orchestrator.

        Args:
            metadata_db: UpdateMetadataDB instance
            nubra_handler: NubraAPIHandler instance
            csv_base_path: Base path to CSV files
            num_workers: Number of parallel workers
        """
        self.db = metadata_db
        self.nubra = nubra_handler
        self.csv_base_path = csv_base_path
        self.num_workers = num_workers

    def run_update(self) -> List[Tuple[str, Dict]]:
        """
        Run parallel update for all stocks.

        Returns:
            List of (symbol, result) tuples
        """
        # Get stocks to update
        tasks = self.db.get_stocks_to_update()

        if not tasks:
            logger.info("No stocks need updating")
            return []

        logger.info(f"Starting update for {len(tasks)} stocks with {self.num_workers} workers")

        # Process tasks in parallel
        with mp.Pool(self.num_workers) as pool:
            results = pool.starmap(
                self._process_stock,
                tasks
            )

        # Update database with results
        for (symbol, from_date, to_date), result in zip(tasks, results):
            if result['status'] == 'success':
                self.db.update_stock_status(symbol, to_date, 'success')
            else:
                self.db.update_stock_status(
                    symbol, None, 'failed', result.get('error')
                )

        logger.info(f"Update complete: processed {len(results)} stocks")
        return list(zip([t[0] for t in tasks], results))

    def _process_stock(self, symbol: str, from_date: str, to_date: str) -> Dict:
        """
        Worker function: process a single stock.

        Args:
            symbol: Stock symbol
            from_date: Start date
            to_date: End date

        Returns:
            Result dict from DataFetcher
        """
        # Note: Each worker process needs its own NubraAPIHandler instance
        # This is a simplified version - in production, we'd need to
        # reinitialize the handler in each worker process
        fetcher = DataFetcher(self.nubra, self.csv_base_path)
        return fetcher.fetch_and_append(symbol, from_date, to_date)
