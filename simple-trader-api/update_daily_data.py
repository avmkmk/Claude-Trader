#!/usr/bin/env python3
"""
Daily Data Update Pipeline - Main Entry Point

Orchestrates the complete data update process:
1. Checks for stocks that need updates
2. Fetches missing data from Nubra API
3. Appends new data to CSV files
4. Updates metadata database
5. Handles retries for failed stocks
6. Generates summary report

Usage:
    # Normal mode: Update all stocks
    python update_daily_data.py

    # Bootstrap mode: Scan CSVs and populate metadata DB
    python update_daily_data.py --bootstrap

    # Dry-run mode: Show what would be updated
    python update_daily_data.py --dry-run

    # Verbose logging
    python update_daily_data.py --verbose
"""

import sys
import os
import argparse
import logging
from datetime import datetime
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from lib.update_metadata_db import UpdateMetadataDB
from lib.data_update_orchestrator import DataUpdateOrchestrator
from lib.retry_manager import RetryManager
from lib.update_reporter import UpdateReporter


def setup_logging(verbose: bool = False):
    """
    Configure logging to file and console.

    Args:
        verbose: If True, set log level to DEBUG
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # File handler
    file_handler = logging.FileHandler(config.CONFIG['log_file'])
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))

    # Root logger
    logging.basicConfig(
        level=log_level,
        handlers=[file_handler, console_handler]
    )


def load_stock_list() -> list:
    """
    Load stock symbols from nifty_750.csv.

    Returns:
        List of stock symbols
    """
    stock_list_path = config.CONFIG['stock_list_path']

    if not os.path.exists(stock_list_path):
        logging.error(f"Stock list not found: {stock_list_path}")
        sys.exit(1)

    df = pd.read_csv(stock_list_path)

    # Assume CSV has 'symbol' column
    if 'symbol' not in df.columns:
        logging.error(f"Stock list CSV must have 'symbol' column")
        sys.exit(1)

    symbols = df['symbol'].tolist()
    logging.info(f"Loaded {len(symbols)} stocks from {stock_list_path}")

    return symbols


def bootstrap_metadata(db: UpdateMetadataDB, symbols: list):
    """
    Bootstrap mode: Scan CSV files and populate metadata database.

    Args:
        db: UpdateMetadataDB instance
        symbols: List of stock symbols to scan
    """
    logging.info("=== BOOTSTRAP MODE ===")
    logging.info(f"Scanning {len(symbols)} CSV files...")

    csv_base_path = config.CONFIG['csv_base_path']
    db.bootstrap_from_csvs(csv_base_path, symbols)

    logging.info(f"Bootstrap complete")


def dry_run_mode(db: UpdateMetadataDB):
    """
    Dry-run mode: Show which stocks would be updated.

    Args:
        db: UpdateMetadataDB instance
    """
    logging.info("=== DRY RUN MODE ===")

    tasks = db.get_stocks_to_update()

    if not tasks:
        logging.info("No stocks need updating")
        return

    logging.info(f"\n{len(tasks)} stocks need updating:")
    logging.info("-" * 80)
    logging.info(f"{'Symbol':<15} {'From Date':<12} {'To Date':<12}")
    logging.info("-" * 80)

    for symbol, from_date, to_date in tasks:
        logging.info(f"{symbol:<15} {from_date:<12} {to_date:<12}")

    logging.info("-" * 80)
    logging.info(f"Total: {len(tasks)} stocks")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Daily Data Update Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Normal mode: Update all stocks
  python update_daily_data.py

  # Bootstrap mode: Scan CSVs and populate metadata DB
  python update_daily_data.py --bootstrap

  # Dry-run mode: Show what would be updated
  python update_daily_data.py --dry-run

  # Verbose logging
  python update_daily_data.py --verbose
        """
    )

    parser.add_argument(
        '--bootstrap',
        action='store_true',
        help='Bootstrap mode: Scan CSVs and populate metadata database'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry-run mode: Show what would be updated without making changes'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose (DEBUG level) logging'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    logging.info("=" * 80)
    logging.info("Daily Data Update Pipeline")
    logging.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("=" * 80)

    # Initialize database
    db_path = config.CONFIG['db_path']
    db = UpdateMetadataDB(db_path)
    logging.info(f"Connected to database: {db_path}")

    # Bootstrap mode
    if args.bootstrap:
        symbols = load_stock_list()
        bootstrap_metadata(db, symbols)
        logging.info("Bootstrap complete. Exiting.")
        return

    # Dry-run mode
    if args.dry_run:
        dry_run_mode(db)
        logging.info("Dry-run complete. Exiting.")
        return

    # Normal mode: Run update pipeline
    logging.info("Starting normal update mode...")

    # Initialize Nubra API (import here to avoid protobuf issues in other modes)
    logging.info("Initializing Nubra API...")
    from apis.nubra_api import NubraAPIHandler
    from nubra_python_sdk.start_sdk import NubraEnv

    nubra_env = NubraEnv.PROD if config.CONFIG['nubra_env'] == 'PROD' else NubraEnv.UAT
    nubra_handler = NubraAPIHandler(env=nubra_env)

    if not nubra_handler.initialize_sdk():
        logging.error("Failed to initialize Nubra SDK")
        sys.exit(1)

    logging.info("Nubra API initialized successfully")

    # Run orchestrator
    logging.info("Starting parallel data update orchestrator...")
    orchestrator = DataUpdateOrchestrator(
        metadata_db=db,
        nubra_handler=nubra_handler,
        csv_base_path=config.CONFIG['csv_base_path'],
        num_workers=config.CONFIG['num_workers']
    )

    results = orchestrator.run_update()
    logging.info(f"Orchestrator complete: {len(results)} stocks processed")

    # Run retry manager
    logging.info("Starting retry manager for failed stocks...")
    retry_manager = RetryManager(
        metadata_db=db,
        nubra_handler=nubra_handler,
        csv_base_path=config.CONFIG['csv_base_path'],
        max_retries=config.CONFIG['max_retries'],
        retry_backoff=config.CONFIG['retry_backoff']
    )

    retry_results = retry_manager.run_retries()
    logging.info(f"Retry manager complete: {len(retry_results)} retries attempted")

    # Generate summary report
    logging.info("Generating update summary report...")
    reporter = UpdateReporter(db)
    summary = reporter.generate_summary()

    # Log summary
    logging.info("\n" + "=" * 80)
    logging.info("UPDATE SUMMARY")
    logging.info("=" * 80)
    logging.info(f"Total stocks:    {summary['total_stocks']}")
    logging.info(f"Up to date:      {summary['up_to_date']}")
    logging.info(f"Updated today:   {summary['updated_today']}")
    logging.info(f"Failed:          {summary['failed']}")
    logging.info(f"Never updated:   {summary['never_updated']}")
    logging.info("=" * 80)

    if summary['failed'] > 0:
        logging.info("\nFailed stocks:")
        failed_stocks = reporter.get_failed_stocks()
        for stock in failed_stocks:
            logging.info(f"  {stock['symbol']}: {stock['error_message']}")

    logging.info(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("\nInterrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        logging.exception(f"Fatal error: {e}")
        sys.exit(1)
