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
