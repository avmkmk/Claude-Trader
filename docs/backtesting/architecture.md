# Backtesting Architecture

> Part of [Backtesting System](README.md)

## Overview

SimpleTrader's backtesting system is built on Backtrader, a Python framework for testing trading strategies on historical data. The architecture separates data management, strategy logic, execution engine, and performance analysis into independent components.

---

## Component Design

### BacktestRunner

Orchestrator class that manages the entire backtest lifecycle.

**Initialization:**
```python
runner = BacktestRunner(initial_cash=100000)
# Sets up:
# - Cerebro engine (Backtrader's main orchestrator)
# - Broker with initial cash
# - Commission (default 0.1%)
```

**Core Methods:**

**`load_data(csv_path, symbol_name)`**
- Loads CSV with OHLCV data into Backtrader PandasData format
- CSV must have datetime index and columns: open, high, low, close, volume
- Supports multiple data feeds for multi-symbol strategies

```python
runner.load_data('data/RELIANCE_90days.csv', 'RELIANCE')
# Converts pandas DataFrame to bt.feeds.PandasData
```

**`add_strategy(strategy_class, **params)`**
- Adds strategy class with configurable parameters
- Parameters override strategy's default `params` tuple
- Multiple strategies can be added for comparison

```python
runner.add_strategy(SMACrossoverStrategy, fast_period=10, slow_period=30)
```

**`add_analyzers()`**
- Attaches performance analyzers to Cerebro
- Standard analyzers: SharpeRatio, DrawDown, Returns, TradeAnalyzer
- Results accessible after `run()` completes

**`run()`**
- Executes backtest by iterating through all bars
- Calls strategy's `next()` method for each bar
- Returns strategy instance with analyzer results

```python
result = runner.run()
# Prints: Starting/Ending Portfolio Value
# Returns: First strategy instance
```

**`get_metrics(result)`**
- Extracts metrics from analyzer results
- Returns dictionary with Sharpe, drawdown, returns, trade stats
- Handles missing data gracefully (returns None for unavailable metrics)

```python
metrics = runner.get_metrics(result)
# Returns: {'sharpe_ratio': 1.25, 'returns': {...}, 'drawdown': {...}, 'trades': {...}}
```

**`plot()`**
- Displays backtest chart with equity curve, indicators, trades
- Requires matplotlib configuration
- Optional - use for visual inspection only

---

## Data Flow

```
CSV File (OHLCV)
    ↓
pandas DataFrame (index=datetime, columns=[open,high,low,close,volume])
    ↓
bt.feeds.PandasData (Backtrader data feed)
    ↓
Cerebro Engine (orchestrator)
    ↓
Strategy.__init__() - Initialize indicators (called once)
    ↓
For each bar in data:
    Strategy.next() - Trading logic (called each bar)
        ↓
    Buy/Sell orders → Broker → Execution
        ↓
    Analyzers track metrics
    ↓
Backtest complete → Analyzers return results
    ↓
get_metrics() extracts performance data
```

---

## Strategy Integration

Strategies inherit from `bt.Strategy` and integrate via three key methods:

**1. `params` tuple** - Configurable parameters
```python
params = (
    ('period', 20),
    ('threshold', 30),
)
```

**2. `__init__()` - Indicator initialization**
```python
def __init__(self):
    self.sma = bt.indicators.SMA(self.data.close, period=self.params.period)
    # Called once at backtest start
```

**3. `next()` - Trading logic**
```python
def next(self):
    if not self.position:
        if self.sma[0] > threshold:
            self.buy()
    # Called for each bar in data
```

---

## Analyzer Configuration

Analyzers calculate performance metrics during backtest execution.

**Standard Analyzers:**
- **SharpeRatio:** Risk-adjusted return (`cerebro.addanalyzer(bt.analyzers.SharpeRatio)`)
- **DrawDown:** Peak-to-trough decline (returns max drawdown %)
- **Returns:** Portfolio returns (total, average)
- **TradeAnalyzer:** Trade statistics (won/lost, total closed)

Access via: `strategy_result.analyzers.sharpe.get_analysis()`

---

## Broker Configuration

```python
cerebro.broker.setcash(100000)  # Initial capital
cerebro.broker.setcommission(commission=0.001)  # 0.1% per trade

# Position sizing (in strategy):
self.buy(size=100)  # Fixed size
# Or: Risk-based
position_size = account_risk / stop_loss_distance
self.buy(size=position_size)
```

---

## Related Documentation

**System:**
- [Backtesting Overview](README.md) - System introduction
- [Creating Strategies](creating_strategies.md) - Implementation guide

**Strategies:**
- [Strategy Templates](../../strategies/README.md) - Ready-to-use templates
- [Strategy Development](../strategy_development/README.md) - Complete workflow

---

**Navigation:**
[← README](README.md) | [Creating Strategies →](creating_strategies.md) | [CLAUDE.md](../../CLAUDE.md)
