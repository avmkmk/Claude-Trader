# SimpleTrader Data Pipeline Documentation

## Overview

The SimpleTrader data pipeline is a comprehensive system for managing stock data, watchlist management, and ATH (All-Time High) analysis. It provides:

- **Real-time Data Updates**: Fetches and processes market data with validation and error recovery
- **Watchlist Management**: CRUD operations for tracking selected stocks with historical context
- **ATH Monitoring**: Analyzes stocks for All-Time High reclaim patterns with phase detection
- **Candidate Screening**: Scrapes and evaluates stock candidates from Chartink screeners
- **Database Persistence**: SQLite-based storage with automatic schema management

The pipeline is designed for the Indian equity markets (NSE/BSE) and integrates with the FastAPI backend to provide REST endpoints for the React frontend.

---

## Features

### Core Capabilities

1. **Stock Data Management**
   - Stores and validates historical OHLCV data (Open, High, Low, Close, Volume)
   - Supports 3,318+ stocks from NSE/BSE with split-adjusted pricing
   - Validates data quality before storage

2. **Watchlist Operations**
   - Add/remove stocks with duplicate prevention
   - Symbol validation against historical data
   - Storage of custom notes and metadata

3. **ATH Analysis**
   - Calculates All-Time High values and dates
   - Computes EMA 200 for trend analysis
   - Determines phase classification (Phase 1, 2, or 3)
   - Tracks distance metrics from ATH
   - Real-time analysis for monitoring momentum

4. **Chartink Integration**
   - Automated scraping of stock screeners
   - Deduplication of scraped results
   - Phase-based sorting and filtering
   - Bulk transfer to watchlist

5. **Error Recovery**
   - Retry mechanism with exponential backoff
   - Duplicate detection and handling
   - Comprehensive error logging
   - Database transaction safety

---

## First-Time Setup

### Prerequisites

- Python 3.8+
- SQLite3 (included with Python)
- ChromeDriver (for Chartink scraping)
- Historical data files (see Configuration section)

### Installation Steps

1. **Navigate to the API directory**
   ```bash
   cd simple-trader-api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create environment configuration**
   Create `.env` file in `simple-trader-api/`:
   ```
   NUBRA_CLIENT_ID="your_client_id"
   NUBRA_MPIN="your_mpin"
   GEMINI_API_KEY="your_gemini_key"
   MARKETAUX_API_KEY="your_marketaux_key"
   ALPHA_VANTAGE_API_KEY="your_alphavantage_key"
   ```

4. **Run database migrations**
   ```bash
   python -m app.db_migrations
   ```
   This creates:
   - `data/dashboard.db` - Main SQLite database
   - `candidates` table - For scraped stock candidates
   - Enhanced `watchlist` table with ATH analysis columns

5. **Verify setup**
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('data/dashboard.db'); print('✓ Database connected')"
   ```

---

## Daily Usage

### Starting the API Server

```bash
# From simple-trader-api directory
python -m app.main
```

The API will start at `http://localhost:8000`

### Common Workflow

#### 1. Scrape Candidates from Chartink

**Endpoint:** `POST /scanner/scrape-chartink`

Scrapes from two screeners:
- Within 2% of 52-week highs
- Stage 2 trend template

**Example using curl:**
```bash
curl -X POST http://localhost:8000/scanner/scrape-chartink \
  -H "X-Session-ID: your_session_id"
```

**Response:**
```json
{
  "success": true,
  "total_found": 42,
  "unique_stocks": 35,
  "overlap_removed": 7,
  "new_candidates": 28,
  "duplicates_skipped": 7,
  "errors": []
}
```

#### 2. View Candidates

**Endpoint:** `GET /scanner/candidates`

Retrieves all candidate stocks with their analysis data.

```bash
curl http://localhost:8000/scanner/candidates \
  -H "X-Session-ID: your_session_id"
```

#### 3. Analyze Candidates

**Endpoint:** `POST /scanner/analyze-candidates`

Runs ATH analysis on all candidates to determine phases.

```bash
curl -X POST http://localhost:8000/scanner/analyze-candidates \
  -H "X-Session-ID: your_session_id"
```

**Response shows phase distribution:**
```json
{
  "success": true,
  "analyzed": 35,
  "phase_1": 8,
  "phase_2": 15,
  "phase_3": 12,
  "errors": []
}
```

#### 4. Add to Watchlist

**Option A: Single stock**

**Endpoint:** `POST /scanner/candidates/{symbol}/add-to-watchlist`

```bash
curl -X POST http://localhost:8000/scanner/candidates/RELIANCE/add-to-watchlist \
  -H "X-Session-ID: your_session_id"
```

