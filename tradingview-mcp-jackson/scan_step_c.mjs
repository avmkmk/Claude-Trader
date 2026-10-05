/**
 * Daily ATH scan routine - Step C (automated via CDP, no screenshots).
 *
 * For each candidate symbol, determines the live "ATH Reclaim - Final
 * Verified" Pine strategy's current state by reading its own drawn
 * RECLAIM/EXIT labels - the strategy's actual output - rather than
 * re-deriving the phase state machine from raw OHLCV in JS.
 *
 * An earlier version replayed the strategy's phase logic (dormant -> new
 * peak set -> dipped below EMA200, primed -> reclaim) bar-by-bar over
 * getOhlcv's 500-bar cap. That produced false "reclaimed" verdicts: the
 * 500-bar window doesn't reach back to the stock's listing, so the replay
 * had to start mid-history with phase/absoluteAth reset to 0, and any local
 * price high inside the window got misread as a fresh "new peak" even when
 * the real Pine engine (which carries true state from inception) was
 * already past that point. E.g. for ALIVUS the replay invented a reclaim on
 * 2026-04-21, when the strategy's own RECLAIM #2 label was actually on
 * 2026-08-04 - a state that had been running since before the fetch window
 * even started.
 *
 * Labels are ground truth because Pine computes them once, correctly, over
 * the symbol's whole chart history:
 *   - last label is "RECLAIM #N" and no EXIT since -> still holding that
 *     entry -> verdict "reclaimed". The label's y-position is the entry
 *     bar's low (label.new(bar_index, low, ...)), so the exact entry date
 *     is recovered by matching that price against OHLCV bar lows.
 *   - last label is "EXIT" (y-position = bar's high) or no labels exist ->
 *     currently flat. Whether it's "approaching" (primed, phase 2) is then
 *     just: has close dipped below EMA200 at any point since that EXIT bar
 *     (or since the start of the fetched window, if no labels)? Once phase
 *     reaches 2 in the real strategy it stays 2 regardless of further
 *     wiggles until an actual reclaim, so this single boolean check is
 *     sufficient and, unlike the old replay, doesn't require reconstructing
 *     absoluteAth's full history to be correct.
 *
 * Usage:
 *   node scan_step_c.mjs <candidates.json> <verdicts_out.json>
 */
import { chart, data } from './src/core/index.js';
import { evaluate } from './src/connection.js';
import { round2, toDateStr, findBarIndexByPrice, computeRankingFields, resolveHeldEntry } from './src/core/ranking.js';
import fs from 'fs';
import path from 'path';

const EMA_PERIOD = 200;
const STRATEGY_NAME = 'ATH Reclaim - Final Verified';
const BUY_ZONE_PCT = 5.0; // build_excel.py does no distance filtering itself - the band must be enforced here

// Rejected symbols (skip verdicts) are cached for REJECTION_COOLDOWN_DAYS so
// re-runs on later days don't re-drive the live TradingView desktop check
// for stocks that are very unlikely to have changed state - e.g. a stock
// -36% below its ATH won't be in the buy zone tomorrow either, and the
// Chartink screeners tend to keep resurfacing the same names for days at a
// stretch. Verdicts caused by a transient read/data problem (not an actual
// analysis outcome) are never cached, so those are always retried fresh.
const REJECTION_COOLDOWN_DAYS = 3;
const TRANSIENT_SKIP_REASONS = new Set([
  'strategy_not_found', 'missing_live_ath', 'insufficient_history',
  'stale_data_after_retries', 'ohlcv_error', 'error',
]);

const [, , candidatesPath, outputPath, cachePathArg] = process.argv;
if (!candidatesPath || !outputPath) {
  console.error('Usage: node scan_step_c.mjs <candidates.json> <verdicts_out.json> [rejection_cache.json]');
  process.exit(1);
}

const candidates = JSON.parse(fs.readFileSync(candidatesPath, 'utf8'));

// run_daily.py passes the persistent cache in data/state/; standalone use falls back to next to the output file
const cachePath = cachePathArg || path.join(path.dirname(outputPath), '_rejection_cache.json');

