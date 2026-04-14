# Daily Data Pipeline Design Specification

**Date**: April 14, 2026
**Author**: Claude Code
**Status**: Approved

## Overview

A manual-run Python script that updates historical daily OHLCV data for NIFTY 750 stocks using the Nubra broker API. Features smart gap detection, parallel processing, and centralized metadata tracking to ensure no data gaps even when updates are missed for several days.

## Problem Statement

Current historical data is stale (18 days old as of April 14, 2026), causing incorrect ATH phase analysis. The system needs a reliable way to keep daily stock data current by:
- Fetching end-of-day data from Nubra API
- Detecting and filling data gaps automatically
- Processing 750 stocks efficiently (parallel execution)
- Tracking update status centrally (no CSV scanning)
- Handling failures gracefully with retry logic

## Requirements

### Functional Requirements
1. **Smart Gap Detection**: Calculate missing date ranges per stock from last_updated_date to today
2. **Parallel Processing**: Fetch 10 stocks simultaneously to minimize total execution time
3. **Centralized Metadata**: SQLite table tracks last update date/status for each stock
4. **Automatic Retry**: Failed stocks are retried 3 times with exponential backoff
5. **Data Validation**: Verify fetched data for missing dates and price sanity
6. **Progress Reporting**: Generate summary with successes, failures, and gaps filled

### Non-Functional Requirements
1. **Performance**: Complete 750 stock update in 5-10 minutes (vs 30-40 sequential)
2. **Reliability**: File locking prevents corruption from parallel writes
3. **Observability**: Structured logging for debugging and audit trail
4. **Maintainability**: Simple configuration file for tuning workers, retries, etc.

## Architecture

### High-Level Design

```
update_daily_data.py (Main Script)
    │
    ├── StockListManager
    │   └── Loads NIFTY 750 symbols from nifty_750.csv
    │
    ├── UpdateMetadataDB (SQLite)
    │   ├── Table: data_updates
    │   │   ├── symbol (TEXT PRIMARY KEY)
    │   │   ├── last_updated_date (DATE)
    │   │   ├── last_run_timestamp (TIMESTAMP)
    │   │   ├── status (TEXT: 'success', 'failed', 'pending')
    │   │   └── error_message (TEXT, nullable)
    │   │
    │   ├── get_stocks_to_update() → List[(symbol, from_date, to_date)]
    │   ├── update_stock_metadata(symbol, new_date, status)
    │   └── bootstrap_from_csvs(csv_directory, symbols)
    │
    ├── DataUpdateOrchestrator
    │   ├── Queries UpdateMetadataDB for stocks needing updates
    │   ├── Creates update tasks (symbol, from_date, to_date)
    │   └── Manages parallel worker pool (multiprocessing)
    │
    ├── DataFetcher (Worker Process)
    │   ├── Uses NubraAPIHandler to fetch historical data
    │   ├── Validates data quality (dates, price sanity)
    │   ├── Appends to CSV files with file locking
    │   └── Updates metadata DB on success/failure
    │
    ├── RetryManager
    │   ├── Queries failed stocks from DB
    │   └── Retries with exponential backoff (5s, 10s, 20s)
    │
    └── UpdateReporter
        ├── Queries metadata DB for run statistics
        └── Generates human-readable summary report
```

### Data Flow

```
1. User runs: python update_daily_data.py
   ↓
2. Initialize NubraAPIHandler (SDK login with env credentials)
   ↓
3. Load NIFTY 750 stock list from nifty_750.csv
   ↓
4. Query metadata DB:
   SELECT symbol, last_updated_date FROM data_updates
   ↓
5. For each symbol:
   - Calculate: from_date = last_updated_date + 1 day
   - Calculate: to_date = today
   - If from_date <= to_date: Add to update queue
   ↓
6. Create worker pool (10 parallel workers)
   ↓
7. Each worker processes one stock at a time:
   ├─ Fetch data from Nubra API (from_date → to_date)
   ├─ Validate: Check for missing dates, price sanity
   ├─ Acquire file lock on CSV
   ├─ Append new rows to CSV
   ├─ Release file lock
   ├─ Update metadata DB:
   │  - last_updated_date = to_date
   │  - status = 'success'
   │  - last_run_timestamp = now()
   └─ Log result (success/failure)
   ↓
8. After all stocks processed:
   Query failed stocks: WHERE status = 'failed'
   ↓
9. Retry each failed stock (up to 3 attempts with backoff)
   ↓
10. Generate summary report:
    - Total stocks: 750
    - Updated successfully: X
    - Failed after retries: Y
    - Data gaps filled: Z days
    - Total time: MM:SS
    ↓
11. Display report and write to log
```

## Component Details

### 1. UpdateMetadataDB (Database Manager)

**Purpose**: Centralized tracking of update status per stock

