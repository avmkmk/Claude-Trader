# SimpleTrader Scripts

This directory contains utility scripts for data scraping, backtesting, and strategy comparison.

## Core Scripts

### `compare_strategy.py` - Generic Strategy Comparison CLI ⭐

**Purpose**: Compare ANY strategy across multiple timeframes for ANY symbol.

**Basic Usage**:
```bash
python scripts/compare_strategy.py \
  --symbol <SYMBOL> \
  --strategy-module <PATH> \
  --strategy-class <CLASS_NAME>
```

**Required Arguments**:
- `--symbol`: Trading symbol (e.g., HDFCBANK, RELIANCE, INFY, TCS)
- `--strategy-module`: Path to Python file (e.g., strategies/sma_crossover.py)
- `--strategy-class`: Class name (e.g., SMACrossoverStrategy)

**Optional Arguments**:
- `--intervals`: Timeframes to test (default: 15m 1h 4h 1d)
- `--strategy-params`: JSON dict of parameters (default: {})
- `--initial-cash`: Capital in Rs (default: 5000000 = 50 lakhs)
- `--commission`: Commission rate (default: 0.001 = 0.1%)

**Example 1**: SMA Crossover on HDFCBANK (all timeframes)
```bash
python scripts/compare_strategy.py \
  --symbol HDFCBANK \
  --strategy-module strategies/sma_crossover.py \
  --strategy-class SMACrossoverStrategy
```

**Example 2**: RSI Mean Reversion with custom parameters
```bash
python scripts/compare_strategy.py \
  --symbol RELIANCE \
  --strategy-module strategies/rsi_mean_reversion_india.py \
  --strategy-class RSIMeanReversionIndia \
  --strategy-params '{"rsi_period": 21, "rsi_oversold": 25, "rsi_exit": 55}'
```

**Example 3**: Test single timeframe
```bash
python scripts/compare_strategy.py \
  --symbol INFY \
  --strategy-module strategies/sma_crossover.py \
  --strategy-class SMACrossoverStrategy \
  --intervals 1d
```

**Example 4**: Custom capital and commission
```bash
python scripts/compare_strategy.py \
  --symbol TCS \
  --strategy-module strategies/sma_crossover.py \
  --strategy-class SMACrossoverStrategy \
  --initial-cash 1000000 \
  --commission 0.0015
```

**What It Does**:
1. Dynamically loads the strategy class from the specified Python file
2. Tests the strategy on each timeframe (15m, 1h, 4h, 1d)
3. Runs backtest with backtrader engine
4. Calculates performance metrics (Sharpe, returns, drawdown, win rate)
5. Displays comparison table across all timeframes
6. Identifies the best-performing timeframe

---

### `strategy_comparator.py` - Core Comparison Engine

**Purpose**: Internal library used by `compare_strategy.py` and custom scripts.

**Key Function**: `run_strategy_comparison(symbol, data_path_template, strategy_module_path, strategy_class_name, intervals, strategy_params, initial_cash, commission)`

**Note**: You typically don't call this directly - use `compare_strategy.py` instead.

---

## Data Management Scripts

### `hdfc_multi_timeframe_scraper.py` - Multi-Timeframe Data Scraper

**Purpose**: Scrapes HDFCBANK data across multiple timeframes (15m, 1h, 4h, 1d) for 365 days.

**Usage**:
```bash
# Scrape 365 days (default)
python scripts/hdfc_multi_timeframe_scraper.py

# Scrape 90 days
python scripts/hdfc_multi_timeframe_scraper.py --days 90

# Override chunk size
python scripts/hdfc_multi_timeframe_scraper.py --chunk 14
```

**Features**:
- Intelligent rate limiting (60 requests/minute)
- Automatic chunking for intraday intervals
- Converts prices from paise to rupees
- Saves to `scripts/data/HDFCBANK_365days_{interval}.csv`

---

### `batch_data_scraper.py` - Batch Symbol Scraper

**Purpose**: Scrapes 365-day historical data for multiple Nifty 50 symbols.

