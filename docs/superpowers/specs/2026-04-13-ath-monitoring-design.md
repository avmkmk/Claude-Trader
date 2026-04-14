---
name: ATH Monitoring System Design
description: Manual on-demand Chartink scraping and ATH reclaim phase analysis for watchlist stocks
type: design
date: 2026-04-13
---

# ATH Monitoring System Design

## Overview

Build a manual on-demand system to:
1. Scrape stocks from Chartink screeners (Stage 2 Trend + Within 2% of 52W high)
2. Review and selectively add candidates to watchlist
3. **Auto-analyze newly added stocks** to determine ATH reclaim fitness
4. Display status labels: "Phase 3 (Entry)", "Approaching Phase 3", "Consolidation", "Not Applicable"
5. Surface entry-ready stocks (Phase 3) via dashboard alerts

**Approach:** Manual triggers (no scheduled jobs) for maximum flexibility and incremental development.

---

## Requirements

### Functional
- Scrape 2 Chartink screener URLs on-demand
- Handle pagination (results may span multiple pages)
- Store scraped stocks in candidates table
- Allow user to review and approve candidates before adding to watchlist
- **Auto-analyze stocks immediately when added to watchlist**
- Determine if stock fits ATH reclaim pattern with detailed status labels
- Display status badges: "Phase 3 (Entry)", "Approaching Phase 3", "Consolidation", "Not Applicable"
- Highlight Phase 3 stocks as entry signals
- Allow manual re-analysis of all watchlist stocks on-demand

### Non-Functional
- No scheduled jobs (100% manual triggers)
- Use Selenium for Chartink scraping (handles JavaScript rendering)
- Scraping takes 15-30 seconds (acceptable for manual workflow)
- Works with existing FastAPI + SQLite + React architecture
- Reuses existing authentication and data patterns

---

## Architecture

```
React UI
├── Candidates Page (new)
│   ├── "Scan Chartink" button → POST /scanner/scrape-chartink
│   ├── Table of candidates with "Add to Watchlist" buttons
│   └── Source badges (which screener found each stock)
└── Enhanced Watchlist Page
    ├── "Run ATH Analysis" button → POST /scanner/analyze-watchlist
    ├── Phase badge column (Phase 1/2/3)
    └── Alert count for Phase 3 stocks

FastAPI Backend
├── ChartinkScraper (services/chartink_scraper.py)
│   ├── Selenium headless Chrome
│   ├── Scrapes both screener URLs
│   ├── Handles pagination
│   └── Returns list of symbols
├── ATHAnalyzer (services/ath_analyzer.py)
│   ├── Loads historical data from SimpleTraderExternal
│   ├── Calculates EMA 200
│   ├── Detects ATH and current phase
│   └── Returns phase + ATH metrics
└── Scanner Router (routers/scanner.py)
    ├── POST /scanner/scrape-chartink
    ├── POST /scanner/analyze-watchlist
    ├── GET /scanner/candidates
    └── POST /scanner/candidates/{symbol}/add-to-watchlist

Database (SQLite - dashboard.db)
├── candidates table (new)
│   ├── id, symbol, source, scraped_at
│   └── Temporary storage for review
└── watchlist table (enhanced)
    ├── Existing: id, symbol, name, type, added_at
    └── New: phase, ath_value, ath_date, ema_200, last_analyzed
```

---

## Database Schema

### New Table: `candidates`

```sql
CREATE TABLE candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    source TEXT NOT NULL,              -- 'within-2-52week' or 'stage-2-trend'
    current_price REAL,
    week_52_high REAL,
    distance_from_high REAL,           -- percentage
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, source)             -- prevent duplicates from same source
);
```

**Why:** Temporary staging area for scraped stocks before user approval.

### Enhanced Table: `watchlist`

