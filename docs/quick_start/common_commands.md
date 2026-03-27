# Common Commands

Quick command reference for SimpleTrader development.

## Dashboard (Recommended Interface)

```bash
streamlit run dashboard/streamlit_app.py
```

Access at: http://localhost:8501

**Features:**
- Nubra authentication
- Batch data scraping (50+ equities)
- Interactive backtesting with charts
- Real-time metrics display

---

## Testing Strategies

### Via Dashboard (Preferred)
1. Launch dashboard: `streamlit run dashboard/streamlit_app.py`
2. Navigate to "Backtesting" page
3. Select data file and strategy
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
```python
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

### Batch Scraping (Via Dashboard)
1. Launch dashboard
2. Go to "Data Scraping" page
3. Select equities from dropdown (multi-select)
4. Choose period (90 days, 180 days, 1 year)
5. Click "Start Scraping"
6. Monitor progress bar

**Rate limit:** 60 requests/minute (Nubra API limit)

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
```

### Check Installed Packages
```bash
pip list | grep -E "backtrader|streamlit|nubra|upstox"
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

Ensure `.env` exists in project root with:
```
NUBRA_CLIENT_ID="your_client_id"
NUBRA_MPIN="your_mpin"
```

### Dashboard Port Already in Use
```bash
# Use different port
streamlit run dashboard/streamlit_app.py --server.port 8502
```

### Data File Not Found
```bash
# List available data files
ls -lh data/*.csv

# Check file path in backtest code
# Ensure relative path from project root: data/SYMBOL_XXdays.csv
```

---

**Navigation:**
[CLAUDE.md](../../CLAUDE.md) | [Development Workflow](development_workflow.md) | [Market Essentials](market_essentials.md)
