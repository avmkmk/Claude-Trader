# SimpleTrader

A Python-based algorithmic trading bot for Indian equity markets (NSE/BSE) with support for Nubra and Upstox broker APIs. Features a complete backtesting framework, strategy templates, and a modern React + FastAPI web interface.

## Features

- **Multi-Broker Support**: Nubra and Upstox API integration for live trading
- **Backtesting Framework**: Complete backtesting system powered by Backtrader
- **Strategy Templates**: Pre-built templates for momentum, mean reversion, and breakout strategies
- **Web Application**: React + FastAPI UI for portfolio management and backtesting
- **AI Assistant**: Gemini-powered AI chat for stock analysis and trading insights
- **Real Market News**: Integration with Marketaux and Alpha Vantage APIs
- **Indian Market Compliance**: Built-in risk management and circuit breaker awareness

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- Nubra or Upstox trading account
- Git Bash (for Windows users)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/SimpleTrader.git
cd SimpleTrader
```

2. **Create and activate virtual environment:**
```bash
python -m venv venv
source venv/Scripts/activate  # Git Bash on Windows
```

3. **Install Python dependencies:**
```bash
pip install -r requirements.txt

# Install API dependencies
cd simple-trader-api
pip install -r requirements.txt
cd ..
```

4. **Install frontend dependencies:**
```bash
cd simple-trader-web
npm install
cd ..
```

5. **Configure environment variables:**

Create `simple-trader-api/.env`:
```env
# Broker credentials
NUBRA_CLIENT_ID=your_client_id
NUBRA_MPIN=your_mpin

# AI features (get free key from https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key

# News features (get free keys from marketaux.com and alphavantage.co)
MARKETAUX_API_KEY=your_marketaux_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
```

6. **Run the application:**

```bash
# Terminal 1 - Start FastAPI backend
cd simple-trader-api
python -m app.main

# Terminal 2 - Start React frontend
cd simple-trader-web
npm run dev
```

Access the web app at http://localhost:5173

## Project Structure

```
SimpleTrader/
├── main.py                      # CLI entry point for live trading
├── apis/                       # Broker API handlers
│   ├── nubra_api.py           # Nubra broker integration
│   └── upstox_api.py         # Upstox broker integration
├── strategies/                 # Trading strategy implementations
│   ├── templates/             # Strategy templates
│   │   ├── mean_reversion_template.py
│   │   ├── momentum_template.py
│   │   └── breakout_template.py
│   ├── sma_crossover.py      # SMA crossover strategy
│   ├── rsi_mean_reversion_india.py
│   └── ...
├── backtesting/               # Backtesting engine
│   ├── backtest_runner.py    # Backtrader orchestration
│   └── data_scraper.py       # Historical data fetching
├── simple-trader-api/        # FastAPI backend
│   ├── app/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── config.py        # Configuration settings
│   │   ├── auth.py          # Session authentication
│   │   ├── routers/         # API endpoints
│   │   │   ├── auth.py      # Login/logout endpoints
│   │   │   ├── holdings.py  # Portfolio holdings
│   │   │   ├── orders.py    # Order history
│   │   │   ├── watchlist.py # Watchlist management
│   │   │   ├── signals.py   # Trading signals
│   │   │   ├── news.py      # Market news
│   │   │   ├── backtest.py  # Backtesting endpoints
│   │   │   └── ai.py        # AI chat endpoints
│   │   └── services/         # Business logic
│   │       ├── ai_client.py  # Gemini AI integration
│   │       └── news_client.py # News API integration
│   └── data/                 # SQLite database
├── simple-trader-web/        # React frontend
│   ├── src/
│   │   ├── api/             # API client
│   │   ├── pages/           # Page components
│   │   ├── components/      # Reusable components
│   │   └── stores/          # State management
│   └── package.json
└── docs/                     # Documentation
    ├── quick_start/          # Getting started guides
    ├── strategy_development/ # Strategy workflow
    ├── indian_markets/       # Market-specific guides
    └── backtesting/          # Backtesting guides
```

## Configuration

### Broker Credentials

| Variable | Description |
|----------|-------------|
| `NUBRA_CLIENT_ID` | Your Nubra broker client ID |
| `NUBRA_MPIN` | Your Nubra MPIN |
| `UPSTOX_ACCESS_TOKEN` | Your Upstox access token |

### AI Features

| Variable | Description | Get Key From |
|----------|-------------|--------------|
| `GEMINI_API_KEY` | Google Gemini API key for AI chat | https://aistudio.google.com/app/apikey |

### News Features

| Variable | Description | Get Key From |
|----------|-------------|--------------|
| `MARKETAUX_API_KEY` | Marketaux API key | marketaux.com |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key | alphavantage.co |

## Usage

### Web Application

The web app provides a graphical interface for:

- **Dashboard**: Portfolio overview with key metrics
- **Holdings**: Current positions with P&L
- **Orders**: Order history
- **Strategies**: Run backtests on historical data
- **Watchlist**: Track stocks of interest
- **Signals**: View generated trading signals
- **News**: Latest market news
- **AI Chat**: Get AI-powered trading insights

### Command Line

Run a quick backtest:
```bash
python -c "
from backtesting.backtest_runner import BacktestRunner
from strategies.sma_crossover import SMACrossoverStrategy