```sql
ALTER TABLE watchlist ADD COLUMN phase INTEGER DEFAULT NULL;      -- 1, 2, or 3
ALTER TABLE watchlist ADD COLUMN status_label TEXT DEFAULT NULL;  -- Human-readable status
ALTER TABLE watchlist ADD COLUMN ath_value REAL DEFAULT NULL;
ALTER TABLE watchlist ADD COLUMN ath_date TEXT DEFAULT NULL;
ALTER TABLE watchlist ADD COLUMN ema_200 REAL DEFAULT NULL;
ALTER TABLE watchlist ADD COLUMN distance_from_ath REAL DEFAULT NULL;  -- Percentage
ALTER TABLE watchlist ADD COLUMN last_analyzed TIMESTAMP DEFAULT NULL;
```

**Status Labels:**
- `"Phase 3 (Entry Signal)"` - Close > ATH (ready to trade)
- `"Approaching Phase 3"` - Close within 2% of ATH, above EMA 200
- `"Phase 2 (Consolidation)"` - Close < EMA 200 (building setup)
- `"Phase 1 (Tracking)"` - Making new ATHs, no consolidation yet
- `"Not Applicable"` - Doesn't fit ATH reclaim pattern (e.g., never made ATH in history)

**Why:** Enrich watchlist with detailed ATH strategy state for dashboard display and filtering.

---

## Component Details

### 1. Chartink Scraper

**File:** `simple-trader-api/app/services/chartink_scraper.py`

**Technology:** Selenium with headless Chrome

**Why Selenium:**
- Chartink loads data via JavaScript (not in initial HTML)
- BeautifulSoup won't work
- No documented API endpoints

**Scraper URLs:**
1. `https://chartink.com/screener/within-2-of-52-week-highs-chartitude`
2. `https://chartink.com/screener/stage-2-trend-template`

**Implementation:**

```python
class ChartinkScraper:
    def scrape_screener(self, url: str, source_name: str) -> List[Dict]:
        """
        Scrape a Chartink screener with pagination support.

        Returns: List of {symbol, source} dicts
        """
        # 1. Launch headless Chrome
        # 2. Navigate to URL
        # 3. Wait for table (ID: DataTables_Table_0)
        # 4. Loop through pages:
        #    - Parse rows
        #    - Click "Next" button
        #    - Check if "disabled" class (last page)
        # 5. Return all symbols

    def scrape_both_screeners(self) -> List[Dict]:
        """Scrape both URLs with 3-second delay between requests"""
        # For politeness and rate limiting
```

**Pagination Logic:**
- DataTables pagination: `#DataTables_Table_0_next` button
- Check for `disabled` class to detect last page
- 2-second wait between page clicks
- Max 10 pages safety limit

**Dependencies:**
```
selenium==4.17.2
webdriver-manager==4.0.1
```

---

### 2. ATH Analyzer

**File:** `simple-trader-api/app/services/ath_analyzer.py`

**Data Source:** `SimpleTraderExternal/data/daily/eod2/{SYMBOL}.csv`

**Phase Logic with Status Labels:**

| Phase | Condition | Status Label | Badge Color | Meaning |
|-------|-----------|--------------|-------------|---------|
| 3 | Close > ATH | "Phase 3 (Entry Signal)" | 🟢 Green | Ready to trade! |
| 2.5 | Close > EMA 200 AND within 2% of ATH | "Approaching Phase 3" | 🟡 Yellow | Watch closely, near entry |
| 2 | Close < EMA 200 | "Phase 2 (Consolidation)" | 🟠 Orange | Building setup |
| 1 | Default | "Phase 1 (Tracking)" | ⚪ Gray | Making ATHs, no setup |
| 0 | No clear pattern | "Not Applicable" | ⚫ Dark Gray | Doesn't fit strategy |

**Implementation:**

