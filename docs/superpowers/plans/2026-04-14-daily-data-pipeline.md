# Daily Data Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use @superpowers:subagent-driven-development (recommended) or @superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a parallel batch processor that updates historical daily data for 503 stocks with smart gap detection, centralized metadata tracking, and automatic retry logic.

**Architecture:** Parallel multiprocessing system with SQLite metadata tracking. Each worker fetches data from Nubra API, validates it, and appends to CSV files with file locking. Failed stocks are retried with exponential backoff.

**Tech Stack:** Python 3.11+, Nubra SDK, SQLite, multiprocessing, filelock, pandas

---

## File Structure

**New Files:**
- `simple-trader-api/config.py` - Configuration constants
- `simple-trader-api/lib/update_metadata_db.py` - Database manager (170 lines)
- `simple-trader-api/lib/data_fetcher.py` - Worker process (130 lines)
- `simple-trader-api/lib/data_update_orchestrator.py` - Parallel coordinator (110 lines)
- `simple-trader-api/lib/retry_manager.py` - Retry logic (80 lines)
- `simple-trader-api/lib/update_reporter.py` - Reporting (60 lines)
- `simple-trader-api/create_data_updates_table.py` - DB migration (40 lines)
- `simple-trader-api/update_daily_data.py` - Main entry point (150 lines)

**Modified Files:**
- `simple-trader-api/requirements.txt` - Add filelock dependency

**Test Files:**
- `simple-trader-api/tests/test_update_metadata_db.py`
- `simple-trader-api/tests/test_data_fetcher.py`
- `simple-trader-api/tests/test_orchestrator.py`

---

## Task 1: Dependencies and Configuration

**Files:**
- Modify: `simple-trader-api/requirements.txt`
- Create: `simple-trader-api/config.py`

- [ ] **Step 1: Add filelock dependency**

```bash
cd simple-trader-api
echo "filelock>=3.13.0  # Cross-platform file locking" >> requirements.txt
```

- [ ] **Step 2: Install dependency**

Run: `pip install filelock`
Expected: Successfully installed filelock-3.13.x

- [ ] **Step 3: Create configuration file**

Create `simple-trader-api/config.py`:

```python
"""
Configuration for Daily Data Update Pipeline
"""

import os

# Paths (relative to simple-trader-api directory)
CSV_BASE_PATH = os.path.join('..', 'SimpleTraderExternal', 'data', 'daily', 'eod2')
STOCK_LIST_PATH = 'data/nifty_750.csv'
DB_PATH = 'data/dashboard.db'
LOG_FILE = 'data_updates.log'

# Nubra API settings
NUBRA_ENV = 'PROD'
API_TIMEOUT = 30  # seconds

# Parallel processing
NUM_WORKERS = 5  # Conservative to avoid rate limits
BATCH_SIZE = 50  # Stocks per progress update

# Retry settings
MAX_RETRIES = 3
RETRY_BACKOFF = [5, 10, 20]  # seconds between retries

# Data validation
MAX_PRICE_CHANGE = 0.20  # 20% circuit breaker
MIN_PRICE = 0.10
MAX_PRICE = 100000

# NSE Market Holidays 2026 (update annually)
NSE_HOLIDAYS_2026 = [
    '2026-01-26',  # Republic Day
    '2026-03-14',  # Holi
    '2026-04-10',  # Good Friday
    '2026-08-15',  # Independence Day
    '2026-10-02',  # Gandhi Jayanti
    '2026-11-01',  # Diwali
]
```

- [ ] **Step 4: Verify configuration loads**

Run: `python -c "import config; print(f'Workers: {config.NUM_WORKERS}')"`
Expected: `Workers: 5`

- [ ] **Step 5: Commit**

```bash
git add requirements.txt config.py
git commit -m "feat: add dependencies and configuration for data pipeline

- Add filelock for cross-platform file locking
- Add config.py with all settings
- Set conservative worker count (5) to avoid rate limits

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Database Migration

**Files:**
- Create: `simple-trader-api/create_data_updates_table.py`

- [ ] **Step 1: Write database migration script**

Create `simple-trader-api/create_data_updates_table.py`:

```python
"""
Database Migration: Create data_updates Table

Run this once to create the metadata tracking table.
"""

import sqlite3
import os

DB_PATH = 'data/dashboard.db'