**Database Schema**:
```sql
CREATE TABLE IF NOT EXISTS data_updates (
    symbol TEXT PRIMARY KEY,
    last_updated_date DATE NOT NULL,
    last_run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL CHECK(status IN ('success', 'failed', 'pending')),
    error_message TEXT
);

CREATE INDEX idx_status ON data_updates(status);
CREATE INDEX idx_last_updated ON data_updates(last_updated_date);
```

**Key Methods**:
- `bootstrap_from_csvs()`: One-time initialization - reads last date from each CSV
- `get_stocks_to_update()`: Returns list of (symbol, from_date, to_date) for stocks with gaps
- `update_stock_status()`: Updates metadata after fetch attempt
- `get_failed_stocks()`: Returns stocks marked as 'failed' for retry
- `get_run_statistics()`: Aggregates stats for reporting

**Location**: `simple-trader-api/data/dashboard.db` (alongside existing database)

### 2. DataFetcher (Worker Process)

**Purpose**: Fetches and validates data for a single stock

**Key Responsibilities**:
- Call Nubra API with date range
- Validate fetched data (completeness, price sanity)
- Append to CSV with thread-safe file locking
- Return success/failure result

**Data Validation Rules**:
- All dates in range must be present (account for market holidays)
- Prices must be positive: open, high, low, close > 0
- High >= Low, High >= Open, High >= Close
- Daily price change <= 20% (circuit breaker check)
- Min price: 0.10, Max price: 100,000

**File Locking**: Uses `fcntl.flock()` on Unix or `msvcrt.locking()` on Windows

### 3. DataUpdateOrchestrator (Parallel Coordinator)

**Purpose**: Manages parallel execution across multiple workers

**Worker Pool**:
- Uses Python's `multiprocessing.Pool`
- Default: 10 workers (configurable)
- Each worker processes one stock at a time
- Results collected and aggregated

**Progress Tracking**:
- Process stocks in batches of 50
- Display progress after each batch
- Show estimated time remaining

### 4. RetryManager (Error Recovery)

**Purpose**: Handles retry logic for failed stocks

**Retry Strategy**:
1. Skip and log failures during main run
2. After all stocks processed, query failed stocks from DB
3. Retry each failed stock with exponential backoff:
   - Attempt 1: Immediate
   - Attempt 2: Wait 5 seconds
   - Attempt 3: Wait 10 seconds
   - Attempt 4: Wait 20 seconds (final)
4. Update DB with final status

**Error Categories**:
- **Retriable**: Network timeouts, rate limits, temporary server errors
- **Non-retriable**: Data validation errors, missing CSV files
- **Fatal**: Authentication failures, invalid credentials

### 5. UpdateReporter (Reporting)

**Purpose**: Generates human-readable execution summary

**Report Contents**:
- Total stocks processed
- Successful updates count
- Failed updates count (with error details)
- Total data gaps filled (in days)
- Execution time
- Log file location

## Configuration

### Stock List (`nifty_750.csv`)

```csv
symbol
RELIANCE
TCS
HDFCBANK
INFY
ICICIBANK
...
(750 total symbols)
```

**Location**: `simple-trader-api/data/nifty_750.csv`

**Generation**: Combine NIFTY 500 + Midcap 150 + Smallcap 100

### Script Configuration (`config.py`)

```python
CONFIG = {
    # Paths
    'csv_base_path': '../SimpleTraderExternal/data/daily/eod2',
    'stock_list_path': 'data/nifty_750.csv',
    'db_path': 'data/dashboard.db',
    'log_file': 'data_updates.log',

    # Nubra API
    'nubra_env': 'PROD',
    'api_timeout': 30,

    # Parallel processing
    'num_workers': 10,
    'batch_size': 50,

    # Retry settings
    'max_retries': 3,
    'retry_backoff': [5, 10, 20],

    # Data validation
    'max_price_change': 0.20,
    'min_price': 0.10,
    'max_price': 100000,
}
```

### Environment Variables

```bash
# Already exists in .env
NUBRA_CLIENT_ID="your_client_id"
NUBRA_MPIN="your_mpin"
```

## Error Handling

### Error Categories

1. **API Errors** (Retriable)
   - Network timeouts
   - Rate limit exceeded (HTTP 429)
   - Temporary server errors (HTTP 5xx)

2. **Data Validation Errors** (Non-retriable)
   - Missing dates in fetched data
   - Invalid prices (negative, zero, extreme)
   - Data format issues

3. **File System Errors** (Retriable)
   - CSV file locked
   - Disk space issues
   - Permission errors

### Logging Strategy

```python
# Structured logging
logging.basicConfig(
    filename='data_updates.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

# Log examples:
# 2026-04-14 16:30:00 | INFO | Starting update for 750 stocks
# 2026-04-14 16:30:05 | INFO | RELIANCE: Fetched 4 days (2026-04-11 to 2026-04-14)
# 2026-04-14 16:30:06 | ERROR | TCS: API timeout after 30s
# 2026-04-14 16:35:00 | INFO | Update complete: 745 success, 5 failed
```