```python
class ATHAnalyzer:
    def analyze_symbol(self, symbol: str) -> Dict:
        """
        Analyze single stock for ATH reclaim phase.

        Returns:
            {
                'symbol': str,
                'phase': int (1, 2, or 3),
                'ath_value': float,
                'ath_date': str,
                'current_price': float,
                'ema_200': float,
                'distance_from_ath': float (percentage)
            }
        """
        # 1. Load CSV
        # 2. Calculate EMA 200
        # 3. Find all-time high
        # 4. Determine phase
        # 5. Return metrics

    def _determine_phase_and_status(self, df, current_price, ema_200, ath_value) -> tuple:
        """
        Determine phase (numeric) and status label (human-readable).

        Returns: (phase: int, status_label: str)
        """
        # Phase 3: Entry signal
        if current_price > ath_value:
            return (3, "Phase 3 (Entry Signal)")

        # Approaching Phase 3: Within 2% of ATH and above EMA 200
        distance_pct = ((current_price - ath_value) / ath_value) * 100
        if distance_pct > -2.0 and current_price > ema_200:
            return (2, "Approaching Phase 3")

        # Phase 2: Consolidation
        if current_price < ema_200:
            return (2, "Phase 2 (Consolidation)")

        # Phase 1: Default tracking
        return (1, "Phase 1 (Tracking)")
```

**Why local data:**
User confirmed local historical data should NOT be used for screening (not updated daily), but CAN be used for phase analysis since we only need EMA 200 and ATH tracking (not time-sensitive).

---

### 3. API Endpoints

**File:** `simple-trader-api/app/routers/scanner.py`

#### POST /scanner/scrape-chartink

**Purpose:** Trigger Chartink scraping

**Response:**
```json
{
  "success": true,
  "total_found": 45,
  "new_candidates": 12,
  "duplicates_skipped": 33
}
```

**Process:**
1. Launch ChartinkScraper
2. Scrape both URLs
3. Insert into `candidates` table (skip duplicates)
4. Return counts

---

#### POST /scanner/analyze-watchlist

**Purpose:** Run ATH analysis on all watchlist stocks

**Response:**
```json
{
  "success": true,
  "analyzed": 25,
  "phase_1": 10,
  "phase_2": 12,
  "phase_3": 3
}
```

**Process:**
1. Load all watchlist symbols
2. Run ATHAnalyzer on each
3. Update watchlist table with phase data
4. Return phase distribution

---

#### GET /scanner/candidates

**Purpose:** View all candidate stocks

**Response:**
```json
[
  {
    "id": 1,
    "symbol": "RELIANCE",
    "source": "stage-2-trend",
    "scraped_at": "2026-04-13T16:30:00"
  }
]
```

---

#### POST /scanner/candidates/{symbol}/add-to-watchlist

**Purpose:** Move candidate to watchlist and auto-analyze

**Response:**
```json
{
  "success": true,
  "analysis": {
    "symbol": "RELIANCE",
    "phase": 2,
    "status_label": "Approaching Phase 3",
    "distance_from_ath": -1.5
  }
}
```

**Process:**
1. INSERT into watchlist
2. DELETE from candidates
3. **Run ATH analysis immediately** on the newly added stock
4. UPDATE watchlist with phase, status, ATH metrics
5. Return analysis result to show in UI toast
6. Invalidate caches

---

### 4. React UI Components

#### New Page: Candidates

**File:** `simple-trader-web/src/pages/Candidates.tsx`

**Features:**
- "Scan Chartink" button (triggers scraping)
- Loading spinner during 15-30 second scrape
- Table of candidates with:
  - Symbol
  - Source badge (which screener found it)
  - Scraped date
  - "Add to Watchlist" button per row
- Success message showing scan results

**User flow:**
1. Click "Scan Chartink"
2. Wait 15-30 seconds (spinner shown)
3. Review list of candidates
4. Click "Add to Watchlist" for interesting stocks
5. **See instant analysis result** in toast: "RELIANCE added → Approaching Phase 3 (-1.5% from ATH)"
6. Candidates removed from list after adding

---

