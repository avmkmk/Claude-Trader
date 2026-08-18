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

## Revision (2026-08-12): Entry-price-based distance for Reclaimed stocks

First live run of the routine surfaced a classification bug in how "Reclaimed" stocks were filtered/sorted, fixed as follows.

**The bug:** Step D was measuring a Reclaimed stock's "distance from entry" as `(current_price - current_absolute_ath) / current_absolute_ath`. This is wrong once a stock is actually held: `absoluteAth` in the Pine strategy keeps ratcheting up on every new high *even while a position is open* (the ATH-update block isn't gated on position state), so a stock can be deep in profit — far past its real entry — while still sitting right at the ATH line, making the old metric read as "0% away, right at entry" when the true entry was set weeks or months earlier at a much lower price.

Concrete example: `KRISHANA` entered on 2026-04-16 at ~128 (matching its EMA200 at the time, ~124). By 2026-08-12 close was 186.45 — the current ATH had also ratcheted up to 186.45, so the old metric showed `distance_pct = 0` ("right at entry"), when the real distance from the 128 entry was **+46%**. Same pattern hit most of that day's Reclaimed list (`WELCORP` +87%, `SANSERA` +117%, `CUPID` +896%, etc.) — of 34 stocks flagged Reclaimed, only 9 were genuinely still near their actual entry price.

**The fix:**
- For a **Reclaimed** (currently held) stock, "distance from entry" is `(current_price - entry_price) / entry_price`, where `entry_price` is the actual fill price: the close of the bar where the live Pine strategy's `RECLAIM #N` label fired (`process_orders_on_close = true`, so the entry fills at that bar's close — the label's own y-position, the bar's *low*, is only for label placement and is not the fill price). Recovered by matching the `RECLAIM #N` label's price against OHLCV bar lows to find the entry bar, then reading that bar's close.
- For an **Approaching** (not yet held) stock, distance-from-ATH is still the right measure — there is no entry price yet, so the current ATH *is* the trigger the stock needs to close above.
- Reclaimed stocks are only kept in the watchlist if `|distance_from_entry_pct| <= 5` (same ±5% band used elsewhere), sorted ascending by that distance so the ones closest to their actual entry lead the sheet.
- The Excel's per-row reference price column is therefore "Entry Price" for Reclaimed rows and "ATH (entry trigger)" for Approaching rows — these are two different reference prices and must not be conflated into a single "distance from ATH" column.

This does not change *whether* a stock counts as Reclaimed (that's still: last drawn label is `RECLAIM #N` with no `EXIT` since — see the EMA200-stop-based Reclaimed rule already governing that classification) — only how "close to actionable" is measured and filtered for stocks that already have an open position.

## Revision (2026-08-13): Persistent symbol state + diff-and-carry-forward scanning

Running full Step C (live TradingView desktop check) against the entire candidate union every day is expensive (~270-300 symbols, tens of minutes) and mostly redundant — day to day, ~90% of the Chartink candidate list is the same symbols repeating (2026-08-12 → 2026-08-13: 244 of 270 candidates were unchanged, only 26 genuinely new). Re-running Step C on all of them daily was pure waste for the ones that hadn't changed screener membership.

**The mechanism:**

- **Persistent state file**: `simple-trader-api/data/daily_scans/symbol_state.json` — a cumulative, never-auto-deleted record of every symbol ever checked, keyed by symbol, holding its last-known verdict, reason, distance, entry_date/entry_price, cap tier, and `last_checked` date. This is distinct from (and more durable than) `scan_step_c.mjs`'s own short-lived `_rejection_cache.json`, which only tracks recent skip verdicts for a 3-day cooldown and got wiped multiple times during active development of the classification logic — a real gap that caused rework.
- **Daily diff**: Step A+B still scrape fresh today (Chartink screener membership genuinely changes day to day), producing today's `{date}_candidates.json`. Before running Step C, diff today's candidate symbols against the *keys already present* in `symbol_state.json`. Only symbols **not already in the state file** get a live Step C check today.
- **Carry-forward**: every symbol already in `symbol_state.json` keeps its last-known verdict/data as-is for today's watchlist — no re-check, no expensive live read.
- **Merge**: today's fresh Step C results are written into `symbol_state.json` (overwriting/adding those symbols), then Step D builds the watchlist by reading the *entire* state file (not just today's candidates), applying the same Reclaimed/Approaching filters and entry-price-band logic described above.