**Option B: Bulk add**

**Endpoint:** `POST /scanner/candidates/bulk-add-to-watchlist`

```bash
curl -X POST http://localhost:8000/scanner/candidates/bulk-add-to-watchlist \
  -H "X-Session-ID: your_session_id" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE", "TCS", "INFY"]}'
```

#### 5. Monitor Watchlist

**Endpoint:** `GET /watchlist`

```bash
curl http://localhost:8000/watchlist \
  -H "X-Session-ID: your_session_id"
```

**Returns watchlist items with ATH data:**
```json
[
  {
    "id": 1,
    "symbol": "RELIANCE",
    "name": "Reliance Industries",
    "type": "EQUITY",
    "phase": 2,
    "status_label": "Above EMA200",
    "ath_value": 3245.50,
    "ath_date": "2024-10-15",
    "ema_200": 3100.25,
    "distance_from_ath": 3.5,
    "last_analyzed": "2026-04-14T10:30:00"
  }
]
```

#### 6. Update Watchlist Analysis

**Endpoint:** `POST /scanner/analyze-watchlist`

Refreshes ATH analysis for all watchlist stocks.

```bash
curl -X POST http://localhost:8000/scanner/analyze-watchlist \
  -H "X-Session-ID: your_session_id"
```

### Database Schema

#### Watchlist Table
```sql
CREATE TABLE watchlist (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL UNIQUE,
  name TEXT,
  type TEXT,                    -- EQUITY, DERIVATIVE
  added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  notes TEXT,
  -- ATH Analysis columns (added via migration)
  phase INTEGER,                -- 1, 2, or 3
  status_label TEXT,            -- Human-readable status
  ath_value REAL,              -- All-time high price
  ath_date TEXT,               -- Date of ATH
  ema_200 REAL,                -- 200-day EMA
  distance_from_ath REAL,      -- % distance from ATH
  last_analyzed TIMESTAMP
);
```

#### Candidates Table
```sql
CREATE TABLE candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  source TEXT NOT NULL,        -- 'ath_near_high', 'stage_2_trend', etc.
  current_price REAL,
  week_52_high REAL,
  distance_from_high REAL,
  scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(symbol, source)       -- Prevents exact duplicates
);
```

---

## Configuration

### Environment Variables

Place in `.env` file:

```
# Broker API credentials
NUBRA_CLIENT_ID=your_nubra_id
NUBRA_MPIN=your_nubra_pin

# AI services
GEMINI_API_KEY=your_gemini_key

# Market data services
MARKETAUX_API_KEY=your_marketaux_key
ALPHA_VANTAGE_API_KEY=your_alphavantage_key
```

### Data Paths

The pipeline expects historical data at:
```
../SimpleTraderExternal/data/daily/eod2/{SYMBOL}.csv
```

Each CSV file should contain:
- Date (YYYY-MM-DD format)
- Open, High, Low, Close (numeric)
- Volume (numeric)

Example:
```csv
Date,Open,High,Low,Close,Volume
2026-04-10,2500.00,2510.00,2495.00,2505.00,1000000
2026-04-11,2505.00,2520.00,2500.00,2515.00,1200000
```

### ChromeDriver Setup (for Chartink Scraping)

The scraper requires ChromeDriver:

```bash
# Automatic installation via webdriver-manager (recommended)
# Already in requirements.txt

# Or manual installation
# Download from: https://chromedriver.chromium.org/
# Place in PATH or specify path in code
```

---

## Monitoring

### Checking Logs

Logs are written to the console by default. For production:

```bash
# Redirect to file
python -m app.main > api.log 2>&1 &

# Monitor logs in real-time
tail -f api.log
```

### Database Statistics

Check database health:

```bash
# Connect to database
sqlite3 data/dashboard.db

# View table sizes
SELECT name, COUNT(*) as count FROM watchlist;
SELECT name, COUNT(*) as count FROM candidates;

# Check for orphaned records
SELECT symbol, COUNT(*) FROM candidates GROUP BY symbol HAVING COUNT(*) > 1;

# View analysis coverage
SELECT COUNT(*) as analyzed FROM watchlist WHERE phase IS NOT NULL;
SELECT COUNT(*) as analyzed FROM candidates WHERE phase IS NOT NULL;

# Recent activity
SELECT * FROM watchlist ORDER BY last_analyzed DESC LIMIT 10;
```

### Performance Monitoring

**Endpoint:** `GET /api/health`

Quick health check:
```bash
curl http://localhost:8000/api/health
# Response: {"status": "ok"}
```