function loadRejectionCache() {
  try {
    return JSON.parse(fs.readFileSync(cachePath, 'utf8'));
  } catch {
    return {};
  }
}

function daysSince(dateStr) {
  const then = new Date(dateStr + 'T00:00:00Z').getTime();
  const now = new Date(new Date().toISOString().slice(0, 10) + 'T00:00:00Z').getTime();
  return Math.round((now - then) / 86400000);
}

function parseNumber(v) {
  if (typeof v === 'number') return v;
  if (typeof v === 'string') return parseFloat(v.replace(/,/g, ''));
  return NaN;
}

function computeEma(closes, period) {
  const ema = new Array(closes.length).fill(null);
  if (closes.length < period) return ema;
  let sum = 0;
  for (let i = 0; i < period; i++) sum += closes[i];
  ema[period - 1] = sum / period;
  const k = 2 / (period + 1);
  for (let i = period; i < closes.length; i++) {
    ema[i] = closes[i] * k + ema[i - 1] * (1 - k);
  }
  return ema;
}

// chart.setSymbol()'s own readiness wait can time out (returns chart_ready:
// false) before the Pine strategy has actually recalculated on the new
// symbol, leaving getStudyValues()/getQuote() reading stale data left over
// from the previous symbol for a short window. Confirm the chart legend
// itself has switched, then cross-check quote.close against the OHLCV
// series' own last close (same underlying data, fetched independently) -
// if they disagree, the read raced the recalculation, so retry.
async function switchSymbolAndWaitReady(tvSymbol, bareSymbol) {
  await chart.setSymbol({ symbol: tvSymbol });
  for (let i = 0; i < 10; i++) {
    const state = await chart.getState();
    if (state.symbol && state.symbol.toUpperCase().includes(bareSymbol.toUpperCase())) return true;
    await new Promise((r) => setTimeout(r, 300));
  }
  return false;
}

async function fetchConsistentSnapshot(symbol) {
  for (let attempt = 0; attempt < 3; attempt++) {
    const quote = await data.getQuote({});
    const studyValues = await data.getStudyValues();
    const ohlcv = await data.getOhlcv({ count: 500, summary: false });
    const bars = ohlcv.bars || [];

    if (bars.length > 0 && Math.abs(quote.close - bars[bars.length - 1].close) / bars[bars.length - 1].close > 0.005) {
      await new Promise((r) => setTimeout(r, 600));
      continue;
    }
    return { quote, studyValues, bars };
  }
  return null;
}

