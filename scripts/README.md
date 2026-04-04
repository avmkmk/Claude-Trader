# SimpleTrader Scripts

This directory contains the core backtesting script for the ATH Reclaim strategy.

## Core Script

### `backtest_portfolio_chronological.py` - Portfolio-Level Chronological Backtest ⭐

**Purpose**: Run realistic portfolio-level backtest with capital constraints and monthly SIP injections.

**Key Features**:
- Processes trades chronologically day-by-day across ALL stocks
- Shared capital pool with monthly injections
- Skips trades when capital is insufficient
- Position sizing based on portfolio value (10%)
- Realistic capital management simulation

**Usage**:
```bash
python scripts/backtest_portfolio_chronological.py \
  --symbols-file data/nifty_500_valid.csv \
  --start-date 2016-01-01 \
  --end-date 2024-12-31
```

**Arguments**:
- `--symbols-file`: Path to CSV file with stock symbols (required)
- `--start-date`: Backtest start date YYYY-MM-DD (required)
- `--end-date`: Backtest end date YYYY-MM-DD (required)
- `--starting-cash`: Initial capital in Rs (default: 70000)
- `--monthly-injection`: Monthly SIP amount in Rs (default: 70000)
- `--position-pct`: Position size as % of portfolio (default: 0.10)
- `--data-dir`: Custom historical data directory (optional)

**Examples**:

```bash
# Nifty 500 backtest (2016-2024)
python scripts/backtest_portfolio_chronological.py \
  --symbols-file data/nifty_500_valid.csv \
  --start-date 2016-01-01 \
  --end-date 2024-12-31 \
  --starting-cash 70000 \
  --monthly-injection 70000

# Small-cap backtest
python scripts/backtest_portfolio_chronological.py \
  --symbols-file data/nifty_smallcap_250_valid.csv \
  --start-date 2016-01-01 \
  --end-date 2024-12-31

# Full dataset backtest (lower capital)
python scripts/backtest_portfolio_chronological.py \
  --symbols-file data/eod2_full_valid_2023_2025.csv \
  --start-date 2023-01-01 \
  --end-date 2025-12-31 \
  --starting-cash 50000 \
  --monthly-injection 50000

# Historical stress test (2008 crash)
python scripts/backtest_portfolio_chronological.py \
  --symbols-file data/nifty_500_valid.csv \
  --start-date 2008-01-01 \
  --end-date 2015-12-31
```

**Output**:
- Creates `results/portfolio_backtest.csv` with all trades
- Logs detailed execution to console
- Shows performance metrics (CAGR, win rate, P&L)

## Backtest Results

| Universe | Period | CAGR | Win Rate | Trades | Verdict |
|----------|--------|------|----------|--------|---------|
| Nifty 500 | 2016-2024 | 18.5% | 43.1% | 211 | ⭐⭐⭐⭐⭐ BEST |
| Nifty 500 | 2008-2015 | 11.9% | 36.9% | 160 | ⭐⭐⭐⭐⭐ Proven |
| Smallcap 250 | 2016-2024 | 14.4% | 47.5% | 139 | ⭐⭐⭐⭐ Good |
| Full 2,020 | 2023-2025 | 4.8% | 31.5% | 216 | ❌ Poor |

**Recommendation**: Deploy on **Nifty 500** universe for best risk-adjusted returns.

## Strategy Overview

**ATH Reclaim Strategy** (3-Phase State Machine):
1. **Phase 1: ATH Tracking** - Track all-time highs
2. **Phase 2: Below EMA 200** - Wait for correction below 200-day EMA
3. **Phase 3: ATH Reclaim Entry** - Buy when price reclaims ATH (with gap filter)

**Exit**: Close below EMA 200

**Position Sizing**: 10% of portfolio value per trade

**Capital Management**:
- Starting: Rs 70,000
- Monthly SIP: Rs 70,000
- Max concurrent positions: ~10 (based on capital)

## Archived Scripts

Utility and analysis scripts have been moved to `../SimpleTrader_Archive/` for cleanup:
- **Validation scripts**: `validate_*.py`, `create_nifty500_list.py`, etc.
- **Analysis scripts**: `analyze_portfolio_backtest.py`, `debug_reliance_signal.py`
- **FNO data scripts**: `scripts/fno_data/`
- **Old backtest scripts**: `backtest_ath_reclaim_v1.py` (per-stock approach)

See `../SimpleTrader_Archive/README.md` for details.

## Stock Universe Files

Located in `data/` directory:
- `nifty_500_valid.csv` - 478 validated Nifty 500 stocks ⭐ **RECOMMENDED**
- `nifty_smallcap_250_valid.csv` - 236 validated small-cap stocks
- `eod2_full_valid_2023_2025.csv` - 2,020 stocks (full dataset, not recommended)

## Historical Data Path

Default: `../historical_Indian_equity_data/daily/eod2/{SYMBOL}.csv`

Override with `--data-dir` if your data is elsewhere.

## Notes

- Always use chronological portfolio-level backtest for realistic results
- Per-stock independent backtests overestimate returns (no capital constraints)
- Win rate of 40-47% is normal for trend-following strategies
- CAGR of 18.5% is achieved through position sizing and capital compounding
- Strategy proven across 17 years including 2008 financial crisis

## Support

For questions or issues, refer to:
- Main documentation: `docs/`
- Strategy guide: `docs/strategy_development/`
- CLAUDE.md: Project overview and setup