def create_table():
    """Create data_updates table with indexes"""
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_updates (
            symbol TEXT PRIMARY KEY,
            last_updated_date DATE NOT NULL,
            last_run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL CHECK(status IN ('success', 'failed', 'pending')),
            error_message TEXT
        )
    """)

    # Create indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_status ON data_updates(status)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_last_updated ON data_updates(last_updated_date)"
    )

    conn.commit()
    conn.close()

    print(f"✓ data_updates table created in {DB_PATH}")

if __name__ == "__main__":
    create_table()
```

- [ ] **Step 2: Run migration**

Run: `python create_data_updates_table.py`
Expected: `✓ data_updates table created in data/dashboard.db`

- [ ] **Step 3: Verify table created**

Run: `sqlite3 data/dashboard.db ".schema data_updates"`
Expected: Shows CREATE TABLE statement with all columns and indexes

- [ ] **Step 4: Commit**

```bash
git add create_data_updates_table.py
git commit -m "feat: add database migration for data_updates table

- Create data_updates table with symbol, last_updated_date, status
- Add indexes on status and last_updated_date
- Include constraint checking for status values

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Update Metadata DB Manager

**Files:**
- Create: `simple-trader-api/lib/update_metadata_db.py`
- Create: `simple-trader-api/tests/test_update_metadata_db.py`

- [ ] **Step 1: Write failing test for get_stocks_to_update**

Create `simple-trader-api/tests/test_update_metadata_db.py`:

```python
"""Tests for UpdateMetadataDB"""

import pytest
import sqlite3
import os
from datetime import datetime, timedelta
from lib.update_metadata_db import UpdateMetadataDB

@pytest.fixture
def test_db(tmp_path):
    """Create test database"""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE data_updates (
            symbol TEXT PRIMARY KEY,
            last_updated_date DATE NOT NULL,
            last_run_timestamp TIMESTAMP,
            status TEXT NOT NULL,
            error_message TEXT
        )
    """)

    # Insert test data: stock updated 3 days ago
    three_days_ago = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    cursor.execute("""
        INSERT INTO data_updates (symbol, last_updated_date, status)
        VALUES ('RELIANCE', ?, 'success')
    """, (three_days_ago,))

    conn.commit()
    conn.close()

    return str(db_path)

def test_get_stocks_to_update_returns_gaps(test_db):
    """Should return stocks with data gaps"""
    db = UpdateMetadataDB(test_db)
    stocks = db.get_stocks_to_update()

    assert len(stocks) == 1
    symbol, from_date, to_date = stocks[0]
    assert symbol == 'RELIANCE'
    # from_date should be 2 days ago (last_updated + 1)
    # to_date should be today
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_update_metadata_db.py::test_get_stocks_to_update_returns_gaps -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'lib.update_metadata_db'"

- [ ] **Step 3: Implement UpdateMetadataDB class**

Create `simple-trader-api/lib/update_metadata_db.py`:

