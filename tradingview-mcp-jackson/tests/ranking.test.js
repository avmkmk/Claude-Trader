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
