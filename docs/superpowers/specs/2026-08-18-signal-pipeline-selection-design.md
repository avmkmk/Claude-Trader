---
name: Signal Pipeline - Selection & Ranking Design
description: Product pivot from a multi-strategy web app to a single-strategy automated pipeline (technical scan -> ranked selection -> Telegram delivery -> fundamentals); this spec covers the cleanup and the Selection/Ranking stage in full detail
type: design
date: 2026-08-18
---

# Signal Pipeline: Selection & Ranking Design

## Overview

The project is pivoting away from a multi-strategy, multi-broker web application
toward a single, fully automated daily pipeline built around one proven
strategy (`ath_reclaim_daily_v1` / the "ATH Reclaim - Final Verified" Pine
script). The eventual shape is:

1. **Technical scan** (already built — the `/daily-ath-scan` skill, see
   `docs/superpowers/specs/2026-08-11-daily-ath-scan-routine-design.md`):
   Chartink screening + live TradingView confirmation, producing a daily
   Reclaimed/Approaching watchlist.
2. **Selection & Ranking** (this spec): from that watchlist, rank symbols by
   how well the strategy has actually performed on each one historically,
   using the strategy's own live backtest report — not a static dataset.
3. **Telegram delivery + scheduling**: an unattended daily trigger that sends
   the top 5 ranked picks to a registered user via Telegram DM.
4. **Fundamental analysis**: enrich the shortlist with news + financials
   before delivery.

Steps 3 and 4 are deliberately built in that order (delivery before
fundamentals) so a working, useful end-to-end pipeline exists as early as
possible — the first live Telegram messages will carry technical/ranking
data only, with fundamentals layered in later without changing the delivery
mechanism.

This spec covers the **cleanup** (mechanical) and the **Selection & Ranking**
stage (fully designed) in detail. Delivery/scheduling and fundamentals are
named here only as forward-looking scope, to be designed in their own
revisions or follow-up specs when their turn comes.

## Relationship to Existing Specs

- `docs/superpowers/specs/2026-04-13-ath-monitoring-design.md` and
  `docs/superpowers/specs/2026-08-11-daily-ath-scan-routine-design.md`
  cover the technical scan (Step 1 above). The `/daily-ath-scan` skill is
  unchanged by this spec except for the entry-price-accuracy improvement
  described under Selection & Ranking below, which happens to close a gap
  explicitly parked as out-of-scope in the 2026-08-11 spec's 2026-08-18
  revision ("Fragile bar-price-matched entry_date/entry_price recovery").
- This spec supersedes the original multi-strategy, multi-broker product
  direction implied by the top-level `CLAUDE.md` project structure (backtest
  UI, order execution, holdings sync). Those pieces are being removed, not
  extended.

## Scope Decisions

Established through brainstorming on 2026-08-18:

- **Delete `simple-trader-web/` entirely.** No web UI going forward — the
  product is a headless daily routine ending in a Telegram message.
- **Delete routers:** `orders.py`, `holdings.py`, `auth.py`, `watchlist.py`,
  `signals.py`. These exist only to serve the scrapped UI / broker-execution
  vision; the pipeline is suggestion-only.
- **Keep:** `scanner.py`, `chartink_scraper.py`, `ath_analyzer.py` — already
  in active use by `/daily-ath-scan`.
- **Deferred:** disposition of `news_client.py` / `ai_client.py` (candidate
  building blocks for the fundamentals stage) — decide when that stage is
  designed.
- **Build order:** Cleanup → Selection & Ranking (this spec) → Telegram
  Delivery + Scheduling → Fundamental Analysis.

## Part A: Cleanup

Mechanical, no design required:

- Delete `simple-trader-web/` (entire directory).
- Delete `simple-trader-api/app/routers/orders.py`, `holdings.py`,
  `auth.py`, `watchlist.py`, `signals.py`.
- Remove their registrations from `simple-trader-api/app/main.py`.
- Remove any service code that exists solely to support the deleted
  routers (confirm via grep for imports before deleting — e.g. broker
  order-placement helpers in `apis/` may be shared with backtesting and
  should stay if so).

## Part B: Selection & Ranking

### Problem

"Choose which ones have worked for us historically well from the
watchlist" requires per-symbol historical performance data for the exact
strategy in use. A static backtest CSV
(`ath_reclaim_nifty500_detailed_results.csv`, dated 2026-04-13) was
initially considered, but only 11 of the 71 symbols in the current
watchlist appear in it — an 85% coverage gap, and the dataset would need
manual re-generation and storage maintenance to stay useful.