async function analyzeSymbol(symbol) {
  const tvSymbol = `NSE:${symbol}`;
  await switchSymbolAndWaitReady(tvSymbol, symbol);

  const snapshot = await fetchConsistentSnapshot(symbol);
  if (!snapshot) {
    return { symbol, verdict: 'skip', reason: 'stale_data_after_retries' };
  }
  const { quote, studyValues, bars } = snapshot;

  const athStudy = (studyValues.studies || []).find((s) => s.name === STRATEGY_NAME);
  if (!athStudy) {
    return { symbol, verdict: 'skip', reason: 'strategy_not_found' };
  }
  const athLive = parseNumber(athStudy.values['Absolute ATH']);
  const ema200Live = parseNumber(athStudy.values['EMA 200']);
  const close = quote.close;
  if (!isFinite(athLive) || !athLive) {
    return { symbol, verdict: 'skip', reason: 'missing_live_ath' };
  }

  const labelsResult = await data.getPineLabels({ study_filter: 'ATH Reclaim', max_labels: 50 });
  const labelStudy = (labelsResult.studies || []).find((s) => s.name === STRATEGY_NAME);
  const labels = labelStudy ? labelStudy.labels : [];
  const lastLabel = labels.length ? labels[labels.length - 1] : null;

  if (bars.length < EMA_PERIOD + 10) {
    return { symbol, verdict: 'skip', reason: 'insufficient_history', bar_count: bars.length };
  }

  const strategyResults = await data.getStrategyResults();
  const rankingFields = computeRankingFields(strategyResults?.metrics);

  const distancePct = ((close - athLive) / athLive) * 100;
  const base = { distance_pct: round2(distancePct), ema200: ema200Live, absolute_ath: athLive, close, ...rankingFields };

  // A symbol only counts as primed if it has been through at least one real
  // dip-below-EMA200 cycle - otherwise "close to its ATH" just means it's
  // making fresh highs with no pullback structure yet (e.g. today's high is
  // itself the new ATH), which isn't a reclaim setup at all.
  //
  // Still holding an entry (last label RECLAIM, no EXIT since) already
  // proves a dip happened before that entry, no matter how long ago it
  // fired - and since absoluteAth keeps ratcheting up even while a position
  // is held, price can currently sit slightly *below* that still-open
  // entry's now-higher ATH (e.g. AUROPHARMA holding since an earlier
  // reclaim, currently -0.06% vs its climbed ATH). That is functionally the
  // same "sitting just under a rising high" setup as a flat approaching
  // stock, so both cases are classified by the same distance band below,
  // not gated on whether Pine's own position is technically still open.
  //
  // A last label of EXIT also already proves a dip happened (the one before
  // the entry that just got stopped out) - the live strategy now re-arms
  // straight to phase 2 on exit (see ath-reclaim-pinecone.txt), so simply
  // re-crossing the same absoluteAth level counts as a fresh valid entry;
  // no additional post-exit dip is required. Only a symbol with no labels
  // at all (never been through a cycle) still needs the actual EMA-dip scan.
  let dipConfirmed = false;
  let isHeld = false;
  let entry_date = null;
  let entry_price = null;

  if (lastLabel && /^RECLAIM/.test(lastLabel.text)) {
    dipConfirmed = true;
    isHeld = true;
    // Prefer the strategy's own recorded trade fill (exact, any trade age)
    // over bar-price matching, which is capped by the 500-bar OHLCV window
    // and only approximate even within it. resolveHeldEntry falls back to
    // bar-matching automatically if the trades read fails or shows no open
    // position for a symbol Pine's own labels say is held.
    const tradesResult = await data.getTrades({ max_trades: 20 });
    const resolved = resolveHeldEntry({ trades: tradesResult?.trades, lastLabel, bars });
    entry_price = resolved.entry_price;
    entry_date = resolved.entry_date;
  } else if (lastLabel && lastLabel.text === 'EXIT') {
    dipConfirmed = true;
  } else {
    const ema = computeEma(bars.map((b) => b.close), EMA_PERIOD);
    for (let i = EMA_PERIOD - 1; i < bars.length; i++) {
      if (ema[i] != null && bars[i].close < ema[i]) {
        dipConfirmed = true;
        break;
      }
    }
  }

  if (!dipConfirmed) {
    return { symbol, verdict: 'skip', reason: 'not_primed', ...base };
  }

  // Held positions (RECLAIM fired, no EXIT since) are governed by the
  // strategy's actual risk rule - EMA200 as the stop on both sides - not a
  // fixed distance-from-ATH band. Pine's own EXIT label is exactly that
  // stop: if it hasn't fired, the trade is still valid no matter how far
  // price has since moved from the (possibly since-ratcheted) ATH, so it's
  // always "reclaimed" here. The ±BUY_ZONE_PCT band still applies to the
  // flat/"approaching" case, where distance-from-ATH is the right question
  // (how close is price to triggering a *new* entry).
  if (isHeld) {
    const distance_from_entry_pct = entry_price ? round2(((close - entry_price) / entry_price) * 100) : null;
    return { symbol, verdict: 'reclaimed', ...base, entry_date, entry_price, distance_from_entry_pct };
  }
  if (distancePct < 0 && distancePct >= -BUY_ZONE_PCT) {
    return { symbol, verdict: 'approaching', ...base, entry_date };
  }
  return { symbol, verdict: 'skip', reason: 'outside_band', ...base, entry_date };
}

