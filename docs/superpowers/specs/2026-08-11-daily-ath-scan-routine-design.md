---
name: Daily ATH Scan Routine Design
description: Claude-driven daily routine that combines Chartink screening, market-cap segregation, and live TradingView desktop chart confirmation into a single actionable Excel watchlist
type: design
date: 2026-08-11
---

# Daily ATH Scan Routine Design

## Overview

A repeatable morning routine, invoked as a Claude Code skill (e.g. `/daily-ath-scan`), that:

1. Scrapes two Chartink screeners and takes the **intersection** (stocks common to both)
2. Segregates the common stocks by market cap and pulls precise current price / all-time-high figures via `tradingview-cli`
3. Visually confirms each candidate's ATH-reclaim phase by driving the user's real **TradingView desktop app** (where the `ath-reclaim-pinecone.txt` Pine strategy is already applied to the default chart template) and reading the indicator's own visual output — no re-derivation of the strategy logic in Python
4. Filters to only stocks currently in the buy zone: already reclaimed but not yet extended, or approaching after a confirmed EMA200 dip
5. Produces a single dated Excel file as the day's actionable watchlist

This is a **live, Claude-driven** routine, not an unattended cron script — step 3 requires driving a native desktop app, which only makes sense inside an active Claude Code session.

## Relationship to the existing ATH Monitoring System

`docs/superpowers/specs/2026-04-13-ath-monitoring-design.md` already implemented a web-UI-based candidates → analyze → watchlist flow using `ChartinkScraper` and `ATHAnalyzer`. That design explicitly notes: *"User confirmed local historical data should NOT be used for screening (not updated daily)."*

This routine is consistent with that prior decision: it reuses `chartink_scraper.py` for scraping, but deliberately does **not** reuse `ATHAnalyzer`'s snapshot phase classifier (which relies on the same not-reliably-fresh local `eod2` CSVs) for the buy-zone decision. Instead, phase state is read directly off the live TradingView chart, which has accurate, current data by construction.

This routine is additive — it does not modify the existing candidates/watchlist web UI or database tables.

## Requirements

### Functional
- Scrape `within-2-of-52-week-highs-chartitude` and `stage-2-trend-template` Chartink screeners
- Keep only stocks appearing in **both** screeners (true intersection, not union)
- Classify each common stock by market cap tier: Large (≥20,000cr), Mid (5,000–20,000cr), Small (<5,000cr), Unknown (lookup failed)
- For each common stock, determine buy-zone status by reading the Pine strategy's visual state on the real TradingView desktop chart:
  - Blue background (Phase 2) and within 5% below the plotted Absolute ATH line → `"Approaching"`
  - A recent green `"RECLAIM #N"` label at/near the latest bar, with current close within 5% above the ATH line → `"Reclaimed"`
  - Anything else (fresh-high-only, deep consolidation, no historical EMA200 dip, or already >5% extended past ATH) → excluded
- Output one Excel file per run: single sheet, grouped by cap tier, sorted within tier by distance-from-ATH ascending
- No screenshots persisted after each is read

### Non-Functional
- No new database tables, no changes to the existing FastAPI app or web UI
- Deterministic parts (scrape, market cap lookup, Excel build) run as plain Python via Bash — testable independent of any live desktop session
- The desktop-chart-reading step adapts to whatever TradingView window/layout is actually on screen at runtime rather than hardcoding pixel coordinates
- Symbols that fail market cap lookup or fail to load in TradingView are logged and skipped, not fatal to the run

## Architecture

```
Step A (script): chartink_scraper.py
   scrape_screener(within-2-of-52-week-highs-chartitude)
   scrape_screener(stage-2-trend-template)
   → true intersection by symbol (fix: currently unions+dedups, needs
     changing to set intersection)

Step B (script): tradingview_cli.get_stock_info() per common symbol
   → market_cap_cr, cap_size (large/mid/small/unknown),
     current_price, all_time_high
   → writes simple-trader-api/data/daily_scans/YYYY-MM-DD_candidates.json

Step C (live, Claude drives the desktop via computer-use):
   for each candidate symbol:
     - switch the TradingView desktop chart to that symbol
     - wait for chart + Pine strategy overlay to render
     - screenshot
     - read: is background currently blue (Phase 2)? is there a
       "RECLAIM #N" label on/near the last bar? read price vs the
       plotted Absolute ATH / EMA200 lines
     - delete the screenshot immediately after reading it
     - record a verdict: Approaching / Reclaimed / Skip

Step D (script): merge Step B numeric data + Step C verdicts
   → apply the 5% buy-zone / approach band using the precise
     current_price / all_time_high numbers from Step B (not pixel
     measurements)
   → simple-trader-api/data/daily_scans/YYYY-MM-DD.xlsx
```

## Component Details

### Step A — Chartink intersection fix

**File:** `simple-trader-api/app/services/chartink_scraper.py`