**Usage**:
```bash
python scripts/batch_data_scraper.py
```

**Symbols**: RELIANCE, INFY, HDFCBANK, TCS, ICICIBANK, BHARTIARTL, ITC, TATASTEEL, SBIN, WIPRO

**Output**: `data/{symbol}_365days.csv` (daily OHLCV data)

---

### `validate_data.py` - Data Quality Validator

**Purpose**: Validates scraped CSV files for integrity and completeness.

**Usage**:
```bash
python scripts/validate_data.py
```

**Checks**:
- File existence
- Row count (240-270 for 365 days)
- Null values
- Date ranges

---

## Testing Scripts

### `test_nubra_intervals.py` - Nubra API Interval Tester

**Purpose**: Tests different interval formats with Nubra API.

**Usage**:
```bash
python scripts/test_nubra_intervals.py
```

---

## Data File Structure

Historical data is stored in the parent folder:
```
historical_Indian_equity_data/
├── daily/eod2/                 # 3318 stocks (daily OHLCV)
├── intraday/corrected/         # 55 validated stocks (with corrections applied)
├── intraday/raw/              # ~556 stocks (use with caution)
└── validation_reports/        # Data validation reports
```

### For Backtesting
- **Daily data**: `../historical_Indian_equity_data/daily/eod2/{SYMBOL}.csv`
- **Intraday data**: `../historical_Indian_equity_data/intraday/corrected/{SYMBOL}/{TF}/{TF}.csv`

**CSV Format**: Index is datetime, columns are `open, high, low, close, volume`

---

## Quick Reference

### Compare Strategy on Symbol
```bash
python scripts/compare_strategy.py \
  --symbol <SYMBOL> \
  --strategy-module strategies/<STRATEGY_FILE>.py \
  --strategy-class <StrategyClassName>
```

### Scrape Multi-Timeframe Data
```bash
python scripts/hdfc_multi_timeframe_scraper.py
```

### Scrape Daily Data for 10 Symbols
```bash
python scripts/batch_data_scraper.py
```

### Validate Data Quality
```bash
python scripts/validate_data.py
```

---

## Available Strategies

| Strategy File | Class Name | Type | Parameters |
|---------------|------------|------|------------|
| `strategies/sma_crossover.py` | `SMACrossoverStrategy` | Momentum | fast_period, slow_period |
| `strategies/rsi_mean_reversion_india.py` | `RSIMeanReversionIndia` | Mean Reversion | rsi_period, rsi_oversold, rsi_exit, bb_period, bb_std |

See `strategies/README.md` for complete list and templates.

---

## Troubleshooting

### Error: "Data file not found"
**Cause**: CSV file missing for symbol/interval combination
**Solution**: Check data location:
- Daily data: `../historical_Indian_equity_data/daily/eod2/{SYMBOL}.csv`
- Intraday: `../historical_Indian_equity_data/intraday/corrected/{SYMBOL}/{TF}/{TF}.csv`
- Or run scrapers in `scripts/scrapers/` to fetch new data

### Error: "Strategy class 'XXX' not found"
**Cause**: Class name doesn't match or file path incorrect
**Solution**: Check exact class name (case-sensitive) and verify file exists

### Error: "Invalid JSON in --strategy-params"
**Cause**: Malformed JSON string
**Solution**: Use single quotes around JSON, double quotes inside:
```bash
--strategy-params '{"fast_period": 10, "slow_period": 30}'
```

### Error: "No trades executed"
**Cause**: Strategy conditions not met in timeframe
**Solution**: Try different timeframe or adjust parameters

---

## Next Steps

1. **Run First Backtest**: Use `compare_strategy.py` with HDFCBANK + SMA
2. **Analyze Results**: Focus on Sharpe ratio and max drawdown
3. **Optimize Parameters**: Test different parameter combinations
4. **Validate on Multiple Symbols**: Ensure strategy is robust

See `docs/quick_start/backtest_comparison.md` for a 5-minute quick start guide.