### Key Metrics to Monitor

1. **Scraping Success Rate**
   - Monitor `total_found` vs `unique_stocks` in scrape responses
   - Target: >95% unique rate (low duplicates)

2. **Analysis Coverage**
   - Percentage of watchlist with phase data
   - Target: 100% analyzed within 1 hour

3. **Database Size**
   - Candidates table: Should grow with scrapes
   - Watchlist table: Expected to stabilize after initial setup

4. **Error Rates**
   - Check logs for failed analyses
   - Common: Missing data files, network issues

---

## Troubleshooting

### Issue: Database Connection Failed

**Symptom:** `sqlite3.OperationalError: unable to open database file`

**Solutions:**
1. Ensure `data/` directory exists:
   ```bash
   mkdir -p data
   ```

2. Check file permissions:
   ```bash
   ls -la data/dashboard.db
   chmod 644 data/dashboard.db
   ```

3. Verify migrations ran:
   ```bash
   python -m app.db_migrations
   ```

### Issue: ChromeDriver Not Found

**Symptom:** `chromium not found` or `chromedriver not found`

**Solutions:**
1. Reinstall webdriver-manager:
   ```bash
   pip install --upgrade webdriver-manager
   ```

2. Verify Chrome installation:
   ```bash
   which google-chrome   # Linux
   where Google\ Chrome  # macOS
   where chrome.exe      # Windows
   ```

3. Clear driver cache:
   ```bash
   rm -rf ~/.wdm/  # Linux/macOS
   rmdir %APPDATA%\.wdm  # Windows
   ```

### Issue: No Data Found for Symbol

**Symptom:** ATH analysis returns None, phase is NULL

**Causes:**
- Symbol not in historical data directory
- CSV file corrupted or missing columns
- Data path misconfigured

**Solutions:**
1. Verify symbol exists:
   ```bash
   ls ../SimpleTraderExternal/data/daily/eod2/ | grep SYMBOL
   ```

2. Check CSV format:
   ```bash
   head ../SimpleTraderExternal/data/daily/eod2/RELIANCE.csv
   ```

3. Update data path if needed:
   - Modify `ATHAnalyzer` in `app/services/ath_analyzer.py`
   - Or modify `DAILY_DATA_PATH` in `app/routers/watchlist.py`

### Issue: Duplicate Symbols in Candidates

**Symptom:** Same symbol appears multiple times from different sources

**Expected Behavior:** This is normal - symbols can come from multiple screeners

**To Prevent Mixing:**
- View with `GET /scanner/candidates` before analysis
- Filter by source in frontend

**To Clean Up:**
```sql
-- Remove all duplicate sources for a symbol (keep first)
DELETE FROM candidates WHERE symbol = 'RELIANCE' AND source != 'ath_near_high';
```

### Issue: High Memory Usage During Large Analysis

**Symptom:** Analysis slows down significantly with 100+ stocks

**Cause:** Loading all symbol CSVs simultaneously

**Solutions:**
1. Increase batch processing time
2. Restart API server periodically
3. Archive old candidates table rows

### Issue: Stale Phase Data

**Symptom:** `last_analyzed` is old, phase data doesn't match current market

**Solutions:**
1. Run analysis again:
   ```bash
   curl -X POST http://localhost:8000/scanner/analyze-watchlist \
     -H "X-Session-ID: session_id"
   ```

2. Set up automated analysis (via cron):
   ```bash
   # Every hour
   0 * * * * curl -X POST http://localhost:8000/scanner/analyze-watchlist \
     -H "X-Session-ID: session_id"
   ```

3. Clear and rebuild:
   ```sql
   UPDATE watchlist SET phase = NULL, last_analyzed = NULL;
   ```

### Issue: Session Authentication Errors

**Symptom:** `Not authenticated` response from endpoints

**Cause:** Missing or invalid X-Session-ID header