`scrape_both_screeners()` currently unions and dedups results from both screener calls. Change it to compute the true set intersection on `symbol`, keeping a merged record (both sources' scraped fields) for each stock that appears in both lists. The two screener URLs already hardcoded in this file match the ones required here, so no URL changes are needed.

### Step B — Market cap & precise price enrichment

**New script:** `simple-trader-api/scripts/scan_candidates.py`

For each symbol from Step A, call `tradingview_cli.get_stock_info(symbol)` (existing service, already used by `scanner.py`). Reuses the existing thresholds (`LARGE_CAP_MIN = 20000`, `MID_CAP_MIN = 5000`). If the lookup fails, the stock is kept with `cap_size = "unknown"` rather than dropped, so nothing silently disappears before the visual check.

Output: `simple-trader-api/data/daily_scans/{today}_candidates.json`, a list of:
```json
{
  "symbol": "RELIANCE",
  "cap_size": "large",
  "market_cap_cr": 1881982.12,
  "current_price": 1323.9,
  "all_time_high": 1611.8
}
```

### Step C — Live TradingView desktop confirmation

Not a script — a documented procedure Claude follows live using the `computer-use` MCP tools, per candidate symbol:

1. Bring the TradingView desktop app forward, switch the active chart to the candidate symbol (the Pine strategy `ath-reclaim-pinecone.txt` is already applied to the chart template, per the user)
2. Wait for the chart and indicator overlay to finish rendering
3. Screenshot
4. Read the chart:
   - Blue-tinted background at the current (rightmost) bar → Phase 2 ("Approaching")
   - A green `"RECLAIM #N"` label at or within the last few bars → just reclaimed
   - No blue tint and no recent reclaim label → not currently actionable, skip
5. Delete the screenshot file immediately after reading it — no images persist past the read
6. Record the categorical verdict (`approaching` / `reclaimed` / `skip`) for Step D; do not try to read exact prices off the chart pixels — Step B already has precise numbers

Because this drives a real native window, the exact click/keyboard sequence (symbol search box vs. clicking through an existing watchlist panel) is discovered from the first screenshot each run rather than hardcoded — TradingView desktop layouts can shift between sessions (docked panels, layout changes, etc.).

### Step D — Merge, filter, and build Excel

**New script:** `simple-trader-api/scripts/build_excel.py`

Input: Step B's JSON + Step C's verdict list (symbol → approaching/reclaimed/skip).

Filter logic (using Step B's precise numbers, not the screenshot):
- `reclaimed` and `current_price` within `[all_time_high, all_time_high * 1.05]` → keep, `status = "Reclaimed"`
- `approaching` and `current_price` within `[all_time_high * 0.95, all_time_high)` → keep, `status = "Approaching"`
- otherwise → drop, even if Step C marked it reclaimed/approaching (guards against the visual read being right about the phase but the price having already moved outside the actionable band since the chart was last refreshed)

Excel output (`openpyxl`), single sheet `Watchlist`, one row per surviving symbol, columns:

| Symbol | Cap Tier | Market Cap (cr) | Status | Current Price | ATH | Distance from ATH % | TradingView Link |
|---|---|---|---|---|---|---|---|

Rows grouped by cap tier (Large → Mid → Small → Unknown) with a bold section-header row between tiers; sorted within each tier by `distance_from_ath_pct` ascending (closest to ideal entry first).

**File:** `simple-trader-api/data/daily_scans/YYYY-MM-DD.xlsx`

## Error Handling

| Failure | Handling |
|---|---|
| Chartink scrape fails/times out for one screener | Abort the run with a clear error — an intersection needs both sides; a partial scrape would silently under-report |
| `tradingview-cli` lookup fails for a symbol | Keep the symbol with `cap_size="unknown"`, `market_cap_cr=null`; still goes through Step C |
| TradingView desktop fails to load a symbol / chart doesn't render in time | Log and skip that symbol (excluded from output), continue to the next |
| Zero symbols survive the intersection | Report "no common candidates today" and stop before Step C |
| Zero symbols survive the Step D filter | Still write the Excel with a header-only sheet, so the day's run is recorded even with no actionable entries |

## Testing Strategy

- Step A: unit test the intersection logic with fixed fake screener outputs (overlapping and non-overlapping symbol sets)
- Step B: unit test cap-tier classification thresholds and the "unknown" fallback path, mocking `tradingview_cli`
- Step D: unit test the merge/filter/banding logic with fixed candidate + verdict fixtures, independent of any live run
- Step C: not unit-testable (live desktop interaction); validated by running the full routine end-to-end and manually spot-checking a few symbols' output against what's shown live in TradingView

## Success Criteria

1. Running `/daily-ath-scan` end to end produces one dated Excel file with only stocks that are genuinely in the buy zone per the live chart's own indicator state
2. No stock appears in the output that hasn't been visually confirmed against the actual Pine strategy overlay
3. No screenshot files remain on disk after a run completes
4. A single screener outage or a handful of failed symbol lookups doesn't crash the whole run
5. The output is directly usable for daily monitoring without further manual cross-referencing

## Open Questions / Future Enhancements

- Not in scope now: scheduling this to run automatically (it's inherently a live, Claude-driven session because of Step C)
- Not in scope now: feeding Step D's output back into the existing web app's `watchlist` table — this routine's output is a standalone Excel file only
- Future: if TradingView's data platform ever exposes a historical bar/EMA series via CLI or MCP, Step C could become a pure script and this routine could be fully unattended
