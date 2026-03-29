# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

SimpleTrader is a Python-based algorithmic trading bot for Indian equity markets (NSE/BSE). Supports Nubra and Upstox broker APIs with a complete backtesting framework based on Backtrader. Implements systematic strategy development workflow with templates for momentum, mean reversion, and breakout strategies.

## Quick Links

- **Getting Started**: [Development Workflow](docs/quick_start/development_workflow.md)
- **Strategy Development**: [Strategy Development Guide](docs/strategy_development/README.md)
- **Indian Markets**: [Market Essentials](docs/quick_start/market_essentials.md) | [Full Guide](docs/indian_markets/README.md)
- **Backtesting**: [System Architecture](docs/backtesting/README.md)
- **Commands**: [Common Commands](docs/quick_start/common_commands.md)

## Project Structure

```
SimpleTrader/
├── main.py                    # Entry point
├── apis/                      # Broker API handlers (Nubra, Upstox)
├── strategies/                # Strategy templates and implementations
├── backtesting/              # Data scraper, backtest runner
├── scripts/                   # Utility scripts (scrapers, validators)
├── simple-trader-api/         # FastAPI backend
├── simple-trader-web/         # React frontend
├── docs/                     # Documentation (see Quick Links)
│   ├── quick_start/          # 5-minute orientation guides
│   ├── strategy_development/ # Complete workflow (6 phases)
│   ├── indian_markets/       # Market-specific rules and patterns
│   └── backtesting/          # System architecture and guides
└── historical_Indian_equity_data/  # Historical data (in parent folder)
```

## Core Concepts

**Broker APIs**: Nubra (production) and Upstox for market data and order placement. NubraAPIHandler wraps SDK with methods for historical data, WebSocket streaming, and 3-month equity fetching.

**Backtesting System**: Backtrader-based framework for testing strategies on historical data.
- Strategies inherit from `bt.Strategy` with `params`, `__init__()`, and `next()` methods
- BacktestRunner orchestrates execution: load_data → add_strategy → add_analyzers → run → get_metrics
- Performance metrics: Sharpe ratio (>1.0 target), max drawdown (<15% target), win rate, P&L
- [Full details →](docs/backtesting/README.md)

**Strategy Development**: Systematic 6-phase workflow ensures positive PnL in backtests.
- Research & Selection → Parameter Design → Implementation → Backtesting → Optimization → Validation
- Templates available: mean reversion (RSI + BB), momentum (MACD + volume), breakout (ATR + volume)
- [Full workflow →](docs/strategy_development/README.md)

**Indian Market Specifics**: Critical rules for NSE/BSE algorithmic trading.
- Trading hours: 9:30 AM - 3:30 PM IST (algo window: 9:45 AM - 2:30 PM)
- Min liquidity: 5 lakh daily volume, prefer Nifty 50 stocks
- Circuit breakers: ±5/10/20% halts trading (avoid stocks near ±4%)
- Risk limits: Max 3% per trade, Max 10% per position, -5% daily loss = stop
- [Full guide →](docs/indian_markets/README.md)

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

# Start React frontend (in another terminal)
cd simple-trader-web
npm install
npm run dev
# App runs at http://localhost:5173
```

## Configuration

Create `.env` file with broker credentials:
```
NUBRA_CLIENT_ID="your_client_id"
NUBRA_MPIN="your_mpin"
UPSTOX_ACCESS_TOKEN="your_token"
```

## Key Dependencies

- **backtrader**: Strategy backtesting framework with 100+ indicators
- **fastapi**: REST API backend
- **react**: Frontend web application
- **nubra-sdk**: Nubra broker API (NSE/BSE market data)
- **upstox-python-sdk**: Upstox broker API
- **pandas**: Data manipulation and time series analysis

## Historical Data

Historical data is stored in the parent folder:
```
../historical_Indian_equity_data/
├── daily/eod2/                 # 3318 stocks (daily OHLCV, split-adjusted)
├── intraday/corrected/         # 55 validated stocks (with corporate actions corrected)
├── intraday/raw/              # ~556 stocks (use with caution)
├── intraday/fno/              # Futures & Options data
│   ├── options/NIFTY/5min/    # 5,786 contracts (2022-2024, 706 MB)
│   ├── options/NIFTY/15min/   # 5,563 contracts (250 MB)
│   ├── index/BANKNIFTY/5min/  # 171K candles (2015-2024, 98.9% validated)
│   ├── index/NIFTY/5min/      # 41K candles (2021-2023, 99.8% validated)
│   ├── futures/               # Recent futures from Nubra (3 months)
│   └── daily/                 # NSE bhavcopy 2021-Jul 2024
└── validation_reports/        # Data validation reports
```

**For Backtesting:**
- Daily: `../historical_Indian_equity_data/daily/eod2/{SYMBOL}.csv`
- Intraday: `../historical_Indian_equity_data/intraday/corrected/{SYMBOL}/{TF}/{TF}.csv`
- F&O Options: `../historical_Indian_equity_data/intraday/fno/options/NIFTY/{TF}/{CONTRACT}_{TF}.csv`
- F&O Index: `../historical_Indian_equity_data/intraday/fno/index/{SYMBOL}/{TF}/{SYMBOL}_{TF}.csv`
- F&O Daily: `../historical_Indian_equity_data/intraday/fno/daily/{SYMBOL}/{YEAR}/fo_bhav_{YEAR}.csv`

## Documentation Index

**Quick Start (5-minute orientation):**
- [Development Workflow](docs/quick_start/development_workflow.md) - Condensed workflow reference
- [Market Essentials](docs/quick_start/market_essentials.md) - Critical Indian market rules
- [Common Commands](docs/quick_start/common_commands.md) - Quick command reference

**Strategy Development:**
- [Complete Workflow](docs/strategy_development/README.md) - 6-phase systematic process
- [Phase 1: Research & Selection](docs/strategy_development/research_selection.md)
- [Phase 2: Parameter Design](docs/strategy_development/parameter_design.md)
- [Phase 3: Implementation](docs/strategy_development/implementation.md)
- [Phase 4: Backtesting](docs/strategy_development/backtesting.md)
- [Phase 5: Optimization](docs/strategy_development/optimization.md)
- [Phase 6: Validation](docs/strategy_development/validation.md)

**Indian Markets:**
- [Indian Market Trading Guide](docs/indian_markets/README.md) - Complete reference
- [Trading Hours](docs/indian_markets/trading_hours.md) - Sessions and best windows
- [Liquidity Requirements](docs/indian_markets/liquidity.md) - Volume and position limits
- [Circuit Breakers](docs/indian_markets/circuit_breakers.md) - Price bands and halts
- [Volatility Patterns](docs/indian_markets/volatility.md) - Intraday/weekly/seasonal
- [Risk Management](docs/indian_markets/risk_management.md) - Position sizing and stops
- [High-Impact Events](docs/indian_markets/events.md) - RBI, Budget, Elections

**Backtesting System:**
- [System Architecture](docs/backtesting/README.md) - Components and data flow
- [Architecture Details](docs/backtesting/architecture.md) - BacktestRunner API
- [Creating Strategies](docs/backtesting/creating_strategies.md) - Implementation patterns

**Strategy Templates:**
- [Template Usage](strategies/README.md) - How to use and customize templates
- Mean Reversion: `strategies/templates/mean_reversion_template.py`
- Momentum: `strategies/templates/momentum_template.py`
- Breakout: `strategies/templates/breakout_template.py`