**Solution:**
1. Obtain session ID from login endpoint:
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "user", "password": "pass"}'
   ```

2. Use session ID in all requests:
   ```bash
   curl http://localhost:8000/watchlist \
     -H "X-Session-ID: returned_session_id"
   ```

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                          │
│                  (simple-trader-web)                        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                         │
│               (simple-trader-api/app/main.py)               │
├─────────────────────────────────────────────────────────────┤
│  Routers:                                                   │
│  ├─ auth.py          - Authentication (sessions)           │
│  ├─ watchlist.py     - Watchlist CRUD                      │
│  ├─ scanner.py       - Scraping & analysis                 │
│  ├─ signals.py       - Trading signals                     │
│  ├─ news.py          - Market news                         │
│  ├─ holdings.py      - Portfolio holdings                  │
│  ├─ orders.py        - Order history                       │
│  ├─ backtest.py      - Strategy backtesting               │
│  └─ ai.py            - AI chat & analysis                  │
└────────────┬──────────┬──────────┬──────────────────────────┘
             │          │          │
             ▼          ▼          ▼
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │ Services     │  │ Database     │  │ External     │
   ├──────────────┤  ├──────────────┤  ├──────────────┤
   │ ath_analyzer │  │ dashboard.db │  │ Chartink     │
   │ news_client  │  │              │  │ (Scraper)    │
   │ ai_client    │  │ Tables:      │  │              │
   │ chartink_    │  │ - watchlist  │  │ Broker APIs  │
   │  scraper     │  │ - candidates │  │ (Nubra)      │
   └──────────────┘  └──────────────┘  └──────────────┘
```

### Data Flow

#### Workflow 1: Add from Candidates
```
1. User clicks "Scrape Chartink"
   └─> Scraper hits Chartink URLs (2 screeners)
       └─> Returns list of stocks (may have overlaps)
           └─> Deduplicates results
               └─> Stores in candidates table
                   └─> Returns counts to user

2. User reviews candidates
   └─> Candidates displayed with scraped metadata

3. User clicks "Analyze Candidates"
   └─> ATHAnalyzer loads each symbol's CSV
       └─> Calculates EMA 200, finds ATH
           └─> Determines phase (1/2/3)
               └─> Updates candidates table with phase
                   └─> Returns phase distribution

4. User selects candidates to add
   └─> Bulk add endpoint called
       └─> For each symbol:
           ├─> Copies phase data from candidates
           ├─> Inserts into watchlist
           └─> Deletes from candidates
               └─> Returns counts
```

#### Workflow 2: Direct Watchlist Management
```
1. User adds symbol to watchlist via UI
   └─> Validates symbol against historical data files
       └─> Inserts into watchlist table
           └─> Returns success/error

2. User clicks "Analyze Watchlist"
   └─> Retrieves all symbols from watchlist
       └─> For each symbol:
           ├─> ATHAnalyzer loads CSV data
           ├─> Calculates phase and metrics
           └─> Updates watchlist row
               └─> Returns phase distribution

3. Watchlist displays with analysis data
   └─> Shows phase, ATH, EMA200, distance metrics
```

### Component Details

#### 1. Authentication (`app/auth.py`)
- Session-based authentication
- Validates X-Session-ID header
- In-memory session storage (default)

#### 2. Database Layer (`app/db_migrations.py`)
- Creates/migrates database schema
- Ensures required columns exist
- Safe for re-running

#### 3. ATH Analyzer (`app/services/ath_analyzer.py`)
**Key Methods:**
- `analyze_symbol(symbol)` - Analyzes single stock
- `analyze_multiple(symbols)` - Batch analysis
- `_load_data(symbol)` - Loads CSV
- `_calculate_ema(df, period)` - Computes EMA 200
- `_find_ath(df)` - Finds all-time high

**Output:**
```python
{
    'phase': 1,                    # Phase classification
    'status_label': 'Below EMA200',
    'ath_value': 3245.50,
    'ath_date': '2024-10-15',
    'ema_200': 3100.25,
    'distance_from_ath': 3.5,     # Percentage
    'last_analyzed': '2026-04-14T10:30:00'
}
```

#### 4. Chartink Scraper (`app/services/chartink_scraper.py`)
- Selenium-based web scraping
- Handles JavaScript rendering
- Supports pagination (if needed)
- Returns deduplicated results

**Output:**
```python
{
    'stocks': [
        {'symbol': 'RELIANCE', 'source': 'ath_near_high'},
        {'symbol': 'TCS', 'source': 'stage_2_trend'}
    ],
    'total_scraped': 42,
    'unique_count': 35,
    'errors': []
}
```

#### 5. Router Endpoints (`app/routers/scanner.py` & `app/routers/watchlist.py`)

**Scanner Endpoints:**
- `POST /scanner/scrape-chartink` - Trigger scraping
- `GET /scanner/candidates` - View candidates
- `POST /scanner/analyze-candidates` - Analyze candidates
- `POST /scanner/analyze-watchlist` - Analyze watchlist
- `POST /scanner/candidates/{symbol}/add-to-watchlist` - Single add
- `POST /scanner/candidates/bulk-add-to-watchlist` - Bulk add

**Watchlist Endpoints:**
- `GET /watchlist` - Get all watchlist items
- `POST /watchlist` - Add stock to watchlist
- `DELETE /watchlist/{symbol}` - Remove from watchlist
- `GET /watchlist/symbols` - Get valid symbols for autocomplete