**Known limitation, accepted for now:** carrying forward a Reclaimed/Approaching symbol's state unchanged means a same-day EMA200 stop-out or fresh reclaim on that specific symbol won't be caught until it's re-checked. The user explicitly chose this tradeoff (speed over same-day state-transition detection on already-tracked symbols) over the alternative of re-checking all Reclaimed/Approaching symbols daily in addition to new ones. If this tradeoff changes, the diff step should union "genuinely new candidates" with "symbols currently Reclaimed or Approaching in the state file" before deciding what to live-check.

**Bootstrapping note:** the first diff-based run (2026-08-13) had to seed `symbol_state.json` from the prior day's several partial/inconsistent debugging runs (mixed pre- and post-fix logic versions) rather than a single clean Step C pass — a one-time cost of the routine's classification logic having changed mid-session on its first live day. From this point forward the state file is self-sustaining: each day's diff only ever needs to seed itself from the previous day's already-consistent state.

**Update (2026-08-18):** the "known limitation" above — already-tracked Reclaimed/Approaching symbols never getting re-checked — is now fixed. See the revision below.

## Revision (2026-08-18): Re-check already-tracked Reclaimed/Approaching symbols

A live audit of the routine (walking one symbol, RUBYMILLS, end-to-end through Chart state, Pine labels, the Strategy Tester's own trade list, and Replay mode) confirmed two things converging on the same conclusion:

1. `build_final_watchlist.py` applies zero freshness checks — it reads whatever verdict/entry_price is sitting in `symbol_state.json` and trusts it completely, no matter how stale.
2. The Pine strategy itself is *designed* to re-trigger on the same symbol: on an EMA200 stop-out it re-arms straight to `phase := 2` (not back to `phase := 1`), so a symbol can legitimately produce `RECLAIM #2`, `#3`, etc. at a different price without a fresh peak first. A stop-out or a fresh re-reclaim on an already-tracked symbol was therefore silently invisible to the routine — exactly the risk the 2026-08-13 revision's "known limitation" section named but never implemented a fix for.

### The fix

**New script — `simple-trader-api/scripts/build_check_list.py`** (Step A2, runs immediately after `scan_candidates.py`):

- Loads `symbol_state.json` (existing tracked symbols) and today's `{today}_candidates.json` (fresh Chartink scrape + enrichment from Step A+B).
- `genuinely_new` = symbols in today's candidates not already present as a key in `symbol_state.json`.
- `already_tracked` = symbols in `symbol_state.json` whose stored `verdict` is `"reclaimed"` or `"approaching"`.
- Writes the deduplicated union of the two sets to `{today}_to_check.json`, in the same list-of-`{symbol, ...}` shape `scan_step_c.mjs` already expects.
- Prints a one-line summary (`new=N, re-checked=M, total=T`) so each run's live-check cost is visible before Step C runs.
- If `symbol_state.json` doesn't exist yet (first-ever run), treat it as an empty state — every candidate is `genuinely_new`.

**Bug fix — `simple-trader-api/scripts/update_symbol_state.py`:** its `cap_by_symbol` lookup currently sources `cap_size`/`market_cap_cr` only from today's `candidates.json`. Every re-checked-but-not-freshly-scraped symbol (the entire point of this revision) is absent from that file, so the existing lookup would silently reset the symbol's cap tier to `"unknown"` and `market_cap_cr` to `null` on every re-check. Fix: when a result's symbol isn't found in today's `candidates.json`, fall back to that symbol's existing `cap_size`/`market_cap_cr` already stored in `symbol_state.json`, rather than defaulting to unknown/null.

**No changes needed to `scan_step_c.mjs` or `build_final_watchlist.py`:**
- `scan_step_c.mjs` already correctly re-derives verdict/entry_price/entry_date from live Pine labels for whatever symbol list it's given — a re-checked `reclaimed` symbol that was stopped out comes back `skip` or `approaching`; one that re-triggered `RECLAIM #N+1` comes back `reclaimed` with a freshly recovered `entry_price`/`entry_date` from the new label.
- `build_final_watchlist.py` already reads the *entire* `symbol_state.json` on every run (not just today's touched symbols), so a symbol dropping to `verdict: "skip"` after re-check is automatically excluded from the watchlist with no code change.

### Packaging — `.claude/skills/daily-ath-scan/SKILL.md`

The full routine is packaged as a Claude Code skill documenting this run sequence. Steps 1, 2, 5, 6 run from `simple-trader-api/` (all outputs land in `simple-trader-api/data/daily_scans/`); step 4 runs from `tradingview-mcp-jackson/` and is passed absolute paths into that same `data/daily_scans/` directory so both halves read/write the same files:

1. (from `simple-trader-api/`) `python scripts/scan_candidates.py` → `data/daily_scans/{today}_candidates.json`
2. (from `simple-trader-api/`) `python scripts/build_check_list.py` → `data/daily_scans/{today}_to_check.json` + printed new/re-checked/total counts
3. Ensure TradingView Desktop is running with CDP debugging (`tradingview-mcp-jackson/scripts/launch_tv_debug.ps1` if not already up)
4. (from `tradingview-mcp-jackson/`) `node scan_step_c.mjs <absolute-path-to>/{today}_to_check.json <absolute-path-to>/{today}_verdicts.json`
5. (from `simple-trader-api/`) `python scripts/update_symbol_state.py data/daily_scans/{today}_verdicts_details.json data/daily_scans/{today}_candidates.json {today}` (with the cap-fallback fix)
6. (from `simple-trader-api/`) `python scripts/build_final_watchlist.py {today} data/daily_scans/{today}_final_watchlist.xlsx`
7. Report a run summary (new/re-checked/reclaimed/approaching counts) and send the Excel file

Every step here is now genuinely scriptable — Step C reads structured Pine data over CDP (`data.getStudyValues`, `data.getPineLabels`), not screenshots — so the skill is a checklist of tool/command invocations, not a visual-judgment procedure. The "live, Claude-driven session" framing from the original design (Step C needing computer-use) is superseded; the live desktop app still must be running for CDP to reach it, but no visual reading is involved anywhere in the sequence.

### Cost tradeoff

This restores most of the live-check volume the 2026-08-13 diff-and-carry-forward mechanism was built to cut. As of 2026-08-18, `symbol_state.json` holds 47 `reclaimed` + 9 `approaching` = 56 symbols that will now be re-checked on every run, on top of whatever's genuinely new that day (recently ~20-30). This is the direct, accepted cost of closing the staleness gap — the alternative is the silent stale-state risk this revision fixes.

### Testing

- `build_check_list.py`: unit test the union logic with fixed fixtures — candidates-only new symbols, state-only tracked symbols (reclaimed/approaching kept, skip excluded), symbols present in both (deduplicated, not double-checked), and an empty/missing `symbol_state.json` (first-run case).
- `update_symbol_state.py`: unit test the cap-tier fallback — symbol present in today's `candidates.json` (uses that), symbol absent from `candidates.json` but present in existing `symbol_state.json` (falls back to the stored cap_size/market_cap_cr), symbol absent from both (still defaults to `"unknown"`/`null`, unchanged prior behavior).
- End-to-end: not independently unit-testable (live TradingView desktop dependency, same as the existing Step C) — validated by running the full skill sequence and spot-checking that a previously-`reclaimed` symbol with a real EMA200 stop-out since its `last_checked` date correctly flips to `skip` or `approaching` in the rebuilt `symbol_state.json` and disappears from/moves within the new Excel.

### Explicitly out of scope for this revision

Three other gaps surfaced during the same audit are deliberately **not** addressed here (may become their own future revisions):
- Fragile bar-price-matched `entry_date`/`entry_price` recovery in `scan_step_c.mjs` for trades older than its 500-bar `getOhlcv` fetch window (confirmed wrong for RUBYMILLS's 2016 trade — matched a coincidental 2025 bar instead). The Strategy Tester's own trade list is the reliable ground truth for this, per the live RUBYMILLS audit, but switching to it is a separate change.
- The chart's Daily timeframe is never explicitly asserted before reading Pine values in `scan_step_c.mjs` — it silently trusts whatever resolution the chart template happens to be on.
- The ATH definition mismatch between Step B's `tradingview_cli.get_stock_info()` (an opaque TradingView scanner field) and the Pine script's own `absoluteAth` (a `max(open, close)` running max) — two different numbers used for different purposes today, never reconciled.

## Open Questions / Future Enhancements

- Not in scope now: scheduling this to run automatically without a human present (TradingView Desktop + CDP still needs to already be running; the skill sequence itself is fully scriptable as of the 2026-08-18 revision, so this is now more of a "keep TV Desktop alive" problem than a "Claude must watch the screen" problem)
- Not in scope now: feeding Step D's output back into the existing web app's `watchlist` table — this routine's output is a standalone Excel file only
- Future: the three gaps listed under "Explicitly out of scope" in the 2026-08-18 revision above