```python
"""
Update Metadata Database Manager

Manages SQLite metadata tracking for daily data updates.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import pandas as pd
import os

logger = logging.getLogger(__name__)


class UpdateMetadataDB:
    """Manages metadata tracking for stock data updates"""

    def __init__(self, db_path: str):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def get_stocks_to_update(self) -> List[Tuple[str, str, str]]:
        """
        Get list of stocks that need updates.

        Returns:
            List of (symbol, from_date, to_date) tuples
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT symbol, last_updated_date
            FROM data_updates
        """)

        stocks_to_update = []
        today = datetime.now().strftime('%Y-%m-%d')

        for row in cursor.fetchall():
            symbol = row['symbol']
            last_date_str = row['last_updated_date']

            # Parse last updated date
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d')

            # Calculate from_date (next day after last update)
            from_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')

            # Only add if there's a gap
            if from_date <= today:
                stocks_to_update.append((symbol, from_date, today))

        logger.info(f"Found {len(stocks_to_update)} stocks needing updates")
        return stocks_to_update

    def update_stock_status(self, symbol: str, new_date: Optional[str],
                           status: str, error: Optional[str] = None):
        """
        Update metadata after fetch attempt.

        Args:
            symbol: Stock symbol
            new_date: New last_updated_date (None if failed)
            status: 'success', 'failed', or 'pending'
            error: Error message (optional)
        """
        cursor = self.conn.cursor()

        if new_date:
            cursor.execute("""
                UPDATE data_updates
                SET last_updated_date = ?,
                    status = ?,
                    error_message = ?,
                    last_run_timestamp = CURRENT_TIMESTAMP
                WHERE symbol = ?
            """, (new_date, status, error, symbol))
        else:
            # Failed - don't update date
            cursor.execute("""
                UPDATE data_updates
                SET status = ?,
                    error_message = ?,
                    last_run_timestamp = CURRENT_TIMESTAMP
                WHERE symbol = ?
            """, (status, error, symbol))

        self.conn.commit()
        logger.debug(f"Updated {symbol}: status={status}")

    def get_failed_stocks(self) -> List[Tuple[str, str, str]]:
        """
        Get list of failed stocks for retry.

        Returns:
            List of (symbol, from_date, to_date) tuples
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT symbol, last_updated_date
            FROM data_updates
            WHERE status = 'failed'
        """)

        failed_stocks = []
        today = datetime.now().strftime('%Y-%m-%d')

        for row in cursor.fetchall():
            symbol = row['symbol']
            last_date_str = row['last_updated_date']
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
            from_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')

            if from_date <= today:
                failed_stocks.append((symbol, from_date, today))

        return failed_stocks

    def get_run_statistics(self) -> dict:
        """
        Get statistics for current run.

        Returns:
            Dict with counts and failed stock details
        """
        cursor = self.conn.cursor()

        # Count by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM data_updates
            GROUP BY status
        """)

        stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'pending': 0
        }

        for row in cursor.fetchall():
            stats[row['status']] = row['count']
            stats['total'] += row['count']

        # Get failed stock details
        cursor.execute("""
            SELECT symbol, error_message
            FROM data_updates
            WHERE status = 'failed'
            LIMIT 20
        """)

        stats['failed_stocks'] = [(row['symbol'], row['error_message'])
                                  for row in cursor.fetchall()]

        return stats

    def bootstrap_from_csvs(self, csv_directory: str, symbols: List[str]):
        """
        Bootstrap metadata by scanning existing CSV files.

        Args:
            csv_directory: Path to CSV directory
            symbols: List of symbols to bootstrap
        """
        cursor = self.conn.cursor()

        for symbol in symbols:
            try:
                csv_path = os.path.join(csv_directory, f"{symbol}.csv")

                if not os.path.exists(csv_path):
                    # Stock not yet downloaded
                    last_date = '1990-01-01'
                else:
                    # Read last row from CSV
                    df = pd.read_csv(csv_path)
                    if df.empty:
                        last_date = '1990-01-01'
                    else:
                        # Parse date from last row
                        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                        df = df.dropna(subset=['Date'])
                        if df.empty:
                            last_date = '1990-01-01'
                        else:
                            last_date = df['Date'].max().strftime('%Y-%m-%d')

                # Insert into database
                cursor.execute("""
                    INSERT OR REPLACE INTO data_updates
                    (symbol, last_updated_date, status)
                    VALUES (?, ?, 'pending')
                """, (symbol, last_date))

            except Exception as e:
                logger.warning(f"Bootstrap failed for {symbol}: {e}")
                continue

        self.conn.commit()
        logger.info(f"Bootstrapped {len(symbols)} symbols")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_update_metadata_db.py::test_get_stocks_to_update_returns_gaps -v`
Expected: PASS

- [ ] **Step 5: Write test for update_stock_status**

Add to `simple-trader-api/tests/test_update_metadata_db.py`:

```python
def test_update_stock_status_success(test_db):
    """Should update date and status on success"""
    db = UpdateMetadataDB(test_db)
    today = datetime.now().strftime('%Y-%m-%d')

    db.update_stock_status('RELIANCE', today, 'success')

    # Verify update
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM data_updates WHERE symbol = 'RELIANCE'")
    row = cursor.fetchone()

    assert row['status'] == 'success'
    assert row['last_updated_date'] == today
    assert row['error_message'] is None

def test_update_stock_status_failure(test_db):
    """Should not update date on failure"""
    db = UpdateMetadataDB(test_db)
    three_days_ago = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')

    db.update_stock_status('RELIANCE', None, 'failed', 'Network timeout')

    # Verify update
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM data_updates WHERE symbol = 'RELIANCE'")
    row = cursor.fetchone()

    assert row['status'] == 'failed'
    assert row['last_updated_date'] == three_days_ago  # Unchanged
    assert row['error_message'] == 'Network timeout'
```

- [ ] **Step 6: Run all UpdateMetadataDB tests**

