# SimpleTrader

Production-ready algorithmic trading platform for Indian equity markets (NSE/BSE) with React frontend and FastAPI backend.

## Features

- **Multi-Broker Support**: Nubra and Upstox API integration
- **Web Application**: Modern React + FastAPI interface
- **AI Assistant**: Gemini-powered chat for stock analysis
- **Real Market News**: Integrated news feeds
- **Backtesting**: Strategy validation on historical data
- **Trading Strategies**: Pre-built strategies ready to use

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- Nubra or Upstox trading account

### Installation

1. **Clone and setup:**
```bash
git clone https://github.com/avmkmk/SmartTrader-NSE-BSE.git
cd SimpleTrader
python -m venv venv
source venv/Scripts/activate  # Git Bash
pip install -r requirements.txt
```

2. **Configure credentials:**

Create `simple-trader-api/.env`:
```env
# Broker
NUBRA_CLIENT_ID=your_client_id
NUBRA_MPIN=your_mpin

# AI (get free key from https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_key

# News (get free keys from marketaux.com and alphavantage.co)
MARKETAUX_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key
```

3. **Start backend:**
```bash
cd simple-trader-api
pip install -r requirements.txt
python -m app.main
# Runs at http://localhost:8000
```

4. **Start frontend (new terminal):**
```bash
cd simple-trader-web
npm install
npm run dev
# Runs at http://localhost:5173
```

## Project Structure

```
SimpleTrader/
├── main.py                 # CLI entry point
├── apis/                   # Broker API handlers
├── backtesting/            # Backtesting engine
├── strategies/             # Trading strategies
├── simple-trader-api/      # FastAPI backend
└── simple-trader-web/      # React frontend
```

## Available Strategies

| Strategy | Type | Description |
|----------|------|-------------|
| ATH Reclaim | Breakout | All-time high breakout with EMA 200 filter |
| SMA Crossover | Trend Following | Simple moving average crossover |
| RSI Mean Reversion | Mean Reversion | RSI-based oversold/overbought |
| EMA Crossover | Trend Following | Exponential moving average crossover |

## API Endpoints

### Authentication
- `POST /auth/login` - Login with MPIN
- `POST /auth/logout` - Logout

### Trading
- `GET /holdings` - Portfolio holdings
- `GET /orders` - Order history
- `GET /watchlist` - Watchlist
- `POST /watchlist` - Add to watchlist
- `GET /signals` - Trading signals

### Analysis
- `POST /backtest/run` - Run backtest
- `GET /backtest/status/{id}` - Backtest status
- `POST /ai/chat` - AI chat
- `POST /ai/analyze-stock` - Stock analysis
- `GET /news` - Market news

## Documentation & Resources

All external resources are consolidated in `../SimpleTraderExternal/`:

**Documentation**: `../SimpleTraderExternal/docs/`
- Quick start guides
- Strategy development workflow (6 phases)
- Indian market trading rules
- Backtesting system architecture

**Historical Data**: `../SimpleTraderExternal/data/`
- **Daily**: 3,318 stocks (split-adjusted, `data/daily/eod2/`)
- **Intraday**: 55 validated stocks (`data/intraday/corrected/`)
- **F&O**: Options, futures, index data (`data/intraday/fno/`)
- **Stock Lists**: Nifty constituents, sector mapping (`data/stock_lists/`)

**Backtest Results**: `../SimpleTraderExternal/backtest_results/`
- ATH Reclaim: 18.5% CAGR (2016-2024, Nifty 500)
- Strategy experiments and research

**Archived Code**: `../SimpleTraderExternal/archive/`
- Validation and analysis scripts
- Old backtest implementations
- Unit tests

See `../SimpleTraderExternal/README.md` for complete structure and data paths.

## Risk Management

Built-in safeguards:
- Max 3% risk per trade
- Max 10% position size
- -5% daily loss triggers stop
- Circuit breaker awareness (±5/10/20%)
- Min liquidity: 5 lakh daily volume
- Trading: 9:30 AM - 3:30 PM IST

## Disclaimer

**For educational purposes only.** Trading carries significant risk. The authors are not responsible for any financial losses. Always:
- Test strategies on historical data
- Paper trade before using real capital
- Understand the risks
- Follow proper risk management

## License

For educational and personal use only.