## Usage

### Command-Line Interface

```bash
# Normal daily update (smart gap detection)
python update_daily_data.py

# Bootstrap mode (first-time setup or rebuild metadata)
python update_daily_data.py --bootstrap

# Update specific stocks only
python update_daily_data.py --symbols RELIANCE,TCS,INFY

# Dry run (show what would be updated without fetching)
python update_daily_data.py --dry-run

# Verbose output for debugging
python update_daily_data.py --verbose
```

### First-Time Setup

```bash
# 1. Create NIFTY 750 stock list
# (Manual: Export and save to simple-trader-api/data/nifty_750.csv)

# 2. Run bootstrap to populate metadata
cd simple-trader-api
python update_daily_data.py --bootstrap

# 3. Verify metadata DB
sqlite3 data/dashboard.db
> SELECT COUNT(*) FROM data_updates;  # Should be 750
> SELECT * FROM data_updates LIMIT 5;
```

### Daily Usage

```bash
# Just run the script whenever needed
cd simple-trader-api
python update_daily_data.py

# Review summary report in terminal
# Check logs if any failures: tail -f data_updates.log
```

## Testing Strategy

### Unit Tests

```python
# test_update_metadata_db.py
- test_bootstrap_from_csvs()
- test_get_stocks_to_update()
- test_update_stock_status()

# test_data_fetcher.py
- test_fetch_and_append()
- test_validate_data()
- test_file_locking()

# test_retry_manager.py
- test_exponential_backoff()
- test_max_retries()
```

### Integration Tests

```python
# test_end_to_end.py
- test_full_update_cycle_with_5_stocks()
- test_gap_detection_after_missed_runs()
- test_retry_logic_with_simulated_failures()
```

### Manual Testing

1. **Bootstrap Test**: Verify metadata DB populated correctly
2. **Gap Detection Test**: Manually set last_date to 5 days ago, verify 5 days fetched
3. **Error Handling Test**: Rename a CSV file, verify failure logged and retried
4. **Parallel Execution Test**: Monitor system resources during 750-stock update

### Monitoring Queries

```sql
-- Check data freshness
SELECT symbol, last_updated_date,
       julianday('now') - julianday(last_updated_date) as days_stale
FROM data_updates
WHERE days_stale > 5
ORDER BY days_stale DESC;

-- View recent failures
SELECT symbol, error_message, last_run_timestamp
FROM data_updates
WHERE status = 'failed'
ORDER BY last_run_timestamp DESC;

-- Statistics
SELECT status, COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM data_updates), 2) as pct
FROM data_updates
GROUP BY status;
```

## Implementation Notes

### File Structure

```
simple-trader-api/
├── update_daily_data.py          # Main entry point
├── config.py                      # Configuration
├── data/
│   ├── nifty_750.csv             # Stock list
│   ├── dashboard.db              # Metadata DB
│   └── data_updates.log          # Execution logs
└── lib/
    ├── update_metadata_db.py     # Database manager
    ├── data_fetcher.py           # Worker process
    ├── data_update_orchestrator.py  # Parallel coordinator
    ├── retry_manager.py          # Retry logic
    └── update_reporter.py        # Reporting
```

### Dependencies

```python
# requirements.txt additions
nubra-python-sdk>=1.0.0    # Already exists
filelock>=3.12.0           # For cross-platform file locking
tqdm>=4.65.0              # For progress bars (optional)
```

### Performance Estimates

**Sequential Processing (1 worker)**:
- Time per stock: ~3-5 seconds (API call + validation + file write)
- Total for 750 stocks: 37-62 minutes

**Parallel Processing (10 workers)**:
- Time per stock: ~3-5 seconds
- Total for 750 stocks: 4-7 minutes (10x speedup)

**API Rate Limits**:
- Nubra API: Check documentation for rate limits
- If rate limited, reduce `num_workers` in config

## Success Criteria

1. **Data Freshness**: All 750 stocks updated to latest trading day
2. **No Gaps**: Historical data complete with no missing dates
3. **Performance**: Update completes in under 10 minutes
4. **Reliability**: <1% failure rate on normal runs
5. **Observability**: Clear logs and reports for debugging
6. **Maintainability**: Simple to add/remove stocks from list

## Future Enhancements

1. **Automated Scheduling**: Add Windows Task Scheduler integration
2. **Email Notifications**: Send report via email on completion
3. **Data Quality Dashboard**: Web UI showing data freshness per stock
4. **Incremental Validation**: Verify existing historical data for correctness
5. **Multi-Exchange Support**: Extend to BSE stocks in addition to NSE

## References

- Nubra API Documentation: `apis/nubra_api.py`
- Existing Historical Data: `../SimpleTraderExternal/data/daily/eod2/`
- Database Schema: `simple-trader-api/app/db_migrations.py`
