# Creating Strategies

> Part of [Backtesting System](README.md)

## Overview

Strategies in SimpleTrader inherit from `backtrader.Strategy` and define trading logic via indicators and entry/exit rules. This guide covers the core structure, common patterns, and best practices.

---

## Strategy Class Structure

### Required Components

Every strategy must implement three elements:

**1. params tuple** - Configurable parameters
```python
params = (
    ('fast_period', 10),
    ('slow_period', 30),
)
```

**2. __init__() method** - Indicator initialization
```python
def __init__(self):
    self.fast_sma = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
    self.slow_sma = bt.indicators.SMA(self.data.close, period=self.params.slow_period)
    self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)
```

**3. next() method** - Trading logic (called each bar)
```python
def next(self):
    if not self.position:  # Not in market
        if self.crossover > 0:  # Fast crosses above slow
            self.buy()
    else:  # In market
        if self.crossover < 0:  # Fast crosses below slow
            self.sell()
```

---

## Key Concepts

**Data Access:**
- Current bar: `self.data.close[0]`, `self.rsi[0]`
- Previous bars: `self.data.close[-1]` (negative indices only)
- **Never use positive indices** (look-ahead bias)

**Position Management:**
- Check: `if not self.position:` (not in market)
- Close: `self.sell()` (exit long position)

**Indicators:** SMA, EMA, RSI, MACD, ATR, Bollinger Bands - see [Strategy Templates](../../strategies/README.md) for usage examples

---

## Entry/Exit Patterns

**Threshold Entry:**
```python
def next(self):
    if not self.position and self.rsi[0] < 30:  # Oversold
        self.buy()
    elif self.position and self.rsi[0] > 70:  # Overbought
        self.sell()
```

**Multiple Conditions with ATR Stop:**
```python
def next(self):
    if not self.position:
        if (self.rsi[0] < 30 and
            self.data.close[0] < self.bb.lines.bot[0] and
            self.data.volume[0] > self.volume_sma[0]):
            self.buy()
            self.entry_price = self.data.close[0]
            self.stop_loss = self.entry_price - (1.5 * self.atr[0])
    else:
        if self.data.close[0] <= self.stop_loss:
            self.sell()  # Stop loss hit
```

**More patterns:** See [Strategy Templates](../../strategies/README.md) for crossover detection, breakout entries, trailing stops

---

## Indian Market Filters

### Time Filters

```python
import datetime

def next(self):
    # Only trade during liquid hours (9:45 AM - 2:30 PM IST)
    current_time = self.data.datetime.time()
    if current_time < datetime.time(9, 45) or current_time > datetime.time(14, 30):
        return

    # Trading logic here
```

### Volume Filters

```python
def __init__(self):
    self.volume_sma = bt.indicators.SMA(self.data.volume, period=20)

def next(self):
    # Skip if volume below average (illiquid)
    if self.data.volume[0] < 0.8 * self.volume_sma[0]:
        return
```

---

## Common Mistakes

**1. Look-Ahead Bias:** Never use positive indices (`self.data.close[1]` is future data). Always use `[0]` for current, `[-1]` for previous.

**2. No Position Sizing:** Calculate risk-based size instead of using all cash:
```python
account_value = self.broker.getvalue()
risk_amount = account_value * 0.02  # 2% risk
position_size = int(risk_amount / (1.5 * self.atr[0]))
self.buy(size=position_size)
```

**3. Missing Time Filters:** Add checks for 9:45 AM - 2:30 PM trading window (see Indian Market Filters above)

**4. Too Many Indicators:** Keep it simple - 2-3 indicators with clear logic. Requiring 8+ indicators to align creates rare, unreliable signals.

**5. No Commissions:** Set realistic commission in BacktestRunner (0.1%+) to account for spreads

**6. Overfitting:** Test on 5+ symbols and multiple time periods before optimizing parameters

---

## Testing Workflow

**Step 1: Create strategy file**
```bash
cp strategies/templates/mean_reversion_template.py strategies/my_strategy.py
```

**Step 2: Customize parameters**
```python
params = (
    ('rsi_oversold', 25),  # Changed from 30
    ('rsi_exit', 55),
)
```

**Step 3: Run backtest**
```python
from backtesting.backtest_runner import BacktestRunner
from strategies.my_strategy import MyStrategy

runner = BacktestRunner()
runner.load_data('data/RELIANCE_90days.csv', 'RELIANCE')
runner.add_strategy(MyStrategy)
runner.add_analyzers()

result = runner.run()
metrics = runner.get_metrics(result)
print(f"Sharpe: {metrics['sharpe_ratio']}")
```

**Step 4: Iterate**
- Check Sharpe > 1.0, drawdown < 15%
- Test on multiple symbols
- Adjust parameters based on results

---

## Related Documentation

**Templates:**
- [Strategy Templates](../../strategies/README.md) - Mean reversion, momentum, breakout

**Development:**
- [Strategy Development](../strategy_development/README.md) - 6-phase workflow
- [Implementation Phase](../strategy_development/implementation.md) - Code structure

**System:**
- [Backtesting Overview](README.md) - Architecture
- [Architecture Details](architecture.md) - Component design

---

**Navigation:**
[← Architecture](architecture.md) | [README](README.md) | [CLAUDE.md](../../CLAUDE.md)