runner = BacktestRunner(initial_cash=100000)
runner.load_data('data/RELIANCE_90days.csv', 'RELIANCE')
runner.add_strategy(SMACrossoverStrategy, fast_period=10, slow_period=30)
runner.add_analyzers()

result = runner.run()
metrics = runner.get_metrics(result)
print(f'Sharpe: {metrics[\"sharpe_ratio\"]}')
print(f'Return: {metrics[\"returns\"][\"total_return\"]:.2%}')
"
```

Scrape historical data:
```bash
python -c "
from apis.nubra_api import NubraAPIHandler
from backtesting.data_scraper import EquityDataScraper

nubra = NubraAPIHandler()
nubra.initialize_sdk()

scraper = EquityDataScraper(nubra)
df = scraper.scrape_equity('RELIANCE')
scraper.save_to_csv(df, 'RELIANCE', 90)
"
```

## Strategy Development

### Using Templates

1. Copy a template:
```bash
cp strategies/templates/mean_reversion_template.py strategies/my_strategy.py
```

2. Customize parameters:
```python
params = (
    ('rsi_period', 14),
    ('rsi_oversold', 25),
)
```

3. Test your strategy:
```bash
python strategies/my_strategy.py
```

### Available Templates

| Template | Best For | Timeframe |
|----------|----------|-----------|
| Mean Reversion | Ranging markets | 15min - 1hr |
| Momentum | Trending markets | 5min - 30min |
| Breakout | Volatile markets | 15min - 1hr |

## Risk Management

Built-in safeguards for Indian markets:

- Max 3% risk per trade
- Max 10% risk per position
- -5% daily loss triggers stop
- Circuit breaker awareness (±5/10/20%)
- Liquidity filters (min 5 lakh daily volume)
- Trading hours: 9:30 AM - 3:30 PM IST

See [Risk Management Guide](docs/indian_markets/risk_management.md) for complete rules.

## API Reference

### Backend Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/login | Authenticate with MPIN |
| POST | /auth/logout | End session |
| GET | /holdings | Get portfolio holdings |
| GET | /orders | Get order history |
| GET | /watchlist | Get watchlist items |
| POST | /watchlist | Add to watchlist |
| DELETE | /watchlist/{symbol} | Remove from watchlist |
| GET | /signals | Get trading signals |
| GET | /news | Get market news |
| POST | /backtest/run | Start backtest |
| GET | /backtest/status/{task_id} | Get backtest status |
| POST | /ai/chat | Chat with AI |
| POST | /ai/analyze-stock | Analyze a stock |
| POST | /ai/suggest-stocks | Get stock suggestions |

## Key Dependencies

### Backend

- **fastapi** - REST API framework
- **uvicorn** - ASGI server
- **google-generativeai** - Gemini AI integration
- **requests** - HTTP client for news APIs
- **python-dotenv** - Environment variable loading

### Frontend

- **react** - UI framework
- **vite** - Build tool
- **typescript** - Type safety
- **@tanstack/react-query** - Data fetching
- **zustand** - State management
- **recharts** - Charting library
- **lucide-react** - Icons

### Trading

- **backtrader** - Strategy backtesting
- **nubra-sdk** - Nubra broker API
- **upstox-python-sdk** - Upstox broker API
- **pandas** - Data manipulation

## Documentation

- [Development Workflow](docs/quick_start/development_workflow.md) - Quick start guide
- [Strategy Development](docs/strategy_development/README.md) - Complete workflow
- [Indian Markets Guide](docs/indian_markets/README.md) - Market rules and patterns
- [Backtesting System](docs/backtesting/README.md) - Architecture and usage

## Disclaimer

This software is provided for educational purposes only. Trading in financial markets carries significant risk. The authors are not responsible for any financial losses incurred using this software. Always:

- Test strategies thoroughly on historical data
- Paper trade before using real capital
- Understand the risks involved
- Follow proper risk management

## License

This project is for educational and personal use only.

## Support

For issues or questions:

1. Check the documentation in `docs/`
2. Review strategy templates for examples
3. Open an issue on GitHub
