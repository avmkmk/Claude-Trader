# Backtesting System

Complete framework for testing trading strategies on historical Indian market data.

## Architecture

```
Strategy Templates (strategies/templates/)
        ↓
Strategy Classes (inherit from bt.Strategy)
        ↓
BacktestRunner (orchestrator)
        ↓
Backtrader Engine (data feeds, broker, analyzers)
        ↓
Performance Metrics (Sharpe, Drawdown, Win Rate, P&L)
```

---

## Components

### Strategy Framework

Strategies inherit from `backtrader.Strategy` with three key methods:

**1. params** - Configurable parameters
```python
params = (
    ('period', 20),
    ('threshold', 30),
)
```

**2. __init__()** - Initialize indicators
```python
def __init__(self):
    self.sma = bt.indicators.SMA(self.data.close, period=self.params.period)
    self.rsi = bt.indicators.RSI(self.data.close, period=14)
```

**3. next()** - Trading logic
```python
def next(self):
    if not self.position:
        if self.rsi[0] < self.params.threshold:
            self.buy()
    else:
        if self.rsi[0] > 70:
            self.sell()
```

[Creating Strategies Guide →](creating_strategies.md)

### Backtest Runner

`BacktestRunner` class orchestrates backtest execution:

**Methods:**
- `load_data(filepath, symbol)` - Load historical CSV data
- `add_strategy(StrategyClass, **params)` - Add strategy with parameters
- `add_analyzers()` - Add performance analyzers (Sharpe, Drawdown, etc.)
- `run()` - Execute backtest
- `get_metrics(result)` - Extract performance metrics
- `plot()` - Display equity curve and indicators

**Example:**
```python
from backtesting.backtest_runner import BacktestRunner
from strategies.sma_crossover import SMACrossoverStrategy

runner = BacktestRunner(initial_cash=100000)
runner.load_data('data/GRAPHITE_90days.csv', 'GRAPHITE')
runner.add_strategy(SMACrossoverStrategy, fast_period=10, slow_period=30)
runner.add_analyzers()

result = runner.run()
metrics = runner.get_metrics(result)
```

[Architecture Details →](architecture.md)

### Data Scraper

`EquityDataScraper` fetches historical data via Nubra API:

**Features:**
- Batch scraping with rate limiting (60 requests/minute)
- Saves to `data/{SYMBOL}_{period_days}days.csv`
- Filters NSE equities from security_id_list.csv
- Configurable periods: 90 days, 180 days, 1 year

**Usage:**
```python
from apis.nubra_api import NubraAPIHandler
from backtesting.data_scraper import EquityDataScraper

nubra = NubraAPIHandler()
nubra.initialize_sdk()

scraper = EquityDataScraper(nubra)
df = scraper.scrape_equity('RELIANCE')
scraper.save_to_csv(df, 'RELIANCE', 90)
```

### Dashboard

Streamlit web UI for authentication, data scraping, and backtesting:

**Launch:**
```bash
streamlit run dashboard/streamlit_app.py
# Access at http://localhost:8501
```

**Features:**
- Nubra authentication management
- Batch data scraping (50+ equities)
- Interactive backtesting with charts
- Real-time metrics display

---

## Performance Metrics

| Metric | Description | Target | Interpretation |
|--------|-------------|--------|----------------|
| **Sharpe Ratio** | Risk-adjusted return | >1.0 | <1 poor, 1-2 good, >2 excellent |
| **Max Drawdown** | Largest peak-to-trough decline | <15% | Lower is better, critical for risk management |
| **Total Return** | Overall % gain/loss | Positive | Required for deployment |
| **Win Rate** | % of profitable trades | >45-50% | Depends on strategy type and R:R ratio |
| **Profit Factor** | Gross profit / gross loss | >1.5 | >1.5 sustainable, <1.2 marginal |

---

## Quick Example

```python
from backtesting.backtest_runner import BacktestRunner
from strategies.templates.mean_reversion_template import MeanReversionStrategy

# Create runner
runner = BacktestRunner(initial_cash=100000)

# Load data
runner.load_data('data/RELIANCE_90days.csv', 'RELIANCE')

# Add strategy with custom parameters
runner.add_strategy(
    MeanReversionStrategy,
    rsi_oversold=25,
    rsi_exit=55,
    max_hold_bars=40
)

# Add analyzers
runner.add_analyzers()

# Run backtest
result = runner.run()

# Get metrics
metrics = runner.get_metrics(result)
print(f"Sharpe Ratio: {metrics['sharpe_ratio']}")
print(f"Total Return: {metrics['returns']['total_return']:.2%}")
print(f"Max Drawdown: {metrics['drawdown']['max_drawdown']:.2f}%")
print(f"Win Rate: {metrics['trades']['won_trades']}/{metrics['trades']['total_trades']}")

# Optional: plot
# runner.plot()
```

---

## Related Documentation

**Strategy Development:**
- [Complete Workflow](../strategy_development/README.md) - 6-phase systematic process
- [Implementation Phase](../strategy_development/implementation.md) - Code structure
- [Backtesting Phase](../strategy_development/backtesting.md) - Running backtests

**Guides:**
- [Creating Strategies](creating_strategies.md) - Implementation patterns
- [Architecture Details](architecture.md) - Component design
- [Strategy Templates](../../strategies/README.md) - Template usage

**Quick Start:**
- [Development Workflow](../quick_start/development_workflow.md) - Quick reference
- [Common Commands](../quick_start/common_commands.md) - Command reference

---

**Navigation:**
[CLAUDE.md](../../CLAUDE.md) | [Architecture →](architecture.md) | [Creating Strategies →](creating_strategies.md)