**Decision:** pull each symbol's backtest performance live, on demand,
from the TradingView Strategy Tester itself — the exact engine already
running the exact strategy, for the exact symbol, at scan time. No static
dataset, no coverage gap, no storage to maintain.

### Prerequisite Fix: `tradingview-mcp-jackson` Strategy Detection Bug

**File:** `tradingview-mcp-jackson/src/core/data.js`

Three functions (`getStrategyResults`, `getTrades`, `getEquity`) each walk
the chart's `dataSources()` looking for the strategy object, using this
filter:

```js
if (s.metaInfo && s.metaInfo().is_price_study === false && (s.reportData || s.performance)) { strat = s; break; }
```

Confirmed live (2026-08-18, chart loaded with "ATH Reclaim - Final
Verified" on SIEMENS) that this strategy's `metaInfo().is_price_study` is
`true` — it's an overlay strategy plotted directly on the price pane, not
a separate-pane oscillator. The filter's `=== false` assumption is wrong
for any overlay strategy, so it always fails to find ours, producing the
`"No strategy found on chart"` error `data_get_strategy_results` and
`data_get_trades` have both been observed returning.

The correct detection field, confirmed present on the same object:
`metaInfo().isTVScriptStrategy === true`.

**Fix 1 — detection filter (3 occurrences in `data.js`):** replace
`s.metaInfo().is_price_study === false` with
`s.metaInfo().isTVScriptStrategy === true` in `getStrategyResults`,
`getTrades`, and `getEquity`.

**Fix 2 — `getStrategyResults` metric extraction:** the current
implementation only lifts top-level scalar keys off `strat.reportData()`
(filtering out anything `typeof === 'object'`), then separately falls
back to `strat.performance()` — a different, unrelated property. The
metrics needed for ranking live nested at
`reportData().performance.all.{percentProfitable, profitFactor,
totalTrades, netProfitPercent, sharpeRatio, ...}`, which the current
top-level-only scan never reaches. Fix: after resolving `reportData()`
(calling `.value()` if it's a function-returning wrapper, as the existing
code already does), read `rd.performance` (calling `.value()` on it too
if needed), then return `rd.performance.all` as the metrics object
directly, rather than flattening `rd`'s own top-level keys.

**Fix 3 — `getTrades` data source and field shape:** the current
implementation reads `strat.ordersData()` (falling back to `strat._orders`
or `strat.tradesData()`), then flattens each order object by keeping only
`typeof v !== 'object'` properties — which drops every field that matters,
because each trade in the real data is a compact object with **nested**
sub-objects:

```json
{
  "e": {"c": "Long", "p": 365.65, "tm": 1783568700000},
  "x": {"c": "EMA Touch Exit", "p": 401.55, "tm": 1787024700000},
  "tp": {"v": 9716.92, "p": 0.0973},
  "q": 273
}
```

(`e` = entry, `x` = exit, `tp` = total profit, `q` = quantity; `c` =
signal label, `p` = price, `tm` = unix ms timestamp.) Confirmed live for
both a fully closed history (SIEMENS, 8 trades back to 2004) and a
currently-open position (RUBYMILLS, 3 trades, last one open — see below).

Fix: switch `getTrades`'s data source from `strat.ordersData()` to
`strat.reportData().trades` (the same `reportData()` already used by
`getStrategyResults`, resolved the same way), and change the flattening
logic to explicitly unpack the nested sub-objects into named fields
instead of dropping them:

```js
{
  entry_signal: t.e?.c, entry_price: t.e?.p, entry_time_ms: t.e?.tm,
  exit_signal: t.x?.c, exit_price: t.x?.p, exit_time_ms: t.x?.tm,
  qty: t.q, pnl: t.tp?.v, pnl_pct: t.tp?.p,
}
```

**Open-position detection:** a currently-held trade appears as the *last*
element of `trades[]` with an **empty** `exit_signal` (`x.c === ""`) —
confirmed live for RUBYMILLS, whose `performance.all.totalOpenTrades`
was `1` and whose last trade had `x: {c: "", p: 401.55, tm: ...}` (a
mark-to-market snapshot at the time of the read, not a real exit). A
closed trade's `exit_signal` is always a real label (e.g.
`"EMA Touch Exit"`). This distinction — not the trade's position in the
array alone — is how downstream code (below) identifies "this is the
currently open position" vs. "this is historical."

