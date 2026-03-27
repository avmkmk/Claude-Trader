# Strategy Implementation

> Part of [Strategy Development Workflow](README.md) - Phase 3 of 6

## Overview

Phase 3 translates parameter design into working Python code using Backtrader. Create strategy class, initialize indicators, implement trading logic with proper risk management.

---

## Phase 3: Strategy Implementation

### Step 3.1: Choose Template or Create New

**Option A: Use Template** (Recommended for beginners)
```bash
# Copy template to strategies folder
cp strategies/templates/mean_reversion_template.py strategies/my_strategy.py

# Edit parameters and logic as needed
```

**Option B: Create from Scratch**

Create `strategies/my_strategy.py`:

```python
import backtrader as bt

class MyStrategy(bt.Strategy):
    """
    Brief description of strategy logic
    """

    params = (
        ('param1', default_value1),
        ('param2', default_value2),
    )

    def __init__(self):
        """Initialize indicators"""
        # Add your indicators here
        self.indicator1 = bt.indicators.SomeIndicator(
            self.data.close,
            period=self.params.param1
        )

    def next(self):
        """Trading logic called for each candle"""
        # Entry logic
        if not self.position:  # Not in market
            if self.indicator1 > some_threshold:
                self.buy()

        # Exit logic
        else:  # In market
            if self.indicator1 < some_threshold:
                self.sell()

    def notify_order(self, order):
        """Log order executions"""
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'BUY EXECUTED at {order.executed.price:.2f}')
            elif order.issell():
                print(f'SELL EXECUTED at {order.executed.price:.2f}')

    def notify_trade(self, trade):
        """Log trade P&L"""
        if trade.isclosed:
            print(f'TRADE CLOSED: P&L = {trade.pnl:.2f}')
```

### Step 3.2: Implement Logic

**Common Patterns:**

**Crossover Detection:**
```python
self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

# In next():
if self.crossover > 0:  # Fast crosses above slow
    self.buy()
```

**Threshold Check:**
```python
if self.rsi < 30:  # Oversold
    self.buy()
```

**Multiple Conditions:**
```python
if (self.rsi < 30 and
    self.data.close[0] < self.bb.lines.bot[0] and
    self.data.volume[0] > self.volume_sma[0]):
    self.buy()
```

### Step 3.3: Add Comments

Document your logic clearly:

```python
def next(self):
    # Only trade during liquid hours (9:45 AM - 2:30 PM)
    hour = self.data.datetime.time().hour
    minute = self.data.datetime.time().minute
    if hour < 9 or (hour == 9 and minute < 45) or hour > 14 or (hour == 14 and minute > 30):
        return

    # Entry: RSI oversold + price below lower Bollinger Band
    if not self.position:
        if self.rsi < 30 and self.data.close[0] < self.bb.lines.bot[0]:
            self.buy()
            self.entry_price = self.data.close[0]
            self.stop_loss = self.entry_price - (1.5 * self.atr[0])

    # Exit: Target hit (2:1 R/R) or stop loss
    else:
        target = self.entry_price + (2 * (self.entry_price - self.stop_loss))
        if self.data.close[0] >= target:
            self.sell()  # Take profit
        elif self.data.close[0] <= self.stop_loss:
            self.sell()  # Stop loss
```

---

## Next Steps

With implementation complete, proceed to Phase 4 to backtest on historical data.

---

**Navigation:**
[← Parameter Design](parameter_design.md) | [README](README.md) | [Backtesting →](backtesting.md)

**Related:** [Creating Strategies](../backtesting/creating_strategies.md) | [Templates](../../strategies/README.md)
