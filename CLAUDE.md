# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

SimpleTrader is a production-ready algorithmic trading platform for Indian equity markets (NSE/BSE). Features React frontend, FastAPI backend, and supports Nubra and Upstox broker APIs.

## Project Structure

```
SimpleTrader/
├── main.py                    # CLI entry point
├── apis/                      # Broker API handlers (Nubra, Upstox)
├── strategies/                # Trading strategy implementations
│   ├── ath_reclaim_daily_v1.py       # ATH Reclaim strategy
│   ├── sma_crossover.py              # SMA crossover
│   ├── rsi_mean_reversion_india.py   # RSI mean reversion
│   └── ema_crossover.py              # EMA crossover
├── backtesting/              # Backtesting engine
│   ├── backtest_runner.py   # Backtrader orchestration
│   └── capital_manager.py   # Portfolio capital management
├── simple-trader-api/        # FastAPI backend
│   ├── app/
│   │   ├── main.py         # API entry point
│   │   ├── routers/        # API endpoints
│   │   └── services/       # AI and news services
│   └── data/               # SQLite database
└── simple-trader-web/       # React frontend
    ├── src/
    │   ├── api/           # API client
    │   ├── pages/         # Page components
    │   └── components/    # Reusable components
    └── package.json
```

## External Resources (Parent Folder)

All documentation, data, and archives are consolidated in a single master folder:

```
../Professional Journey/Personal Software Projects/
├── SimpleTrader/              # This repo (production code)
└── SimpleTraderExternal/      # Master external resources folder
    ├── data/                  # All historical market data
    │   ├── daily/
    │   │   └── eod2/         # 3,318 stocks (daily OHLCV)
    │   ├── intraday/
    │   │   ├── corrected/    # Validated intraday data
    │   │   ├── raw/          # Raw intraday data
    │   │   └── fno/          # F&O options, futures, index
    │   ├── stock_lists/      # Stock universe definitions
    │   └── validation_reports/
    ├── docs/                  # All documentation
    │   ├── backtesting/
    │   ├── indian_markets/
    │   ├── quick_start/
    │   ├── strategy_development/
    │   └── optimization_results/
    ├── backtest_results/      # All backtest results
    │   ├── ath_ema200_reclaim_codex/
    │   ├── batch_backtests/
    │   ├── research/
    │   └── vwap_experiments/
    └── archive/               # Archived code and utilities
        ├── scripts/
        ├── data/
        ├── results/
        └── tests/
```

## Core Concepts

**Broker APIs**: Nubra (production) and Upstox for market data and order placement.

**Backtesting System**: Backtrader-based framework.
- Strategies inherit from `bt.Strategy` with `params`, `__init__()`, and `next()` methods
- BacktestRunner orchestrates execution
- Performance metrics: Sharpe ratio, max drawdown, win rate, P&L

**Strategy Development**: Systematic workflow ensures positive PnL in backtests.
- See `../SimpleTrader_Documentation/strategy_development/README.md`

**Indian Market Specifics**: Critical rules for NSE/BSE.
- Trading hours: 9:30 AM - 3:30 PM IST
- Min liquidity: 5 lakh daily volume
- Circuit breakers: ±5/10/20%
- Risk limits: 3% per trade, 10% per position, -5% daily loss = stop
- See `../SimpleTrader_Documentation/indian_markets/README.md`

## Development Setup

```bash
# Activate virtual environment
source venv/Scripts/activate  # Git Bash

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend
cd simple-trader-api
pip install -r requirements.txt
python -m app.main
# API runs at http://localhost:8000

# Start React frontend (new terminal)
cd simple-trader-web
npm install
npm run dev
# App runs at http://localhost:5173
```

## Configuration

Create `simple-trader-api/.env`:
```
NUBRA_CLIENT_ID="your_client_id"
NUBRA_MPIN="your_mpin"
GEMINI_API_KEY="your_gemini_key"
MARKETAUX_API_KEY="your_marketaux_key"
ALPHA_VANTAGE_API_KEY="your_alphavantage_key"
```

## Key Dependencies

- **backtrader**: Strategy backtesting framework
- **fastapi**: REST API backend
- **react**: Frontend web application
- **nubra-sdk**: Nubra broker API
- **upstox-python-sdk**: Upstox broker API
- **pandas**: Data manipulation
- **google-generativeai**: Gemini AI integration

