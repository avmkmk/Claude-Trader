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
