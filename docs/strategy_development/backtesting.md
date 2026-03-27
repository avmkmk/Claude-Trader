# Backtesting

> Part of [Strategy Development Workflow](README.md) - Phase 4 of 6


### Step 4.1: Prepare Historical Data

**Data Requirements:**
- Minimum 1 year for Indian markets (captures different regimes)
- Prefer 2-3 years for robust validation
- Include volatile periods (budget days, elections, market crashes)

**Scrape Data:**
```python
from apis.nubra_api import NubraAPIHandler
from backtesting.data_scraper import EquityDataScraper

nubra = NubraAPIHandler()
nubra.initialize_sdk()

scraper = EquityDataScraper(nubra)

# Scrape multiple symbols for testing
symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK']
scraper.scrape_batch(symbols)
```

### Step 4.2: Run Initial Backtest

```python
from backtesting.backtest_runner import BacktestRunner
from strategies.my_strategy import MyStrategy

runner = BacktestRunner(initial_cash=100000)
runner.load_data('data/RELIANCE_90days.csv', 'RELIANCE')
runner.add_strategy(MyStrategy, param1=10, param2=30)
runner.add_analyzers()

result = runner.run()
metrics = runner.get_metrics(result)
```

### Step 4.3: Analyze Metrics

**Minimum Acceptable Metrics:**

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| **Total Return** | >10% | >5% | <5% |
| **Sharpe Ratio** | >1.5 | >1.0 | <1.0 |
| **Max Drawdown** | <10% | <15% | >15% |
| **Win Rate** | >55% (mean rev) | >50% | <50% |
| **Profit Factor** | >2.0 | >1.5 | <1.5 |

**Analysis Questions:**
- Is total return positive? (If no, strategy likely won't work live)
- Is Sharpe ratio >1.0? (Risk-adjusted return acceptable?)
- Is max drawdown <15%? (Can you stomach the losses?)
- Does win rate meet strategy minimums? (45-55% depending on type)
- Are there long losing streaks? (Check trade log)

### Step 4.4: Review Trade Log

Check individual trades for patterns:

```python
# Print detailed trade log
for trade in result._trades:
    print(f"{trade.dtopen} to {trade.dtclose}: P&L={trade.pnl:.2f}")
```

**Look for:**
- Are losses much larger than wins? (Adjust risk/reward)
- Are there many consecutive losses? (Add filters)
- Do trades cluster at certain times? (Adjust time filters)

---

---

**Navigation:**
[← Implementation](implementation.md) | [README](README.md) | [Optimization →](optimization.md)