### Error Handling

**At Each Layer:**

1. **API Layer**
   - Validates input
   - Catches authentication errors
   - Returns structured error responses

2. **Service Layer**
   - Handles missing data files
   - Manages calculation errors
   - Logs exceptions with context

3. **Database Layer**
   - Transaction safety (rollback on error)
   - Duplicate key handling
   - Connection management

4. **Scraper Layer**
   - Retry on network errors
   - Element detection failures
   - Timeout management

---

## Advanced Topics

### Performance Optimization

#### Database Indexing
For faster candidate filtering, add indexes:
```sql
CREATE INDEX idx_candidates_symbol ON candidates(symbol);
CREATE INDEX idx_candidates_phase ON candidates(phase);
CREATE INDEX idx_watchlist_symbol ON watchlist(symbol);
CREATE INDEX idx_watchlist_phase ON watchlist(phase);
```

#### Batch Analysis
For analyzing 100+ stocks efficiently:
```python
# In code
analyzer = ATHAnalyzer()
symbols = ['SYMBOL1', 'SYMBOL2', ...]  # Up to 100+
results = analyzer.analyze_multiple(symbols)  # Parallelized internally
```

### Extending the System

#### Adding New Screeners
Modify `ChartinkScraper.scrape_both_screeners()`:
```python
def scrape_custom_screener(self):
    # Add new screener URL
    url = "https://chartin.com/custom-screener"
    # Use existing Selenium logic
    # Return with 'custom_screener' as source
```

#### Custom Phase Classification
Modify `ATHAnalyzer.analyze_symbol()`:
```python
def _determine_phase(self, close, ema200, ath_value):
    # Implement custom logic
    # Return phase (1, 2, 3, or custom)
```

### Backup and Recovery

#### Database Backup
```bash
# Backup
cp data/dashboard.db data/dashboard.db.backup

# Restore
cp data/dashboard.db.backup data/dashboard.db
```

#### Rebuild Database
```bash
# Remove existing
rm data/dashboard.db

# Rebuild from scratch
python -m app.db_migrations

# Restore from backup
sqlite3 data/dashboard.db < backup.sql
```

---

## Appendix: Quick Reference

### Common Commands

```bash
# Start API
python -m app.main

# Run migrations
python -m app.db_migrations

# Check database
sqlite3 data/dashboard.db "SELECT COUNT(*) FROM watchlist;"

# Monitor logs
tail -f api.log

# Test health
curl http://localhost:8000/api/health

# List candidates
curl -H "X-Session-ID: id" http://localhost:8000/scanner/candidates

# Analyze watchlist
curl -X POST -H "X-Session-ID: id" http://localhost:8000/scanner/analyze-watchlist
```

### File Locations

```
simple-trader-api/
├── app/
│   ├── main.py                 # API entry point
│   ├── auth.py                 # Session management
│   ├── config.py               # Configuration
│   ├── db_migrations.py        # Database setup
│   ├── routers/
│   │   ├── scanner.py          # Scraping & analysis endpoints
│   │   ├── watchlist.py        # Watchlist endpoints
│   │   ├── signals.py
│   │   ├── news.py
│   │   ├── holdings.py
│   │   ├── orders.py
│   │   ├── backtest.py
│   │   └── ai.py
│   └── services/
│       ├── ath_analyzer.py     # ATH analysis logic
│       ├── chartink_scraper.py # Web scraper
│       ├── ai_client.py        # Gemini AI
│       └── news_client.py      # Market news
├── data/
│   └── dashboard.db            # SQLite database
├── requirements.txt            # Python dependencies
└── README_DATA_PIPELINE.md     # This file
```

### Glossary

- **ATH**: All-Time High - highest price a stock has ever reached
- **EMA 200**: Exponential Moving Average over 200 days
- **Phase 1**: Stock below EMA 200 (Accumulation)
- **Phase 2**: Stock above EMA 200, still 5-10% below ATH (Momentum)
- **Phase 3**: Stock near ATH, breakout potential
- **Candidate**: Stock identified by screener, waiting for review
- **Watchlist**: Selected stocks for active monitoring

---

## Support and Contributions

For issues, feature requests, or improvements:

1. Check this README for common solutions
2. Review logs for error details
3. Verify database integrity with provided SQL commands
4. Consult the project documentation in `../SimpleTraderExternal/docs/`

---

**Last Updated**: April 14, 2026
**Version**: 1.0.0
**Author**: SimpleTrader Development Team