#### Enhanced: Watchlist Page

**File:** `simple-trader-web/src/pages/Watchlist.tsx`

**Additions:**
- "Run ATH Analysis" button at top (re-analyze all stocks)
- New column: Status badge (color-coded)
  - Phase 3 (Entry Signal): 🟢 Green badge
  - Approaching Phase 3: 🟡 Yellow badge
  - Phase 2 (Consolidation): 🟠 Orange badge
  - Phase 1 (Tracking): ⚪ Gray badge
  - Not Applicable: ⚫ Dark gray badge
- Display status distribution after analysis
- Sort by phase (Phase 3 stocks at top)

**User flow:**
1. Click "Run ATH Analysis"
2. Wait for analysis (usually <5 seconds)
3. See phase badges appear in table
4. Focus on Phase 3 stocks for entries

---

## Data Flow

**Complete workflow:**

```
1. USER: Clicks "Scan Chartink" in Candidates page
   ↓
2. API: POST /scanner/scrape-chartink
   ↓
3. SCRAPER: Selenium scrapes both Chartink URLs (15-30 seconds)
   ↓
4. DATABASE: Insert symbols into `candidates` table
   ↓
5. UI: Refresh candidates list, show "45 stocks found, 12 new"
   ↓
6. USER: Reviews candidates, clicks "Add to Watchlist" for interesting ones
   ↓
7. API: POST /scanner/candidates/{symbol}/add-to-watchlist
   ↓
8. DATABASE: INSERT into watchlist, DELETE from candidates
   ↓
9. UI: Refresh both tables
   ↓
10. USER: Clicks "Run ATH Analysis" in Watchlist page
    ↓
11. API: POST /scanner/analyze-watchlist
    ↓
12. ANALYZER: Load historical data, calculate EMA 200, detect phases
    ↓
13. DATABASE: UPDATE watchlist with phase, ATH value, EMA 200
    ↓
14. UI: Refresh watchlist with phase badges
    ↓
15. USER: Sees Phase 3 stocks (green badge) → entry signals!
```

**Daily routine:**
- Evening (4 PM): Scan Chartink → Review candidates → Add to watchlist
- Evening (4:30 PM): Run ATH analysis → Check Phase 3 stocks
- Morning (9 AM): Review Phase 3 stocks → Plan trades

---

## Error Handling

### Scraper Errors

| Error | Handling |
|-------|----------|
| Timeout (no table in 15s) | Return empty list, show error toast |
| Network failure | Catch exception, log, show user-friendly message |
| No results | Show "No candidates found today" |
| Pagination issues | Safety limit of 10 pages, log if hit |

### Analyzer Errors