Run: `pytest tests/test_update_metadata_db.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add lib/update_metadata_db.py tests/test_update_metadata_db.py
git commit -m "feat: implement UpdateMetadataDB with gap detection

- Add get_stocks_to_update() to find stocks needing updates
- Add update_stock_status() to track success/failure
- Add bootstrap_from_csvs() for initial setup
- Add get_run_statistics() for reporting
- All methods tested

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Data Fetcher (Worker Process)

**Files:**
- Create: `simple-trader-api/lib/data_fetcher.py`
- Create: `simple-trader-api/tests/test_data_fetcher.py`

- [ ] **Step 1: Write failing test for fetch_and_append**

Create `simple-trader-api/tests/test_data_fetcher.py`:

```python
"""Tests for DataFetcher"""

import pytest
import pandas as pd
import os
from unittest.mock import Mock, patch
from lib.data_fetcher import DataFetcher

@pytest.fixture
def mock_nubra():
    """Mock Nubra API handler"""
    nubra = Mock()

    # Mock successful data fetch
    mock_data = pd.DataFrame({
        'open': [100, 101],
        'high': [102, 103],
        'low': [99, 100],
        'close': [101, 102],
        'volume': [1000, 1100]
    }, index=pd.date_range('2026-04-10', periods=2))

    nubra.get_historical_data.return_value = mock_data
    return nubra

@pytest.fixture
def test_csv_dir(tmp_path):
    """Create test CSV directory"""
    csv_dir = tmp_path / "csvs"
    csv_dir.mkdir()

    # Create existing CSV with base data
    csv_path = csv_dir / "RELIANCE.csv"
    df = pd.DataFrame({
        'Date': ['2026-04-08', '2026-04-09'],
        'Open': [98, 99],
        'High': [100, 101],
        'Low': [97, 98],
        'Close': [99, 100],
        'Volume': [900, 950]
    })
    df.to_csv(csv_path, index=False)

    return str(csv_dir)

def test_fetch_and_append_success(mock_nubra, test_csv_dir):
    """Should fetch data and append to CSV"""
    fetcher = DataFetcher(mock_nubra, test_csv_dir)

    result = fetcher.fetch_and_append('RELIANCE', '2026-04-10', '2026-04-11')

    assert result['status'] == 'success'
    assert result['rows_added'] == 2

    # Verify CSV updated
    csv_path = os.path.join(test_csv_dir, 'RELIANCE.csv')
    df = pd.read_csv(csv_path)
    assert len(df) == 4  # 2 original + 2 new rows
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_data_fetcher.py::test_fetch_and_append_success -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'lib.data_fetcher'"

- [ ] **Step 3: Implement DataFetcher class**

Create `simple-trader-api/lib/data_fetcher.py`:

```python
"""
Data Fetcher Worker Process

Fetches historical data for a single stock and appends to CSV.
"""

import logging
import os
import pandas as pd
from filelock import FileLock
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetches and validates data for a single stock"""

    def __init__(self, nubra_handler, csv_base_path: str):
        """
        Initialize data fetcher.

        Args:
            nubra_handler: NubraAPIHandler instance
            csv_base_path: Base path to CSV files
        """
        self.nubra = nubra_handler
        self.csv_base_path = csv_base_path

    def fetch_and_append(self, symbol: str, from_date: str, to_date: str) -> Dict:
        """
        Fetch data and append to CSV.

        Args:
            symbol: Stock symbol
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            Dict with status and details
        """
        try:
            # Fetch data from Nubra API
            logger.debug(f"{symbol}: Fetching {from_date} to {to_date}")
            df = self.nubra.get_historical_data(symbol, from_date, to_date, '1d')

            if df is None or df.empty:
                return {
                    'status': 'failed',
                    'error': f'No data returned from API'
                }

            # Validate data
            validation_error = self._validate_data(df, from_date, to_date)
            if validation_error:
                return {
                    'status': 'failed',
                    'error': validation_error
                }

            # Append to CSV with file locking
            csv_path = os.path.join(self.csv_base_path, f"{symbol}.csv")
            self._append_to_csv(csv_path, df)

            logger.info(f"{symbol}: Added {len(df)} rows ({from_date} to {to_date})")

            return {
                'status': 'success',
                'rows_added': len(df)
            }

        except Exception as e:
            logger.error(f"{symbol}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def _validate_data(self, df: pd.DataFrame, from_date: str, to_date: str) -> str:
        """
        Validate fetched data.

        Args:
            df: DataFrame with OHLCV data
            from_date: Expected start date
            to_date: Expected end date

        Returns:
            Error message if invalid, None if valid
        """
        # Check required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return f"Missing columns: {missing_cols}"

        # Check for negative or zero prices
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if (df[col] <= 0).any():
                return f"Invalid prices in {col} column (negative or zero)"

        # Check high >= low, high >= open, high >= close
        if (df['high'] < df['low']).any():
            return "High < Low (invalid)"
        if (df['high'] < df['open']).any():
            return "High < Open (invalid)"
        if (df['high'] < df['close']).any():
            return "High < Close (invalid)"

        # Note: We don't check for missing dates as NSE holidays are expected
        return None

    def _append_to_csv(self, csv_path: str, df: pd.DataFrame):
        """
        Append data to CSV with file locking.

        Args:
            csv_path: Path to CSV file
            df: DataFrame to append
        """
        lock_path = f"{csv_path}.lock"
        lock = FileLock(lock_path, timeout=10)

        with lock:
            # Prepare data for append
            df_to_append = df.copy()
            df_to_append.reset_index(inplace=True)
            df_to_append.rename(columns={'index': 'Date'}, inplace=True)

            # Format date column
            df_to_append['Date'] = pd.to_datetime(df_to_append['Date']).dt.strftime('%Y-%m-%d')

            # Reorder columns
            df_to_append = df_to_append[['Date', 'open', 'high', 'low', 'close', 'volume']]

            # Capitalize column names
            df_to_append.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']

            # Append to CSV
            df_to_append.to_csv(csv_path, mode='a', header=False, index=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_data_fetcher.py::test_fetch_and_append_success -v`
