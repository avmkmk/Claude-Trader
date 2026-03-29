# Development Workflow - Quick Start

Quick reference for developing trading strategies in SimpleTrader.

## Setup

**Activate environment:**
```bash
source venv/Scripts/activate  # Git Bash
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Configuration:**
Create `.env` with broker credentials:
```
NUBRA_CLIENT_ID="your_client_id"
NUBRA_MPIN="your_mpin"
UPSTOX_ACCESS_TOKEN="your_token"
```

---

## Strategy Development (Condensed)

### 1. Research & Selection
- Identify market regime (trending, ranging, volatile)
- Select strategy type (momentum, mean reversion, breakout)
- Choose appropriate indicators and timeframe

[Full guide →](../strategy_development/research_selection.md)

### 2. Parameter Design
- Define entry/exit conditions (primary signal + confirmation)
- Set position sizing (risk per trade, ATR-based)
- Add filters (time: 9:45 AM-2:30 PM, volume: >5 lakh daily)

[Full guide →](../strategy_development/parameter_design.md)

### 3. Implementation
Create strategy class:
```python
import backtrader as bt
import datetime

class MyStrategy(bt.Strategy):
    params = (('period', 20),)

    def __init__(self):
        self.indicator = bt.indicators.SMA(self.data.close, period=self.params.period)

    def next(self):
        # Time filter (Indian market hours)
        current_time = self.data.datetime.time()
        if current_time < datetime.time(9, 45) or current_time > datetime.time(14, 30):
            return

        # Entry/exit logic
        if not self.position:
            if self.data.close[0] > self.indicator[0]:
                self.buy()
        else:
            if self.data.close[0] < self.indicator[0]:
                self.sell()
```

[Full guide →](../strategy_development/implementation.md)

### 4. Backtesting
Run backtest:
```python
from backtesting.backtest_runner import BacktestRunner

runner = BacktestRunner(initial_cash=100000)
runner.load_data('data/GRAPHITE_90days.csv', 'GRAPHITE')
runner.add_strategy(MyStrategy, period=20)
runner.add_analyzers()

result = runner.run()
metrics = runner.get_metrics(result)
```

Key metrics:
- **Sharpe ratio**: >1.0 (good)
- **Max drawdown**: <15% (target)
- **Win rate**: >50% (depends on strategy type)

[Full guide →](../strategy_development/backtesting.md)

### 5. Optimization
- Parameter sensitivity testing (vary one parameter at a time)
- Walk-forward validation (train on period 1, test on period 2)
- Stress test on volatile periods (Budget day, Elections)

[Full guide →](../strategy_development/optimization.md)

### 6. Validation Checklist
- [ ] Positive total return on backtest
- [ ] Sharpe ratio > 1.0
- [ ] Max drawdown < 15%
- [ ] Win rate > 50% (momentum/mean reversion) or >45% (breakout)
- [ ] Profit factor > 1.5
- [ ] Tested on 1+ year Indian market data
- [ ] Time filters: 9:45 AM - 2:30 PM IST
- [ ] Volume filter: Min 5 lakh daily

[Full criteria →](../strategy_development/validation.md)

---

## Common Commands

**Launch web application (recommended):**
```bash
# Terminal 1 - Start FastAPI backend
cd simple-trader-api
python -m app.main

# Terminal 2 - Start React frontend
cd simple-trader-web
npm run dev

# Access at http://localhost:5173
```

**Quick backtest (command line):**
```bash
python -c "from backtesting.backtest_runner import BacktestRunner; from strategies.sma_crossover import SMACrossoverStrategy; r = BacktestRunner(); r.load_data('data/GRAPHITE_3months.csv', 'GRAPHITE'); r.add_strategy(SMACrossoverStrategy); r.add_analyzers(); result = r.run(); print(r.get_metrics(result))"
```

**Scrape single equity:**
```bash
python -c "from apis.nubra_api import NubraAPIHandler; from backtesting.data_scraper import EquityDataScraper; n = NubraAPIHandler(); n.initialize_sdk(); s = EquityDataScraper(n); df = s.scrape_equity('RELIANCE'); s.save_to_csv(df, 'RELIANCE', 90)"
```

[Full commands →](common_commands.md)

---

## Templates

Use strategy templates for quick start:
- **Mean Reversion**: `strategies/templates/mean_reversion_template.py`
- **Momentum**: `strategies/templates/momentum_template.py`
- **Breakout**: `strategies/templates/breakout_template.py`

[Template usage →](../../strategies/README.md)

---

**Navigation:**
[CLAUDE.md](../../CLAUDE.md) | [Strategy Development](../strategy_development/README.md) | [Indian Markets](../indian_markets/README.md)