### Data Extraction: `scan_step_c.mjs` Changes

**File:** `tradingview-mcp-jackson/scan_step_c.mjs`

`analyzeSymbol()` already switches the chart to each candidate symbol and
reads Pine's live labels/study values for the verdict. Extend it to also
call the fixed `data.getStrategyResults()` and `data.getTrades()` while
already on that symbol's chart — no additional chart switches needed.

**Ranking fields** (added to every symbol's result object, regardless of
verdict):

```js
const strategyResults = await data.getStrategyResults();
const perf = strategyResults.metrics; // == reportData().performance.all, post-fix
const total_trades = perf?.totalTrades ?? null;
const ranking_eligible = total_trades !== null && total_trades >= 5;
const ranking = ranking_eligible ? {
  win_rate_pct: round2((perf.percentProfitable ?? 0) * 100),
  profit_factor: perf.profitFactor,
  total_trades,
  net_profit_pct: round2((perf.netProfitPercent ?? 0) * 100),
} : { win_rate_pct: null, profit_factor: null, total_trades, net_profit_pct: null };
```

- `ranking_eligible = total_trades >= 5` — the eligibility floor agreed
  during design, protecting against small-sample noise (e.g. a 1-trade
  100%-win-rate symbol producing an infinite/undefined `profit_factor`
  that would otherwise dominate rankings).
- Symbols below the floor, or where the strategy-results read fails
  entirely (transient CDP hiccup, same class of failure already handled
  for the rest of Step C), still get a verdict as today — they are simply
  `ranking_eligible: false` with null ranking fields, never dropped from
  the scan.

**Entry-price replacement** (for `isHeld === true` symbols only — i.e.
verdict `reclaimed`): replace the existing `findBarIndexByPrice`-based
lookup (current lines 224–231, matching the RECLAIM label's price against
a 500-bar-capped OHLCV window) with a direct read from `getTrades()`:

```js
const trades = await data.getTrades({ max_trades: 20 });
const lastTrade = trades.trades[trades.trades.length - 1];
const openTrade = lastTrade && lastTrade.exit_signal === '' ? lastTrade : null;
if (openTrade) {
  entry_price = openTrade.entry_price;
  entry_date = toDateStr(openTrade.entry_time_ms / 1000);
} else {
  // Fall back to the existing bar-matching approach if the trades read
  // failed or didn't show an open position for a symbol Pine's own
  // labels say is held — never fail the symbol over this.
  const entryIdx = findBarIndexByPrice(bars, 'low', lastLabel.price);
  entry_date = entryIdx >= 0 ? toDateStr(bars[entryIdx].time) : null;
  entry_price = entryIdx >= 0 ? bars[entryIdx].close : lastLabel.price;
}
```

This is a strict accuracy improvement over the existing approach: it
works for trades of any age (not capped by the 500-bar OHLCV fetch
window) and reads the strategy engine's own recorded fill price directly,
rather than approximating it by matching a label's y-position against
nearby bars. It directly closes the "fragile bar-price-matched
entry_date/entry_price recovery" gap parked as explicitly out-of-scope in
the 2026-08-11 spec's 2026-08-18 revision.

**Output:** `{today}_verdicts_details.json` entries gain
`win_rate_pct`, `profit_factor`, `total_trades`, `net_profit_pct`,
`ranking_eligible` alongside the existing fields; `entry_price`/
`entry_date` are unchanged in name and meaning, just more accurate for
`reclaimed` symbols.

### State Persistence: No Changes Needed

`simple-trader-api/scripts/update_symbol_state.py`'s merge logic
(`merge_new_results`) writes `state[symbol] = {**r, cap_size, market_cap_cr,
last_checked}` — a full spread of each result dict `r` from
`{today}_verdicts_details.json`. The new ranking fields flow through
automatically with **zero changes** to this file. (Its existing
entry-price-preservation invariant, which guards against a re-check
silently drifting a stored `entry_price` for the same `entry_date`,
remains a harmless safety net now that the underlying derivation is
exact rather than approximate — no changes needed there either.)

### Watchlist Output: `build_final_watchlist.py` Changes

**File:** `simple-trader-api/scripts/build_final_watchlist.py`

Add a rank computation before building rows: for each status group
(Reclaimed, Approaching) independently, among symbols with
`ranking_eligible: true`, rank by `win_rate_pct` descending and by
`profit_factor` descending, then combine:

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