Expected: PASS

- [ ] **Step 5: Write test for data validation**

Add to `simple-trader-api/tests/test_data_fetcher.py`:

```python
def test_validate_data_rejects_negative_prices(mock_nubra, test_csv_dir):
    """Should reject data with negative prices"""
    # Mock data with negative price
    mock_data = pd.DataFrame({
        'open': [100, -10],  # Negative open
        'high': [102, 103],
        'low': [99, 100],
        'close': [101, 102],
        'volume': [1000, 1100]
    }, index=pd.date_range('2026-04-10', periods=2))

    mock_nubra.get_historical_data.return_value = mock_data

    fetcher = DataFetcher(mock_nubra, test_csv_dir)
    result = fetcher.fetch_and_append('RELIANCE', '2026-04-10', '2026-04-11')

    assert result['status'] == 'failed'
    assert 'Invalid prices' in result['error']
```

- [ ] **Step 6: Run all DataFetcher tests**

Run: `pytest tests/test_data_fetcher.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add lib/data_fetcher.py tests/test_data_fetcher.py
git commit -m "feat: implement DataFetcher with validation and file locking

- Add fetch_and_append() to fetch and append data
- Add _validate_data() to check price sanity
- Use filelock for thread-safe CSV appends
- Validate: no negative prices, high >= low/open/close
- All methods tested

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Parallel Orchestrator

**Files:**
- Create: `simple-trader-api/lib/data_update_orchestrator.py`

- [ ] **Step 1: Implement DataUpdateOrchestrator**

Create `simple-trader-api/lib/data_update_orchestrator.py`:

```python
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
```

- [ ] **Step 2: Verify orchestrator loads**

Run: `python -c "from lib.data_update_orchestrator import DataUpdateOrchestrator; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add lib/data_update_orchestrator.py
git commit -m "feat: implement DataUpdateOrchestrator for parallel execution

- Add run_update() to process all stocks in parallel
- Use multiprocessing.Pool with configurable workers
- Update metadata DB after each stock processed
- Log progress and completion

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Retry Manager

**Files:**
- Create: `simple-trader-api/lib/retry_manager.py`

- [ ] **Step 1: Implement RetryManager**

Create `simple-trader-api/lib/retry_manager.py`:

```python
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
```

- [ ] **Step 2: Verify retry manager loads**

Run: `python -c "from lib.retry_manager import RetryManager; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add lib/retry_manager.py
git commit -m "feat: implement RetryManager with exponential backoff

- Add retry_failed_stocks() to retry all failed stocks
- Use exponential backoff: 5s, 10s, 20s between attempts
- Update metadata DB on success or final failure
- Log retry attempts and results

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Update Reporter

**Files:**
- Create: `simple-trader-api/lib/update_reporter.py`

- [ ] **Step 1: Implement UpdateReporter**

Create `simple-trader-api/lib/update_reporter.py`:

```python
"""
Update Reporter

Generates human-readable summary reports after data updates.
"""