## Historical Data

All historical data is organized in `../SimpleTraderExternal/data/`:

**Daily Data** (3,318 stocks):
- Path: `../SimpleTraderExternal/data/daily/eod2/{SYMBOL}.csv`
- Format: CSV with Date, Open, High, Low, Close, Volume
- Split-adjusted with corporate actions applied

**Intraday Data** (validated stocks):
- Path: `../SimpleTraderExternal/data/intraday/corrected/{SYMBOL}/{TF}/{TF}.csv`
- Timeframes: 1min, 5min, 15min, 1hr
- 55 validated stocks with verified corporate actions

**F&O Data**:
- Options: `../SimpleTraderExternal/data/intraday/fno/options/{INDEX}/{TF}/{CONTRACT}_{TF}.csv`
  - 5,786 NIFTY contracts (5min, 2022-2024)
  - 5,563 contracts (15min)
- Index: `../SimpleTraderExternal/data/intraday/fno/index/{INDEX}/{TF}/{INDEX}_{TF}.csv`
  - NIFTY: 41K candles (99.8% validated)
  - BANKNIFTY: 171K candles (98.9% validated)
- Futures: `../SimpleTraderExternal/data/intraday/fno/futures/`
- Daily: `../SimpleTraderExternal/data/intraday/fno/daily/`

**Stock Lists**:
- `../SimpleTraderExternal/data/stock_lists/nifty_200_constituents.csv`
- `../SimpleTraderExternal/data/stock_lists/nifty_sector_mapping.csv`
- `../SimpleTraderExternal/data/stock_lists/nifty_test_set_20.csv`

## Available Strategies

**Production Strategies** (used by API):
- `ath_reclaim_daily_v1.py` - ATH Reclaim with EMA 200 (18.5% CAGR proven)
- `sma_crossover.py` - SMA crossover strategy
- `rsi_mean_reversion_india.py` - RSI mean reversion
- `ema_crossover.py` - EMA crossover

## Documentation Index

**Quick Start:**
- [Development Workflow](../SimpleTraderExternal/docs/quick_start/development_workflow.md)
- [Market Essentials](../SimpleTraderExternal/docs/quick_start/market_essentials.md)
- [Common Commands](../SimpleTraderExternal/docs/quick_start/common_commands.md)

**Strategy Development:**
- [Complete Workflow](../SimpleTraderExternal/docs/strategy_development/README.md)
- [Phase 1: Research & Selection](../SimpleTraderExternal/docs/strategy_development/research_selection.md)
- [Phase 2: Parameter Design](../SimpleTraderExternal/docs/strategy_development/parameter_design.md)
- [Phase 3: Implementation](../SimpleTraderExternal/docs/strategy_development/implementation.md)
- [Phase 4: Backtesting](../SimpleTraderExternal/docs/strategy_development/backtesting.md)
- [Phase 5: Optimization](../SimpleTraderExternal/docs/strategy_development/optimization.md)
- [Phase 6: Validation](../SimpleTraderExternal/docs/strategy_development/validation.md)

**Indian Markets:**
- [Complete Guide](../SimpleTraderExternal/docs/indian_markets/README.md)
- [Trading Hours](../SimpleTraderExternal/docs/indian_markets/trading_hours.md)
- [Liquidity Requirements](../SimpleTraderExternal/docs/indian_markets/liquidity.md)
- [Circuit Breakers](../SimpleTraderExternal/docs/indian_markets/circuit_breakers.md)
- [Risk Management](../SimpleTraderExternal/docs/indian_markets/risk_management.md)

**Backtesting:**
- [System Architecture](../SimpleTraderExternal/docs/backtesting/README.md)
- [Architecture Details](../SimpleTraderExternal/docs/backtesting/architecture.md)
- [Creating Strategies](../SimpleTraderExternal/docs/backtesting/creating_strategies.md)

## Important Notes

- Only modify code in this repository
- All external resources are in `../SimpleTraderExternal/` (read-only for data/docs)
- Save new backtest results to `../SimpleTraderExternal/backtest_results/{STRATEGY}/{DATE}/`
- Archive old/experimental code to `../SimpleTraderExternal/archive/`
- See `../SimpleTraderExternal/README.md` for complete data paths and structure