Averaging independent rank positions (rather than multiplying raw
`win_rate_pct * profit_factor`) avoids one unbounded metric
(`profit_factor` has no upper limit for a strong-but-thin edge)
dominating the score.

**Sort order change:** within each status group, sort by
`combined_rank` ascending (lower = better) with `ranking_eligible: false`
rows sorted after all eligible ones, falling back to the existing
`abs(distance_pct)` ordering as a tiebreaker within each sub-group. This
replaces the current pure `abs(distance_pct)` sort as the primary key —
ranking by track record is the point of this stage.

**New columns** added to the Excel output: `Win Rate %`, `Profit Factor`,
`Total Trades`, `Combined Rank`. Symbols with `ranking_eligible: false`
show blank/`N/A` in these columns rather than being dropped from the
sheet — consistent with this session's established principle of not
silently losing information from the watchlist (see the 2026-08-18
`data/daily_scans/` cleanup discussion). Nothing is excluded from the
**visible watchlist**; ranking only determines **order**, and downstream
selection (Telegram top-5, Part D) is what actually filters to eligible,
top-ranked symbols.

### Testing Strategy

- `tradingview-mcp-jackson/src/core/data.js`: not unit-testable in
  isolation (live CDP dependency) — validated the same way the rest of
  Step C is: running against a live chart and confirming the returned
  metrics match the Strategy Tester panel's own displayed numbers
  (already spot-checked for SIEMENS: net profit, win rate, profit
  factor, and drawdown all matched exactly during design).
- `scan_step_c.mjs`: unit test the ranking-field derivation and the
  open-trade detection (`exit_signal === ''`) with fixed fixtures —
  eligible (≥5 trades), ineligible (<5 trades), and a strategy-results
  read failure (falls back to null ranking fields, doesn't fail the
  symbol). Unit test the entry-price fallback path (trades read
  succeeds but shows no open position for a symbol whose labels say
  held → falls back to bar-matching) separately from the primary path.
- `build_final_watchlist.py`: unit test `compute_combined_rank` with
  fixed fixtures — all eligible, mixed eligible/ineligible, and a tie
  case (two symbols with identical win_rate_pct and profit_factor).
  Unit test the sort order (eligible-by-rank first, ineligible after,
  each internally consistent) independent of the live pipeline.

### Success Criteria

1. `data_get_strategy_results` and `data_get_trades` return real metrics
   for the "ATH Reclaim - Final Verified" strategy on any symbol with
   trade history, matching what the Strategy Tester panel displays.
2. Every symbol checked by `scan_step_c.mjs` carries ranking fields
   (or explicit nulls + `ranking_eligible: false`) — no silent gaps.
3. `reclaimed` symbols' `entry_price`/`entry_date` are sourced from the
   strategy's own trade record, not bar-price matching, for any trade
   age.
4. The final watchlist Excel is sorted by combined rank within each
   status group, with rank-ineligible symbols visible but ordered last.
5. No static per-symbol backtest dataset is introduced or maintained.

## Deferred: Part D — Telegram Delivery & Scheduling

To be designed separately. Known constraints from brainstorming
(2026-08-18):
- Ships before fundamentals (Part C) — first live messages carry
  technical/ranking data only.
- Scheduling trigger (pre-market vs. post-market vs. both; Windows Task
  Scheduler vs. another mechanism) not yet decided.
- "Subscription-based" delivery implied (per the user's stated plan and
  `PHASE4_COMPLETE.md`'s prior "Phase 5: Telegram Channel Bot (Multi-User
  Broadcast)" notes) but single-user MVP scope not yet confirmed.

## Deferred: Part C — Fundamental Analysis

To be designed separately, after Part D ships. Candidate building blocks
already in the codebase: `simple-trader-api/app/services/news_client.py`
(Marketaux + Alpha Vantage) and `ai_client.py` (Gemini) — reuse vs.
rebuild not yet decided.

## Open Questions / Future Enhancements

- Whether `getEquity()`'s bug fix (same `is_price_study` issue, fixed
  alongside the other two for consistency) has any near-term consumer,
  or is fixed opportunistically now since it's the same one-line change.
- Whether the ranking formula (win-rate/profit-factor rank average)
  should later incorporate `sharpeRatio` or `sortinoRatio` once a
  business definition for handling their flat-time dilution (noted
  during design — SIEMENS showed -0.01 Sharpe despite an excellent
  trade record) is worked out. Not needed for the MVP ranking.