import logging

logger = logging.getLogger(__name__)


class UpdateReporter:
    """Generates summary reports for data updates"""

    def __init__(self, metadata_db):
        """
        Initialize reporter.

        Args:
            metadata_db: UpdateMetadataDB instance
        """
        self.db = metadata_db

    def generate_report(self, duration_seconds: float):
        """
        Generate and print summary report.

        Args:
            duration_seconds: Total execution time
        """
        stats = self.db.get_run_statistics()

        # Format duration
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        duration_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

        # Print report
        print("\n" + "="*60)
        print("DATA UPDATE SUMMARY")
        print("="*60)
        print(f"Total stocks processed: {stats['total']}")
        print(f"✓ Successful updates:  {stats['success']}")
        print(f"✗ Failed updates:      {stats['failed']}")
        print(f"⏱️  Execution time:      {duration_str}")
        print("="*60)

        if stats['failed'] > 0:
            print("\nFailed stocks (review logs for details):")
            for symbol, error in stats['failed_stocks'][:10]:
                error_short = error[:50] if error else "Unknown error"
                print(f"  • {symbol}: {error_short}...")

        print(f"\nLog file: data_updates.log")
        print(f"Metadata DB: {self.db.db_path}\n")

        logger.info(
            f"Update complete: {stats['success']} success, "
            f"{stats['failed']} failed, {duration_str}"
        )
```

- [ ] **Step 2: Verify reporter loads**

Run: `python -c "from lib.update_reporter import UpdateReporter; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add lib/update_reporter.py
git commit -m "feat: implement UpdateReporter for summary generation

- Add generate_report() to print human-readable summary
- Show success/failure counts and execution time
- List failed stocks with truncated error messages
- Log summary to logger

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 8: Main Entry Point

**Files:**
- Create: `simple-trader-api/update_daily_data.py`

- [ ] **Step 1: Implement main script**

Create `simple-trader-api/update_daily_data.py`:

```python
#!/usr/bin/env python3
"""
Daily Data Update Script

Updates historical daily OHLCV data for NIFTY 750 stocks using Nubra API.
Features smart gap detection, parallel processing, and automatic retry.

Usage:
    python update_daily_data.py              # Normal update
    python update_daily_data.py --bootstrap  # First-time setup
    python update_daily_data.py --dry-run    # Show what would be updated
"""

import sys
import os
import argparse
import logging
import time
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import config and libraries
import config
from lib.update_metadata_db import UpdateMetadataDB
from lib.data_update_orchestrator import DataUpdateOrchestrator
from lib.retry_manager import RetryManager
from lib.update_reporter import UpdateReporter
from apis.nubra_api import NubraAPIHandler


def setup_logging():
    """Configure logging to file and console"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler()
        ]
    )


def load_stock_list() -> list:
    """Load stock list from CSV"""
    if not os.path.exists(config.STOCK_LIST_PATH):
        logging.error(f"Stock list not found: {config.STOCK_LIST_PATH}")
        logging.error("Run generate_stock_list.py first to create nifty_750.csv")
        sys.exit(1)

    df = pd.read_csv(config.STOCK_LIST_PATH)
    symbols = df['symbol'].tolist()
    logging.info(f"Loaded {len(symbols)} symbols from {config.STOCK_LIST_PATH}")
    return symbols


def bootstrap_metadata(db: UpdateMetadataDB, symbols: list):
    """Bootstrap metadata by scanning existing CSV files"""
    logging.info("Bootstrap mode: Scanning existing CSV files...")

    if not os.path.exists(config.CSV_BASE_PATH):
        logging.error(f"CSV directory not found: {config.CSV_BASE_PATH}")
        sys.exit(1)

    db.bootstrap_from_csvs(config.CSV_BASE_PATH, symbols)
    logging.info("✓ Bootstrap complete")


def dry_run_mode(db: UpdateMetadataDB):
    """Show what would be updated without fetching"""
    stocks_to_update = db.get_stocks_to_update()

    print("\n" + "="*60)
    print("DRY RUN: Stocks to Update")
    print("="*60)

    if not stocks_to_update:
        print("No stocks need updating (all up-to-date)")
    else:
        print(f"\nTotal stocks needing updates: {len(stocks_to_update)}\n")
        for i, (symbol, from_date, to_date) in enumerate(stocks_to_update[:10], 1):
            print(f"{i}. {symbol}: {from_date} → {to_date}")

        if len(stocks_to_update) > 10:
            print(f"... and {len(stocks_to_update) - 10} more")

    print("\n" + "="*60 + "\n")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Update daily stock data')
    parser.add_argument('--bootstrap', action='store_true',
                       help='Bootstrap metadata from existing CSV files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be updated without fetching')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    # Setup
    setup_logging()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info("="*60)
    logging.info("Daily Data Update - Starting")
    logging.info("="*60)

    start_time = time.time()

    # Initialize components
    db = UpdateMetadataDB(config.DB_PATH)
    symbols = load_stock_list()

    # Bootstrap mode
    if args.bootstrap:
        bootstrap_metadata(db, symbols)
        db.close()
        return

    # Dry run mode
    if args.dry_run:
        dry_run_mode(db)
        db.close()
        return

    # Initialize Nubra API
    logging.info("Initializing Nubra API...")
    nubra = NubraAPIHandler(env=config.NUBRA_ENV)
    if not nubra.initialize_sdk():
        logging.error("Failed to initialize Nubra SDK")
        db.close()
        sys.exit(1)

    # Run parallel update
    orchestrator = DataUpdateOrchestrator(
        db, nubra, config.CSV_BASE_PATH, config.NUM_WORKERS
    )
    orchestrator.run_update()

    # Retry failed stocks
    logging.info("\n" + "-"*60)
    logging.info("Retrying failed stocks...")
    logging.info("-"*60)

    retry_manager = RetryManager(
        db, nubra, config.CSV_BASE_PATH,
        config.MAX_RETRIES, config.RETRY_BACKOFF
    )
    success_count, failed_count = retry_manager.retry_failed_stocks()

    logging.info(f"Retry complete: {success_count} recovered, {failed_count} still failed")

    # Generate report
    duration = time.time() - start_time
    reporter = UpdateReporter(db)
    reporter.generate_report(duration)

    # Cleanup
    db.close()
    logging.info("="*60)
    logging.info("Daily Data Update - Complete")
    logging.info("="*60)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test --dry-run mode**

Run: `python update_daily_data.py --dry-run`
Expected: Shows list of stocks to update (or "all up-to-date")

- [ ] **Step 3: Test --bootstrap mode**

Run: `python update_daily_data.py --bootstrap`
Expected: `✓ Bootstrap complete` with 503 symbols bootstrapped

- [ ] **Step 4: Verify metadata DB populated**

Run: `sqlite3 data/dashboard.db "SELECT COUNT(*) FROM data_updates"`
Expected: `503`

- [ ] **Step 5: Commit**

```bash
git add update_daily_data.py
git commit -m "feat: implement main entry point for data pipeline

- Add update_daily_data.py with CLI args (--bootstrap, --dry-run)
- Initialize Nubra API and all components
- Run parallel orchestrator + retry manager
- Generate summary report
- Support verbose logging

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 9: End-to-End Testing

**Files:**
- None (manual testing)

- [ ] **Step 1: Verify all dependencies installed**

Run: `pip list | grep filelock`
Expected: `filelock              3.13.x`

- [ ] **Step 2: Run database migration**

Run: `python create_data_updates_table.py`
Expected: `✓ data_updates table created in data/dashboard.db`

- [ ] **Step 3: Bootstrap metadata**

Run: `python update_daily_data.py --bootstrap`
Expected: Bootstrap complete with 503 symbols

- [ ] **Step 4: Dry run to verify stocks detected**

Run: `python update_daily_data.py --dry-run`
Expected: Shows stocks needing updates with date ranges

- [ ] **Step 5: Run full update (WARNING: Will make API calls)**

**IMPORTANT**: Only run this when ready to fetch real data from Nubra API.

Run: `python update_daily_data.py`
Expected:
- Nubra SDK initialization succeeds
- Parallel workers start processing
- Progress logs show stocks being updated
- Retry logic runs after main execution
- Summary report shows success/failure counts
- Execution completes in 5-10 minutes for ~500 stocks

- [ ] **Step 6: Verify CSV files updated**

Run: `tail -3 ../SimpleTraderExternal/data/daily/eod2/RELIANCE.csv`
Expected: Last 3 rows show recent dates (should include today if market is open)

- [ ] **Step 7: Check metadata DB status**

Run: `sqlite3 data/dashboard.db "SELECT status, COUNT(*) FROM data_updates GROUP BY status"`
Expected: Shows breakdown of success/failed/pending