// After TradingView is (re)launched the debug port answers well before the chart widget exists; reading symbols in that
// window makes every one error out. Wait for a real chart, and say why if it never appears (e.g. not signed in).
const CHART_READY_EXPR = "(function(){try{var w=window.TradingViewApi&&window.TradingViewApi._activeChartWidgetWV;return !!(w&&w.value()&&w.value()._chartWidget)}catch(e){return false}})()";
async function waitForChartReady(timeoutMs = 180000) {
  const start = Date.now();
  let lastErr = '';
  while (Date.now() - start < timeoutMs) {
    try {
      // each attempt is time-boxed: evaluate() can hang when the debug port has gone away
      const ready = await Promise.race([evaluate(CHART_READY_EXPR), new Promise((_, rej) => setTimeout(() => rej(new Error('CDP evaluate timed out')), 10000))]);
      if (ready) return true;
    } catch (e) { lastErr = String(e.message || e); }
    await new Promise((r) => setTimeout(r, 3000));
  }
  console.error(`TradingView chart not ready after ${Math.round(timeoutMs / 1000)}s${lastErr ? ` (${lastErr})` : ''}. Is TradingView signed in and showing a chart?`);
  return false;
}

// If most live reads error out the run is useless (and must not be merged into state): abort without writing anything.
const MAX_ERROR_RATIO = 0.25;

async function main() {
  if (!(await waitForChartReady())) process.exit(2);
  const verdicts = {};
  const details = [];
  const rejectionCache = loadRejectionCache();
  const today = new Date().toISOString().slice(0, 10);
  let cachedSkips = 0;

  for (const c of candidates) {
    const symbol = c.symbol;
    const cached = rejectionCache[symbol];

    if (cached && daysSince(cached.date) <= REJECTION_COOLDOWN_DAYS) {
      const result = { symbol, verdict: 'skip', reason: cached.reason, cached_from: cached.date };
      verdicts[symbol] = result.verdict;
      details.push(result);
      cachedSkips++;
      console.log(`${symbol}: skip (cached rejection from ${cached.date}, reason=${cached.reason})`);
      continue;
    }

    try {
      const result = await analyzeSymbol(symbol);
      verdicts[symbol] = result.verdict;
      details.push(result);
      const dateInfo = result.entry_date ? ` entry=${result.entry_date}` : '';
      const reasonInfo = result.reason ? ` reason=${result.reason}` : '';
      console.log(`${symbol}: ${result.verdict}${dateInfo}${reasonInfo}`);

      if (result.verdict === 'skip' && !TRANSIENT_SKIP_REASONS.has(result.reason)) {
        rejectionCache[symbol] = { date: today, reason: result.reason };
      } else if (result.verdict !== 'skip') {
        delete rejectionCache[symbol];
      }
    } catch (e) {
      verdicts[symbol] = 'skip';
      details.push({ symbol, verdict: 'skip', reason: 'error', error: String(e.message || e) });
      console.log(`${symbol}: skip (error: ${e.message || e})`);
    }
  }

  const liveChecked = details.filter((d) => !d.cached_from).length;
  const errored = details.filter((d) => d.reason === 'error').length;
  if (errored >= 5 && errored / Math.max(1, liveChecked) > MAX_ERROR_RATIO) {
    console.error(`ABORT: ${errored} of ${liveChecked} live reads errored (>${MAX_ERROR_RATIO * 100}%). Nothing written; fix TradingView (signed in? chart visible?) and re-run.`);
    process.exit(3);
  }
  fs.writeFileSync(outputPath, JSON.stringify(verdicts, null, 2));
  const detailsPath = outputPath.replace(/\.json$/, '_details.json');
  fs.writeFileSync(detailsPath, JSON.stringify(details, null, 2));
  fs.writeFileSync(cachePath, JSON.stringify(rejectionCache, null, 2));

  const counts = details.reduce((acc, d) => {
    acc[d.verdict] = (acc[d.verdict] || 0) + 1;
    return acc;
  }, {});
  console.log(`\nDone. ${JSON.stringify(counts)} (${cachedSkips} skipped via cached rejection, no live check)`);
  console.log(`Verdicts: ${outputPath}`);
  console.log(`Details: ${detailsPath}`);
  console.log(`Rejection cache: ${cachePath}`);
}

main()
  .then(() => process.exit(0))
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });
