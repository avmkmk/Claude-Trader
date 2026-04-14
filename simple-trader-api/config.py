"""
Configuration for Daily Data Update Pipeline
"""

CONFIG = {
    # Paths (relative to simple-trader-api directory)
    'csv_base_path': '../../../../SimpleTraderExternal/data/daily/eod2',
    'stock_list_path': 'data/nifty_750.csv',
    'db_path': 'data/dashboard.db',
    'log_file': 'data_updates.log',

    # Nubra API settings
    'nubra_env': 'PROD',
    'api_timeout': 30,  # seconds

    # Parallel processing
    'num_workers': 5,  # Conservative to avoid rate limits
    'batch_size': 50,  # Stocks per progress update

    # Retry settings
    'max_retries': 3,
    'retry_backoff': [5, 10, 20],  # seconds between retries

    # Data validation
    'max_price_change': 0.20,  # 20% circuit breaker
    'min_price': 0.10,
    'max_price': 100000,

    # NSE Market Holidays 2026 (update annually)
    'nse_holidays_2026': [
        '2026-01-26',  # Republic Day
        '2026-03-14',  # Holi
        '2026-04-10',  # Good Friday
        '2026-08-15',  # Independence Day
        '2026-10-02',  # Gandhi Jayanti
        '2026-11-01',  # Diwali
    ]
}
