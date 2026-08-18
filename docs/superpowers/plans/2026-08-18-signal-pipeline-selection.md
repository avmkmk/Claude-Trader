# Signal Pipeline: Cleanup + Selection & Ranking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete the scrapped web-UI/broker-execution surface, fix the TradingView Strategy Tester data-extraction bug, and build the Selection & Ranking stage so the daily watchlist is ordered by each symbol's actual historical performance under the live strategy.

**Architecture:** Two independent tracks. Track 1 (Task 1) deletes dead code — the React frontend and five FastAPI routers that only served it. Track 2 (Tasks 2-5) fixes a strategy-detection bug in the vendored `tradingview-mcp-jackson` MCP server, extracts the new ranking logic into a small pure/testable module, wires it into the existing `scan_step_c.mjs` live-scan script, and extends `build_final_watchlist.py` to rank and display the new data. Track 2's tasks are ordered by dependency (data.js fix -> pure ranking module -> wiring -> Excel output) but Task 1 has no dependency on the others and could run first or last.

**Tech Stack:** Python 3 (FastAPI backend, pytest), Node.js ESM (`tradingview-mcp-jackson`, `node --test`), openpyxl (Excel output).

**Spec:** `docs/superpowers/specs/2026-08-18-signal-pipeline-selection-design.md`

## Global Constraints

- Strategy name on the chart: `"ATH Reclaim - Final Verified"` (must match exactly for study/strategy lookups already used elsewhere in `scan_step_c.mjs`).
- Strategy detection field: `metaInfo().isTVScriptStrategy === true` (replaces the broken `is_price_study === false` check in three places in `tradingview-mcp-jackson/src/core/data.js`).
- Ranking eligibility floor: `total_trades >= 5` (symbols below this get `ranking_eligible: false` and null ranking fields, never dropped from output).
- Open-position detection in a strategy's `trades` array: the **last** trade element has an **empty string** `exit_signal` (`""`) — this is how a still-open position is distinguished from a closed one, which always has a real exit label (e.g. `"EMA Touch Exit"`).
- Ranking score: average of two independent rank positions (win_rate_pct descending, profit_factor descending) among eligible symbols within the same status group (Reclaimed / Approaching are ranked separately) — lower `combined_rank` is better.
- Nothing is ever silently dropped from the watchlist by ranking — ranking only changes sort order; rank-ineligible symbols still appear, sorted after eligible ones.
- Only delete `orders.py`, `holdings.py`, `auth.py`, `watchlist.py`, `signals.py`, `totp_helper.py`, and `simple-trader-web/`. Do not touch `ai.py`, `backtest.py`, `news.py`, `scanner.py`, `app/auth/` (still used by the kept routers), or `app/state.py` (still used by `main.py`).

---

### Task 1: Cleanup — delete scrapped web UI and dead routers

**Files:**
- Delete: `simple-trader-web/` (entire directory)
- Delete: `simple-trader-api/app/routers/auth.py`
- Delete: `simple-trader-api/app/routers/holdings.py`
- Delete: `simple-trader-api/app/routers/orders.py`
- Delete: `simple-trader-api/app/routers/watchlist.py`
- Delete: `simple-trader-api/app/routers/signals.py`
- Delete: `simple-trader-api/app/services/totp_helper.py` (orphaned once `auth.py` is gone — confirmed via `grep -rl totp_helper` that no other file imports it)
- Modify: `simple-trader-api/app/main.py`

**Interfaces:**
- Produces: a FastAPI app that still boots cleanly (`from app.main import app` succeeds) and still serves `ai.py`, `backtest.py`, `news.py`, `scanner.py` unchanged. Later tasks (3-5) do not depend on this task's completion.

- [ ] **Step 1: Confirm nothing else references the files about to be deleted**

Run (from `simple-trader-api/`):
```bash
grep -rln "totp_helper" --include="*.py" .
grep -rln "from app.routers import" --include="*.py" . | xargs grep -n "auth\|holdings\|orders\|watchlist\|signals"
```
Expected: only `app/main.py` references the five routers (via its single combined import line), and only `app/routers/auth.py` itself references `totp_helper`. If anything else turns up, stop and report it — do not delete blindly.

- [ ] **Step 2: Delete the frontend and the five dead routers + orphaned service**

```bash
rm -rf simple-trader-web
rm simple-trader-api/app/routers/auth.py
rm simple-trader-api/app/routers/holdings.py
rm simple-trader-api/app/routers/orders.py
rm simple-trader-api/app/routers/watchlist.py
rm simple-trader-api/app/routers/signals.py
rm simple-trader-api/app/services/totp_helper.py
```

- [ ] **Step 3: Update `app/main.py`**

