# Common Commands

Quick command reference for SimpleTrader development.

## Web Application (Recommended Interface)

```bash
# Start FastAPI backend
cd simple-trader-api
python -m app.main

# Start React frontend
cd simple-trader-web
npm run dev
```

Access at: http://localhost:5173

**Features:**
- Authentication (MPIN-based)
- Portfolio holdings and orders
- Backtesting with charts
- Watchlist management
- AI Chat (Gemini-powered)
- Real news (Marketaux + Alpha Vantage)

---

## Testing Strategies

### Via Web Application
1. Launch the app (see above)
2. Navigate to "Strategies" page
3. Select symbol and strategy
4. Click "Run Backtest"
5. View metrics and charts

### Command Line (Quick Test)
```bash
python -c "from backtesting.backtest_runner import BacktestRunner; \
from strategies.sma_crossover import SMACrossoverStrategy; \
r = BacktestRunner(); \
r.load_data('data/GRAPHITE_3months.csv', 'GRAPHITE'); \
r.add_strategy(SMACrossoverStrategy); \
r.add_analyzers(); \
result = r.run(); \
metrics = r.get_metrics(result); \
print(f\"Sharpe: {metrics['sharpe_ratio']}, Return: {metrics['returns']['total_return']:.2%}\")"
```

### Test Custom Strategy
```bash
python my_strategy.py  # If strategy includes __main__ block
```

---

## Data Scraping

### Single Equity
```bash
python -c "from apis.nubra_api import NubraAPIHandler; \
from backtesting.data_scraper import EquityDataScraper; \
n = NubraAPIHandler(); \
n.initialize_sdk(); \
s = EquityDataScraper(n); \
df = s.scrape_equity('RELIANCE'); \
s.save_to_csv(df, 'RELIANCE', 90)"
```

Saves to: `data/RELIANCE_90days.csv`

---

## Authentication Testing

```bash
python -c "from apis.nubra_api import NubraAPIHandler; \
n = NubraAPIHandler(); \
print('Auth:', n.initialize_sdk())"
```

Expected output: `Auth: True`

If fails: Check `.env` file has correct `NUBRA_CLIENT_ID` and `NUBRA_MPIN`

---

## Development

### Activate Virtual Environment
```bash
source venv/Scripts/activate  # Git Bash
# Or: venv\Scripts\activate.bat  # Windows CMD
# Or: venv\Scripts\Activate.ps1  # PowerShell
```

### Install/Update Dependencies
```bash
pip install -r requirements.txt

# API dependencies
cd simple-trader-api
pip install -r requirements.txt
```

### Check Installed Packages
```bash
pip list | grep -E "backtrader|fastapi|nubra|upstox"
```

---

## Troubleshooting

### "Module not found" Error
```bash
# Ensure venv is activated
source venv/Scripts/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Nubra Authentication Fails
```bash
# Check environment variables
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('CLIENT_ID:', os.getenv('NUBRA_CLIENT_ID')[:10] if os.getenv('NUBRA_CLIENT_ID') else 'NOT SET')"
```

Ensure `.env` exists in simple-trader-api/ with:
```
NUBRA_CLIENT_ID="your_client_id"
NUBRA_MPIN="your_mpin"
```

### Port Already in Use
```bash
# Use different port for backend
cd simple-trader-api
python -m app.main --port 8001
```

### Data File Not Found
```bash
# List available data files
ls -lh ../historical_Indian_equity_data/daily/eod2/*.csv | head -20

# Check file path in backtest code
# Ensure relative path from project root
```

---

## Navigation

[CLAUDE.md](../../CLAUDE.md) | [Development Workflow](development_workflow.md) | [Market Essentials](market_essentials.md)
