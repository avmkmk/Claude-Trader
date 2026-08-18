import { chart, data } from './src/core/index.js';
import fs from 'fs';

const symbols = [
  'SOUTHBANK', 'SUVEN', 'PIDILITIND', 'GOKULAGRO', 'YATHARTH', 'RUBYMILLS', 'ALIVUS',
  'BHARATSE', 'AUROPHARMA', 'RISHABH', 'DEEPINDS', 'RATEGAIN', 'SMLMAH', 'TALBROAUTO',
  'AUBANK', 'LUMAXTECH', 'MACPOWER',
];

async function analyzeSymbol(symbol) {
  await chart.setSymbol({ symbol: `NSE:${symbol}` });
  const labelsResult = await data.getPineLabels({ study_filter: 'ATH Reclaim', max_labels: 50 });
  const study = (labelsResult.studies || []).find((s) => s.name === 'ATH Reclaim - Final Verified');
  const labels = study ? study.labels : [];

  const trades = [];
  let openReclaim = null;
  for (const l of labels) {
    if (/^RECLAIM/.test(l.text)) {
      openReclaim = l;
    } else if (l.text === 'EXIT' && openReclaim) {
      const pnlPct = ((l.price - openReclaim.price) / openReclaim.price) * 100;
      trades.push({ entry: openReclaim.price, exit: l.price, pnl_pct: Math.round(pnlPct * 100) / 100 });
      openReclaim = null;
    }
  }
  const wins = trades.filter((t) => t.pnl_pct > 0).length;
  const losses = trades.filter((t) => t.pnl_pct <= 0).length;
  const avgPnl = trades.length ? Math.round((trades.reduce((s, t) => s + t.pnl_pct, 0) / trades.length) * 100) / 100 : null;
  const stillHolding = openReclaim !== null;

  return {
    symbol, total_labels: labels.length, closed_trades: trades.length,
    wins, losses, win_rate_pct: trades.length ? Math.round((wins / trades.length) * 10000) / 100 : null,
    avg_pnl_pct: avgPnl, still_holding: stillHolding, trades,
  };
}

async function main() {
  const results = [];
  for (const symbol of symbols) {
    try {
      const r = await analyzeSymbol(symbol);
      results.push(r);
      console.log(`${symbol}: ${r.closed_trades} closed trades, ${r.wins}W/${r.losses}L (${r.win_rate_pct}% win rate), avg pnl ${r.avg_pnl_pct}%`);
    } catch (e) {
      results.push({ symbol, error: String(e.message || e) });
      console.log(`${symbol}: ERROR ${e.message || e}`);
    }
  }
  fs.writeFileSync('strategy_history_results.json', JSON.stringify(results, null, 2));
  console.log('\nWrote strategy_history_results.json');
}

main().then(() => process.exit(0)).catch((e) => { console.error(e); process.exit(1); });