Change the router import line from:
```python
from app.routers import auth, holdings, orders, watchlist, signals, news, backtest, ai, scanner
```
to:
```python
from app.routers import news, backtest, ai, scanner
```

Remove these five lines (keep the rest of the block unchanged):
```python
app.include_router(auth.router)      # Authentication (login/logout)
app.include_router(holdings.router)  # Portfolio holdings
app.include_router(orders.router)    # Order history
app.include_router(watchlist.router)  # Stock watchlist management
app.include_router(signals.router)    # Trading signals
```

Leave `state.set_nubra_handler(None)` and the `/api/nubra-status` endpoint in `startup_event`/`main.py` exactly as they are — `app/state.py` is unrelated to the deleted routers and still used here.

- [ ] **Step 4: Verify the app still imports and the existing suite still passes**

Run (from `simple-trader-api/`):
```bash
python -c "from app.main import app; print('OK')"
python -m pytest tests/ -v
```
Expected: `OK` printed, and all existing tests pass (no test currently references the deleted files, confirmed in Step 1's grep, so the count should be unchanged from before this task).

- [ ] **Step 5: Commit**

```bash
git add -A -- simple-trader-web simple-trader-api/app/routers/auth.py simple-trader-api/app/routers/holdings.py simple-trader-api/app/routers/orders.py simple-trader-api/app/routers/watchlist.py simple-trader-api/app/routers/signals.py simple-trader-api/app/services/totp_helper.py simple-trader-api/app/main.py
git commit -m "chore: delete scrapped web UI and dead broker/auth routers"
```

---

### Task 2: Fix strategy detection + report extraction in `tradingview-mcp-jackson`

**Files:**
- Modify: `tradingview-mcp-jackson/src/core/data.js`

**Interfaces:**
- Produces: `data.getStrategyResults()` returning `{ success, metric_count, source, metrics, error }` where `metrics` is `reportData().performance.all` (win_rate/profit_factor/total_trades/etc.) for any chart with the "ATH Reclaim - Final Verified" strategy applied. `data.getTrades({ max_trades })` returning `{ success, trade_count, source, trades, error }` where each trade is `{ entry_signal, entry_price, entry_time_ms, exit_signal, exit_price, exit_time_ms, qty, pnl, pnl_pct }`. Task 4 consumes both of these shapes directly.
- This task is **not unit-testable** (live CDP dependency, consistent with the rest of this file — see `docs/superpowers/specs/2026-08-11-daily-ath-scan-routine-design.md`, "Testing Strategy" for Step C). Verification is a live smoke test against the running TradingView Desktop app (Steps 2-4 below), not `node --test`.

- [ ] **Step 1: Fix the strategy-detection filter (3 occurrences)**

In `getStrategyResults()`, `getTrades()`, and `getEquity()`, replace every occurrence of:
```js
s.metaInfo().is_price_study === false
```
with:
```js
s.metaInfo().isTVScriptStrategy === true
```
(Leave the rest of each conditional — e.g. `&& (s.reportData || s.performance)` — unchanged.)

- [ ] **Step 2: Fix `getStrategyResults()`'s metric extraction**

Replace the body of `getStrategyResults()` (currently: flatten `strat.reportData()`'s own top-level scalar keys, then separately try `strat.performance()` as a fallback) with logic that resolves `reportData()`, drills into its `performance` property, and returns `performance.all` as the metrics object:

```js
export async function getStrategyResults() {
  const results = await evaluate(`
    (function() {
      try {
        var chart = ${CHART_API}._chartWidget;
        var sources = chart.model().model().dataSources();
        var strat = null;
        for (var i = 0; i < sources.length; i++) {
          var s = sources[i];
          if (s.metaInfo && s.metaInfo().isTVScriptStrategy === true) { strat = s; break; }
        }
        if (!strat) return {metrics: {}, source: 'internal_api', error: 'No strategy found on chart. Add a strategy indicator first.'};
        if (!strat.reportData) return {metrics: {}, source: 'internal_api', error: 'Strategy found but reportData() is unavailable.'};
        var rd = typeof strat.reportData === 'function' ? strat.reportData() : strat.reportData;
        if (rd && typeof rd.value === 'function') rd = rd.value();
        if (!rd || !rd.performance) return {metrics: {}, source: 'internal_api', error: 'reportData() has no performance data.'};
        var perf = rd.performance;
        if (perf && typeof perf.value === 'function') perf = perf.value();
        if (!perf || !perf.all) return {metrics: {}, source: 'internal_api', error: 'performance.all is unavailable.'};
        return {metrics: perf.all, source: 'internal_api'};
      } catch(e) { return {metrics: {}, source: 'internal_api', error: e.message}; }
    })()
  `);
  return { success: true, metric_count: Object.keys(results?.metrics || {}).length, source: results?.source, metrics: results?.metrics || {}, error: results?.error };
}
```

- [ ] **Step 3: Fix `getTrades()`'s data source and field shape**

Replace the body of `getTrades()` (currently reads `strat.ordersData()`/`strat._orders`/`strat.tradesData()` and flattens only non-object properties, which drops every field of interest) so it reads `strat.reportData().trades` and explicitly unpacks each trade's nested `e`/`x`/`tp` sub-objects into named fields:

```js
export async function getTrades({ max_trades } = {}) {
  const limit = Math.min(max_trades || 20, MAX_TRADES);
  const trades = await evaluate(`
    (function() {
      try {
        var chart = ${CHART_API}._chartWidget;
        var sources = chart.model().model().dataSources();
        var strat = null;
        for (var i = 0; i < sources.length; i++) {
          var s = sources[i];
          if (s.metaInfo && s.metaInfo().isTVScriptStrategy === true) { strat = s; break; }
        }
        if (!strat || !strat.reportData) return {trades: [], source: 'internal_api', error: 'No strategy found on chart.'};
        var rd = typeof strat.reportData === 'function' ? strat.reportData() : strat.reportData;
        if (rd && typeof rd.value === 'function') rd = rd.value();
        var list = rd && rd.trades;
        if (list && typeof list.value === 'function') list = list.value();
        if (!list || !Array.isArray(list)) return {trades: [], source: 'internal_api', error: 'reportData().trades is unavailable.'};
        var result = [];
        for (var t = 0; t < Math.min(list.length, ${limit}); t++) {
          var raw = list[t];
          result.push({
            entry_signal: raw.e ? raw.e.c : null,
            entry_price: raw.e ? raw.e.p : null,
            entry_time_ms: raw.e ? raw.e.tm : null,
            exit_signal: raw.x ? raw.x.c : null,
            exit_price: raw.x ? raw.x.p : null,
            exit_time_ms: raw.x ? raw.x.tm : null,
            qty: raw.q != null ? raw.q : null,
            pnl: raw.tp ? raw.tp.v : null,
            pnl_pct: raw.tp ? raw.tp.p : null,
          });
        }
        return {trades: result, source: 'internal_api'};
      } catch(e) { return {trades: [], source: 'internal_api', error: e.message}; }
    })()
  `);
  return { success: true, trade_count: trades?.trades?.length || 0, source: trades?.source, trades: trades?.trades || [], error: trades?.error };
}
```

- [ ] **Step 4: Live smoke test**

With TradingView Desktop running (CDP on port 9222) and a chart open with the "ATH Reclaim - Final Verified" strategy applied to a symbol with known trade history (e.g. `NSE:SIEMENS`), call the two fixed tools and confirm the numbers match the Strategy Tester panel's own displayed values:

```
mcp__tradingview-desktop__data_get_strategy_results
```
Expected: `success: true`, `metrics.percentProfitable`, `metrics.profitFactor`, `metrics.totalTrades`, `metrics.netProfitPercent` all present and non-null, matching the on-screen "Key stats" panel (open it first with `ui_open_panel` if needed).

```
mcp__tradingview-desktop__data_get_trades
```
Expected: `success: true`, `trades` is a non-empty array, each entry has `entry_price`/`entry_date`-equivalent (`entry_time_ms`)/`exit_signal` populated for closed trades.

Also verify on a symbol currently holding an open position (e.g. `NSE:RUBYMILLS` if still `reclaimed` in `symbol_state.json` at implementation time, or any other currently-`reclaimed` symbol): the **last** trade in the returned array has `exit_signal === ""`.

Record the exact tool outputs (or a summary of the key fields) in the task report as evidence — this is the test evidence for this task, since it has no automated suite.

- [ ] **Step 5: Commit**

```bash
git add tradingview-mcp-jackson/src/core/data.js
git commit -m "fix: strategy detection used is_price_study instead of isTVScriptStrategy"
```

---

### Task 3: New `ranking.js` module — pure ranking logic (TDD)

**Files:**
- Create: `tradingview-mcp-jackson/src/core/ranking.js`
- Test: `tradingview-mcp-jackson/tests/ranking.test.js`

**Interfaces:**
- Consumes: nothing external — pure functions only.
- Produces:
  - `RANKING_MIN_TRADES` (constant, value `5`)
  - `round2(n) -> number`
  - `toDateStr(unixSeconds) -> string` ("YYYY-MM-DD")
  - `findBarIndexByPrice(bars, field, targetPrice) -> number` (moved verbatim from `scan_step_c.mjs`, same behavior, no test changes needed for this one — it's an unmodified relocation)
  - `computeRankingFields(perf) -> { win_rate_pct, profit_factor, total_trades, net_profit_pct, ranking_eligible }` — `perf` is the `metrics` object from `data.getStrategyResults()` (i.e. `performance.all`), or `null`/`undefined` if that call failed.
  - `resolveHeldEntry({ trades, lastLabel, bars }) -> { entry_price, entry_date, source }` — `trades` is the array from `data.getTrades()`, `lastLabel` is the last Pine label object (`{ text, price, ... }`), `bars` is the OHLCV bars array. `source` is `"trades"` or `"bar_match"`.
- Task 4 imports all of the above from this module.

- [ ] **Step 1: Write the failing tests**

Create `tradingview-mcp-jackson/tests/ranking.test.js`:

```js
/**
 * Unit tests for ranking.js - pure logic, no TradingView connection needed.
 *
 * Run: node --test tests/ranking.test.js
 */
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  RANKING_MIN_TRADES,
  round2,
  toDateStr,
  findBarIndexByPrice,
  computeRankingFields,
  resolveHeldEntry,
} from '../src/core/ranking.js';

describe('computeRankingFields', () => {
  it('marks a symbol with enough trades as eligible and computes fields', () => {
    const perf = {
      percentProfitable: 0.625,
      profitFactor: 10.463243971430819,
      totalTrades: 8,
      netProfitPercent: 0.37231939712000006,
    };
    const result = computeRankingFields(perf);
    assert.deepEqual(result, {
      win_rate_pct: 62.5,
      profit_factor: 10.463243971430819,
      total_trades: 8,
      net_profit_pct: 37.23,
      ranking_eligible: true,
    });
  });

  it('is eligible at exactly the RANKING_MIN_TRADES floor', () => {
    const perf = { percentProfitable: 1, profitFactor: 5, totalTrades: RANKING_MIN_TRADES, netProfitPercent: 0.1 };
    const result = computeRankingFields(perf);
    assert.equal(result.ranking_eligible, true);
  });

  it('marks a symbol below the trade floor as ineligible with null fields', () => {
    const perf = { percentProfitable: 1, profitFactor: 999, totalTrades: 1, netProfitPercent: 2.5 };
    const result = computeRankingFields(perf);
    assert.deepEqual(result, {
      win_rate_pct: null,
      profit_factor: null,
      total_trades: 1,
      net_profit_pct: null,
      ranking_eligible: false,
    });
  });

  it('handles a null/failed strategy-results read', () => {
    const result = computeRankingFields(null);
    assert.deepEqual(result, {
      win_rate_pct: null,
      profit_factor: null,
      total_trades: null,
      net_profit_pct: null,
      ranking_eligible: false,
    });
  });
});

describe('resolveHeldEntry', () => {
  it('uses the trades array when the last trade is open (empty exit_signal)', () => {
    const trades = [
      { entry_signal: 'Long', entry_price: 60.2, entry_time_ms: 1095738300000, exit_signal: 'EMA Touch Exit', exit_price: 238.2, exit_time_ms: 1148269500000 },
      { entry_signal: 'Long', entry_price: 365.65, entry_time_ms: 1783568700000, exit_signal: '', exit_price: 401.55, exit_time_ms: 1787024700000 },
    ];
    const result = resolveHeldEntry({ trades, lastLabel: { text: 'RECLAIM #3', price: 365.65 }, bars: [] });
    assert.equal(result.source, 'trades');
    assert.equal(result.entry_price, 365.65);
    assert.equal(result.entry_date, toDateStr(1783568700000 / 1000));
  });

  it('falls back to bar-matching when the trades array is empty', () => {
    const bars = [
      { time: 1700000000, low: 100, close: 105 },
      { time: 1700086400, low: 110, close: 112 },
    ];
    const result = resolveHeldEntry({ trades: [], lastLabel: { text: 'RECLAIM #1', price: 110 }, bars });
    assert.equal(result.source, 'bar_match');
    assert.equal(result.entry_price, 112);
    assert.equal(result.entry_date, toDateStr(1700086400));
  });

  it('falls back to bar-matching when the last trade is already closed', () => {
    const trades = [
      { entry_signal: 'Long', entry_price: 60.2, entry_time_ms: 1095738300000, exit_signal: 'EMA Touch Exit', exit_price: 238.2, exit_time_ms: 1148269500000 },
    ];
    const bars = [{ time: 1700000000, low: 60.2, close: 61.0 }];
    const result = resolveHeldEntry({ trades, lastLabel: { text: 'RECLAIM #1', price: 60.2 }, bars });
    assert.equal(result.source, 'bar_match');
  });

  it('falls back to the label price when no bar match is found', () => {
    const result = resolveHeldEntry({ trades: [], lastLabel: { text: 'RECLAIM #1', price: 999.99 }, bars: [{ time: 1700000000, low: 1, close: 1 }] });
    assert.equal(result.source, 'bar_match');
    assert.equal(result.entry_price, 999.99);
    assert.equal(result.entry_date, null);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test tests/ranking.test.js`
Expected: FAIL — `Cannot find module '../src/core/ranking.js'` (file doesn't exist yet).

- [ ] **Step 3: Create `src/core/ranking.js`**

```js
/**
 * Pure ranking/entry-resolution logic for the Selection & Ranking stage.
 * No TradingView connection - safe to import from tests or scripts.
 */

export const RANKING_MIN_TRADES = 5;
const PRICE_MATCH_TOLERANCE_PCT = 0.5;

export function round2(n) {
  return Math.round(n * 100) / 100;
}

export function toDateStr(unixSeconds) {
  return new Date(unixSeconds * 1000).toISOString().slice(0, 10);
}

// Finds the bar whose `field` (open/high/low/close) most closely matches
// targetPrice, searching from the most recent bar backwards (label events
// are rare, so the closest match is almost always the intended one).
export function findBarIndexByPrice(bars, field, targetPrice) {
  let bestIdx = -1;
  let bestDiff = Infinity;
  for (let i = bars.length - 1; i >= 0; i--) {
    const diff = Math.abs(bars[i][field] - targetPrice);
    if (diff < bestDiff) {
      bestDiff = diff;
      bestIdx = i;
    }
  }
  if (bestIdx === -1 || bestDiff > targetPrice * (PRICE_MATCH_TOLERANCE_PCT / 100)) return -1;
  return bestIdx;
}

export function computeRankingFields(perf) {
  const total_trades = perf && perf.totalTrades != null ? perf.totalTrades : null;
  const ranking_eligible = total_trades !== null && total_trades >= RANKING_MIN_TRADES;
  if (!ranking_eligible) {
    return { win_rate_pct: null, profit_factor: null, total_trades, net_profit_pct: null, ranking_eligible: false };
  }
  return {
    win_rate_pct: round2((perf.percentProfitable ?? 0) * 100),
    profit_factor: perf.profitFactor,
    total_trades,
    net_profit_pct: round2((perf.netProfitPercent ?? 0) * 100),
    ranking_eligible: true,
  };
}

// A currently-held position is the *last* element of `trades` with an
// empty exit_signal (a mark-to-market snapshot, not a real exit) - see
// docs/superpowers/specs/2026-08-18-signal-pipeline-selection-design.md.
export function resolveHeldEntry({ trades, lastLabel, bars }) {
  const list = trades || [];
  const lastTrade = list.length ? list[list.length - 1] : null;
  if (lastTrade && lastTrade.exit_signal === '') {
    return {
      entry_price: lastTrade.entry_price,
      entry_date: toDateStr(lastTrade.entry_time_ms / 1000),
      source: 'trades',
    };
  }
  const entryIdx = findBarIndexByPrice(bars, 'low', lastLabel.price);
  return {
    entry_price: entryIdx >= 0 ? bars[entryIdx].close : lastLabel.price,
    entry_date: entryIdx >= 0 ? toDateStr(bars[entryIdx].time) : null,
    source: 'bar_match',
  };
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test tests/ranking.test.js`
Expected: PASS, all tests green, no warnings.

- [ ] **Step 5: Commit**

```bash
git add tradingview-mcp-jackson/src/core/ranking.js tradingview-mcp-jackson/tests/ranking.test.js
git commit -m "feat: add ranking.js with ranking-eligibility and held-entry resolution logic"
```

---

### Task 4: Wire `ranking.js` into `scan_step_c.mjs`

**Files:**
- Modify: `tradingview-mcp-jackson/scan_step_c.mjs`

**Interfaces:**
- Consumes: `RANKING_MIN_TRADES` is not referenced directly here (internal to `computeRankingFields`); imports `round2`, `toDateStr`, `findBarIndexByPrice`, `computeRankingFields`, `resolveHeldEntry` from `./src/core/ranking.js` (Task 3), and the fixed `data.getStrategyResults()`/`data.getTrades()` (Task 2).
- Produces: each entry in `{today}_verdicts_details.json` gains `win_rate_pct`, `profit_factor`, `total_trades`, `net_profit_pct`, `ranking_eligible`; `reclaimed` entries' `entry_price`/`entry_date` are now sourced via `resolveHeldEntry` instead of the old inline bar-matching block. Task 5 (`build_final_watchlist.py`) consumes these new field names directly from `symbol_state.json` (no changes needed to `update_symbol_state.py` — its merge already spreads every field from this output, confirmed during design).
- Not unit-testable (live CDP dependency, same as Task 2) — verified via a live smoke run in Step 4 below.

- [ ] **Step 1: Remove the now-duplicated local definitions and import from `ranking.js`**

Remove the local `round2`, `toDateStr`, and `findBarIndexByPrice` function definitions from `scan_step_c.mjs` (now living in `ranking.js`). Remove the now-unused `PRICE_MATCH_TOLERANCE_PCT` constant (moved into `ranking.js`).

Change the import line from:
```js
import { chart, data } from './src/core/index.js';
```
to:
```js
import { chart, data } from './src/core/index.js';
import { round2, toDateStr, findBarIndexByPrice, computeRankingFields, resolveHeldEntry } from './src/core/ranking.js';
```

- [ ] **Step 2: Add the ranking-fields fetch in `analyzeSymbol()`**

After the existing `athStudy`/`athLive`/`ema200Live` checks (right after the `missing_live_ath` early return, before the labels fetch), add:

```js
const strategyResults = await data.getStrategyResults();
const rankingFields = computeRankingFields(strategyResults?.metrics);
```

Add `...rankingFields` to the `base` object (the existing line building `base` from `distancePct`/`ema200Live`/`athLive`/`close`):

```js
const base = { distance_pct: round2(distancePct), ema200: ema200Live, absolute_ath: athLive, close, ...rankingFields };
```

This means every return path that already spreads `...base` (the `not_primed` skip, `reclaimed`, `approaching`, and the trailing `outside_band` skip) automatically carries the ranking fields. The three very-early skip returns (`stale_data_after_retries`, `strategy_not_found`, `missing_live_ath`, `insufficient_history` — before `base` exists) do **not** get ranking fields, matching the spec: those paths already return before there's any other analysis data either, and adding a live strategy-results call to failure paths that haven't even confirmed the study exists would add latency for no benefit.

- [ ] **Step 3: Replace the bar-matching entry-price block with `resolveHeldEntry`**

Replace this existing block (inside the `if (lastLabel && /^RECLAIM/.test(lastLabel.text))` branch):

```js
    const entryIdx = findBarIndexByPrice(bars, 'low', lastLabel.price);
    entry_date = entryIdx >= 0 ? toDateStr(bars[entryIdx].time) : null;
    entry_price = entryIdx >= 0 ? bars[entryIdx].close : lastLabel.price;
```

with:

```js
    const tradesResult = await data.getTrades({ max_trades: 20 });
    const resolved = resolveHeldEntry({ trades: tradesResult?.trades, lastLabel, bars });
    entry_price = resolved.entry_price;
    entry_date = resolved.entry_date;
```

Leave everything else in that branch (`dipConfirmed = true; isHeld = true;`) unchanged.

- [ ] **Step 4: Live smoke test**

With TradingView Desktop running and CDP up, run the routine against a small check list containing at least one currently-`reclaimed` symbol and one `approaching` or `skip` symbol (a 2-3 symbol subset is enough — do not run the full daily list for this smoke test):

```bash
node scan_step_c.mjs <path-to-small-test-check-list.json> <path-to-test-output.json>
```

Inspect `<test-output>_details.json` and confirm:
- Every entry has `win_rate_pct`, `profit_factor`, `total_trades`, `net_profit_pct`, `ranking_eligible` keys present (null or populated per eligibility).
- The `reclaimed` entry's `entry_price`/`entry_date` match what a manual `data_get_trades` call on that same symbol shows as its open position's entry (cross-check against the MCP tool directly, same way Task 2's Step 4 was verified).

Record the output (or a summary) in the task report as test evidence.

- [ ] **Step 5: Commit**

```bash
git add tradingview-mcp-jackson/scan_step_c.mjs
git commit -m "feat: scan_step_c.mjs pulls live ranking fields and exact held-entry price"
```

---

### Task 5: Rank and display in `build_final_watchlist.py` (TDD)

**Files:**
- Modify: `simple-trader-api/scripts/build_final_watchlist.py`
- Create: `simple-trader-api/tests/test_build_final_watchlist.py`

**Interfaces:**
- Consumes: `symbol_state.json` entries now carrying `win_rate_pct`, `profit_factor`, `total_trades`, `net_profit_pct`, `ranking_eligible` (from Task 4's output, merged in by the unchanged `update_symbol_state.py`).
- Produces: `compute_combined_rank(rows: list[dict]) -> None` (mutates each row dict in place, adding a `combined_rank` key: `float` for eligible rows, `None` for ineligible ones) — a new importable pure function, following the existing `build_check_list.py` convention of separating pure logic from the `main()` CLI wrapper.

- [ ] **Step 1: Write the failing tests**

Create `simple-trader-api/tests/test_build_final_watchlist.py`:

```python
"""Tests for build_final_watchlist.py's ranking logic."""
from scripts.build_final_watchlist import compute_combined_rank


def test_ranks_eligible_symbols_by_win_rate_and_profit_factor():
    rows = [
        {"symbol": "A", "ranking_eligible": True, "win_rate_pct": 80.0, "profit_factor": 2.0},
        {"symbol": "B", "ranking_eligible": True, "win_rate_pct": 60.0, "profit_factor": 10.0},
        {"symbol": "C", "ranking_eligible": True, "win_rate_pct": 90.0, "profit_factor": 8.0},
    ]
    compute_combined_rank(rows)
    ranks = {r["symbol"]: r["combined_rank"] for r in rows}
    # C: best win_rate (rank 0) + 2nd best profit_factor (rank 1) -> 0.5
    # A: 2nd best win_rate (rank 1) + worst profit_factor (rank 2) -> 1.5
    # B: worst win_rate (rank 2) + best profit_factor (rank 0) -> 1.0
    assert ranks["C"] < ranks["B"] < ranks["A"]


def test_ineligible_symbols_get_null_rank():
    rows = [
        {"symbol": "A", "ranking_eligible": True, "win_rate_pct": 80.0, "profit_factor": 2.0},
        {"symbol": "B", "ranking_eligible": False, "win_rate_pct": None, "profit_factor": None},
    ]
    compute_combined_rank(rows)
    assert rows[0]["combined_rank"] is not None
    assert rows[1]["combined_rank"] is None


def test_empty_list_does_not_error():
    rows = []
    compute_combined_rank(rows)
    assert rows == []


def test_all_ineligible_all_null():
    rows = [
        {"symbol": "A", "ranking_eligible": False, "win_rate_pct": None, "profit_factor": None},
        {"symbol": "B", "ranking_eligible": False, "win_rate_pct": None, "profit_factor": None},
    ]
    compute_combined_rank(rows)
    assert all(r["combined_rank"] is None for r in rows)


def test_tied_metrics_produce_equal_rank():
    rows = [
        {"symbol": "A", "ranking_eligible": True, "win_rate_pct": 70.0, "profit_factor": 3.0},
        {"symbol": "B", "ranking_eligible": True, "win_rate_pct": 70.0, "profit_factor": 3.0},
    ]
    compute_combined_rank(rows)
    assert rows[0]["combined_rank"] == rows[1]["combined_rank"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run (from `simple-trader-api/`): `python -m pytest tests/test_build_final_watchlist.py -v`
Expected: FAIL with `ImportError: cannot import name 'compute_combined_rank'`.

- [ ] **Step 3: Implement `compute_combined_rank` and wire it into row-building/sorting**

Add this function to `scripts/build_final_watchlist.py` (near the top, after the constants):

```python
def compute_combined_rank(rows):
    eligible = [r for r in rows if r.get("ranking_eligible")]
    by_win_rate = sorted(eligible, key=lambda r: -r["win_rate_pct"])
    by_profit_factor = sorted(eligible, key=lambda r: -r["profit_factor"])
    wr_rank = {r["symbol"]: i for i, r in enumerate(by_win_rate)}
    pf_rank = {r["symbol"]: i for i, r in enumerate(by_profit_factor)}
    for r in rows:
        if r.get("ranking_eligible"):
            r["combined_rank"] = (wr_rank[r["symbol"]] + pf_rank[r["symbol"]]) / 2
        else:
            r["combined_rank"] = None
```

In `main()`, when building each row dict for `reclaimed_rows`/`approaching_rows` (the two existing `.append({...})` calls), add the new fields from state:

```python
"win_rate_pct": r.get("win_rate_pct"), "profit_factor": r.get("profit_factor"),
"total_trades": r.get("total_trades"), "ranking_eligible": r.get("ranking_eligible", False),
```

After both lists are built (before the existing `reclaimed_rows.sort(...)`/`approaching_rows.sort(...)` lines), call:

```python
compute_combined_rank(reclaimed_rows)
compute_combined_rank(approaching_rows)
```

Replace the existing sort lines:
```python
reclaimed_rows.sort(key=lambda r: abs(r["distance_pct"]))
approaching_rows.sort(key=lambda r: abs(r["distance_pct"]))
```
with a sort that puts ranked (eligible) rows first, ordered by `combined_rank` ascending, and ineligible rows after, ordered by the existing `abs(distance_pct)`:

```python
def sort_key(r):
    if r["combined_rank"] is not None:
        return (0, r["combined_rank"])
    return (1, abs(r["distance_pct"]))

reclaimed_rows.sort(key=sort_key)
approaching_rows.sort(key=sort_key)
```

Change the `headers` list from:
```python
    headers = [
        "Symbol", "Status", "Cap Tier", "Market Cap (cr)", "Distance from Entry %",
        "Current Price", "Reference Price", "Reference", "EMA 200", "Entry Date",
        "Last Checked", "TradingView Link",
    ]
```
to:
```python
    headers = [
        "Symbol", "Status", "Cap Tier", "Market Cap (cr)", "Distance from Entry %",
        "Current Price", "Reference Price", "Reference", "EMA 200",
        "Win Rate %", "Profit Factor", "Total Trades", "Combined Rank",
        "Entry Date", "Last Checked", "TradingView Link",
    ]
```

Change the per-row cell-writing block from:
```python
        for r in group:
            ws.cell(row=row_idx, column=1, value=r["symbol"])
            ws.cell(row=row_idx, column=2, value=r["status"])
            ws.cell(row=row_idx, column=3, value=CAP_LABELS.get(r["cap_size"], "Unknown"))
            ws.cell(row=row_idx, column=4, value=r["market_cap_cr"])
            ws.cell(row=row_idx, column=5, value=r["distance_pct"])
            ws.cell(row=row_idx, column=6, value=r["close"])
            ws.cell(row=row_idx, column=7, value=r["reference_price"])
            ws.cell(row=row_idx, column=8, value=r["reference_label"])
            ws.cell(row=row_idx, column=9, value=r["ema200"])
            ws.cell(row=row_idx, column=10, value=r["entry_date"] or "")
            ws.cell(row=row_idx, column=11, value=r["last_checked"] or "")
            ws.cell(row=row_idx, column=12, value=f"https://in.tradingview.com/chart/?symbol=NSE:{r['symbol']}")
            row_idx += 1
```
to:
```python
        for r in group:
            ws.cell(row=row_idx, column=1, value=r["symbol"])
            ws.cell(row=row_idx, column=2, value=r["status"])
            ws.cell(row=row_idx, column=3, value=CAP_LABELS.get(r["cap_size"], "Unknown"))
            ws.cell(row=row_idx, column=4, value=r["market_cap_cr"])
            ws.cell(row=row_idx, column=5, value=r["distance_pct"])
            ws.cell(row=row_idx, column=6, value=r["close"])
            ws.cell(row=row_idx, column=7, value=r["reference_price"])
            ws.cell(row=row_idx, column=8, value=r["reference_label"])
            ws.cell(row=row_idx, column=9, value=r["ema200"])
            ws.cell(row=row_idx, column=10, value=r["win_rate_pct"])
            ws.cell(row=row_idx, column=11, value=r["profit_factor"])
            ws.cell(row=row_idx, column=12, value=r["total_trades"])
            ws.cell(row=row_idx, column=13, value=r["combined_rank"])
            ws.cell(row=row_idx, column=14, value=r["entry_date"] or "")
            ws.cell(row=row_idx, column=15, value=r["last_checked"] or "")
            ws.cell(row=row_idx, column=16, value=f"https://in.tradingview.com/chart/?symbol=NSE:{r['symbol']}")
            row_idx += 1
```
(`None` values for `win_rate_pct`/`profit_factor`/`total_trades`/`combined_rank` write as blank cells in openpyxl — no special-casing needed.) The `column_dimensions` loop below already iterates `enumerate(headers, start=1)` dynamically, so it needs no changes.

- [ ] **Step 4: Run tests to verify they pass**

Run (from `simple-trader-api/`): `python -m pytest tests/test_build_final_watchlist.py -v`
Expected: PASS, all 5 tests green.

Run the full existing suite to confirm nothing else broke: `python -m pytest tests/ -v`
Expected: all tests pass (no other test file imports from `build_final_watchlist.py`, but confirm).

- [ ] **Step 5: Commit**

```bash
git add simple-trader-api/scripts/build_final_watchlist.py simple-trader-api/tests/test_build_final_watchlist.py
git commit -m "feat: rank watchlist by win-rate/profit-factor, add ranking columns to Excel"
```

---

## Self-Review Notes

- **Spec coverage:** Part A (Cleanup) -> Task 1. Prerequisite fix -> Task 2. `scan_step_c.mjs` ranking-field extraction and entry-price replacement -> Tasks 3-4. `build_final_watchlist.py` ranking/sort/columns -> Task 5. `update_symbol_state.py` explicitly needs no changes (confirmed in the spec and restated in Task 4's Interfaces) — no task created for it, correctly.
- **Type/interface consistency:** `ranking_eligible`, `win_rate_pct`, `profit_factor`, `total_trades`, `net_profit_pct` field names are identical across Task 3 (produces), Task 4 (wires/produces in JSON output), and Task 5 (consumes) — verified no drift between the JS camelCase-to-snake_case mapping and the Python side, which reads the same `symbol_state.json` keys verbatim.
- **No placeholders:** every step has real, complete code — no "add appropriate handling" language.