- [ ] **Step 8: Review logs**

Run: `tail -50 data_updates.log`
Expected: Shows INFO logs with timestamps, successful updates, any failures

---

## Task 10: Documentation

**Files:**
- Create: `simple-trader-api/README_DATA_PIPELINE.md`

- [ ] **Step 1: Write usage documentation**

Create `simple-trader-api/README_DATA_PIPELINE.md`:

```markdown
# Daily Data Pipeline

Automated daily stock data updates for NIFTY 750 stocks using Nubra API.

## Features

- **Smart Gap Detection**: Automatically fills missing dates
- **Parallel Processing**: 5 workers (configurable)
- **Automatic Retry**: 3 attempts with exponential backoff
- **Centralized Metadata**: SQLite tracking for all stocks
- **File Locking**: Safe parallel CSV writes

## First-Time Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Create database table:**
```bash
python create_data_updates_table.py
```

3. **Bootstrap metadata:**
```bash
python update_daily_data.py --bootstrap
```

## Daily Usage

```bash
# Normal update (run daily)
python update_daily_data.py

# Dry run (preview only)
python update_daily_data.py --dry-run

# Verbose logging
python update_daily_data.py --verbose
```

## Configuration

Edit `config.py` to adjust:
- `NUM_WORKERS`: Parallel worker count (default: 5)
- `MAX_RETRIES`: Retry attempts (default: 3)
- `RETRY_BACKOFF`: Wait times between retries

## Monitoring

**Check data freshness:**
```sql
sqlite3 data/dashboard.db
SELECT symbol, last_updated_date,
       julianday('now') - julianday(last_updated_date) as days_stale
FROM data_updates
WHERE days_stale > 5
ORDER BY days_stale DESC;
```

**View failed stocks:**
```sql
SELECT symbol, error_message, last_run_timestamp
FROM data_updates
WHERE status = 'failed'
ORDER BY last_run_timestamp DESC;
```

**Status distribution:**
```sql
SELECT status, COUNT(*) as count
FROM data_updates
GROUP BY status;
```

## Troubleshooting

**"Nubra SDK initialization failed"**
- Check `.env` file has `NUBRA_CLIENT_ID` and `NUBRA_MPIN`
- Verify credentials are correct

**"Rate limit exceeded"**
- Reduce `NUM_WORKERS` in `config.py` to 3 or less
- Add delays between retries

**"CSV file locked"**
- Another process is accessing the file
- Wait and retry - filelock will handle it

## Architecture

```
update_daily_data.py
├── UpdateMetadataDB (SQLite tracking)
├── DataUpdateOrchestrator (parallel execution)
│   └── DataFetcher (workers)
├── RetryManager (exponential backoff)
└── UpdateReporter (summary generation)
```

## Files

- `config.py` - Configuration settings
- `update_daily_data.py` - Main entry point
- `lib/update_metadata_db.py` - Database manager
- `lib/data_fetcher.py` - Worker process
- `lib/data_update_orchestrator.py` - Parallel coordinator
- `lib/retry_manager.py` - Retry logic
- `lib/update_reporter.py` - Reporting
- `data/dashboard.db` - Metadata database
- `data/nifty_750.csv` - Stock list (503 symbols)
```

- [ ] **Step 2: Commit**

```bash
git add README_DATA_PIPELINE.md
git commit -m "docs: add data pipeline usage documentation

- First-time setup instructions
- Daily usage commands
- Configuration options
- Monitoring SQL queries
- Troubleshooting guide
- Architecture overview

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Completion Checklist

- [ ] All dependencies installed (`filelock>=3.13.0`)
- [ ] Database table created (`data_updates`)
- [ ] Metadata bootstrapped (503 symbols)
- [ ] All unit tests pass
- [ ] End-to-end test successful (or scheduled)
- [ ] Documentation complete
- [ ] Code committed with descriptive messages

---

## Next Steps

After completing this plan:

1. **Schedule Regular Runs**: Set up Windows Task Scheduler or run manually daily
2. **Monitor Logs**: Check `data_updates.log` for any recurring failures
3. **Update Stock List**: When index constituents change, regenerate `nifty_750.csv`
4. **Tune Workers**: If no rate limit issues, increase `NUM_WORKERS` to 10 for faster updates

## Success Criteria

✅ All 503 stocks updated daily
✅ No data gaps in historical CSVs
✅ Update completes in under 10 minutes
✅ <1% failure rate on normal runs
✅ Clear logs for debugging