| Error | Handling |
|-------|----------|
| Missing CSV file | Skip symbol, log warning, continue |
| Insufficient data (<200 days) | Skip symbol (can't calculate EMA 200) |
| Calculation errors | Catch pandas exceptions, continue with next symbol |

### Database Errors

| Error | Handling |
|-------|----------|
| Duplicate entries | Use UNIQUE constraints, INSERT OR IGNORE |
| Connection failures | Retry once, then show error |

### UI Feedback

- Spinners during long operations
- Success/error toast notifications
- Disable buttons during processing
- Inline error messages
- Show phase distribution after analysis

---

## Implementation Phases

**Phase 1: Chartink Scraper**
- Build Selenium scraper
- Create `candidates` table
- Build `/scrape-chartink` endpoint
- Build Candidates UI page

**Phase 2: Candidates Management**
- Build `/candidates` GET endpoint
- Build "Add to Watchlist" functionality
- Wire up UI buttons

**Phase 3: ATH Analyzer**
- Build ATHAnalyzer class
- Enhance `watchlist` table schema
- Build `/analyze-watchlist` endpoint

**Phase 4: Watchlist Enhancements**
- Add phase column to Watchlist UI
- Add "Run ATH Analysis" button
- Add phase badges with color coding
- Add Phase 3 alert count

---

## Testing Strategy

**Scraper Testing:**
- Manual test: Click "Scan Chartink" and verify results
- Check pagination: Ensure all pages scraped
- Check duplicates: Scan twice, verify no duplicates

**Analyzer Testing:**
- Test with known stocks (RELIANCE, TCS, INFY)
- Verify phase detection against manual calculation
- Test with insufficient data (<200 days)
- Test with missing CSV files

**Integration Testing:**
- Full workflow: Scan → Add → Analyze → View phases
- Verify database updates
- Check UI state updates

---

## Future Enhancements

**Not in scope for initial implementation:**

1. **Scheduled jobs** - Can add APScheduler later if desired
2. **Fundamental analysis** - Integrate P/E, debt ratios for prioritization
3. **Real-time monitoring** - Websocket for intraday tracking
4. **Stock ranking** - Auto-score based on volume, sector, RS
5. **Alert emails** - Send Phase 3 alerts via email
6. **Historical phase tracking** - Track when stocks enter/exit phases
7. **API reverse-engineering** - Find Chartink API for faster scraping

---

## Dependencies

**Python packages:**
```
selenium==4.17.2
webdriver-manager==4.0.1
pandas>=1.5.0
numpy>=1.24.0
```

**System requirements:**
- Chrome/Chromium browser
- ChromeDriver (auto-installed via webdriver-manager)

**Existing dependencies:**
- FastAPI
- SQLite3
- React + TanStack Query

---

## Success Criteria

**The system is successful when:**

1. ✅ User can scan Chartink with one button click
2. ✅ Scraper handles pagination and extracts all stocks
3. ✅ Candidates appear in review table
4. ✅ User can selectively add candidates to watchlist
5. ✅ ATH analysis correctly detects Phase 1/2/3
6. ✅ Phase badges display in watchlist UI
7. ✅ Phase 3 stocks are clearly highlighted
8. ✅ Complete workflow takes <5 minutes daily
9. ✅ System handles errors gracefully (no crashes)
10. ✅ All operations are manual (no background jobs)

---

## Why This Design

**Manual triggers over scheduled jobs:**
- User wants flexibility to run anytime
- Easier to test and debug incrementally
- No need to keep backend running 24/7
- Can add scheduling later without refactoring

**Selenium over API reverse-engineering:**
- Guaranteed to work (renders JavaScript)
- More maintainable (not dependent on undocumented API)
- Acceptable performance for manual workflow (15-30s)

**Local phase analysis:**
- Historical data sufficient for EMA 200 and ATH tracking
- Much faster than fetching live data for 50+ stocks
- Can refresh historical data separately

**Review-before-adding workflow:**
- User maintains control over watchlist quality
- Prevents auto-adding hundreds of stocks
- Allows manual filtering based on familiarity, sector, etc.

**SQLite over PostgreSQL:**
- Existing architecture uses SQLite
- Sufficient for personal use (not millions of users)
- Zero additional infrastructure

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Chartink changes page structure | Selenium locators may break → add error handling, alert user |
| Scraping takes too long (>60s) | Add timeout, show progress indicator |
| Historical data outdated | Warn user in UI, suggest updating data |
| Chrome not installed | Include setup instructions in docs |
| Too many candidates (>500 stocks) | Add filters, sorting, pagination to Candidates page |

---

## Open Questions

**Resolved:**
- ✅ Manual vs scheduled: **Manual**
- ✅ Real-time vs EOD monitoring: **EOD (manual trigger)**
- ✅ Auto-add vs review candidates: **Review first**
- ✅ Prioritization: **Manual selection**
- ✅ Notifications: **Dashboard alerts only**
- ✅ Scraping method: **Selenium**

**For future consideration:**
- Should we add a "Clear candidates" button to purge old scans?
- Should phase colors be customizable in settings?
- Should we track phase history (when stock entered Phase 2, etc.)?
