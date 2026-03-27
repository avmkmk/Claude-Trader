# Optimization

> Part of [Strategy Development Workflow](README.md) - Phase 5 of 6


### Step 5.1: Parameter Sensitivity Testing

Test how sensitive results are to parameter changes:

```python
# Test multiple parameter combinations
results = []

for fast in range(5, 21, 5):  # 5, 10, 15, 20
    for slow in range(20, 51, 10):  # 20, 30, 40, 50
        runner = BacktestRunner(initial_cash=100000)
        runner.load_data('data/RELIANCE_90days.csv', 'RELIANCE')
        runner.add_strategy(MyStrategy, fast_period=fast, slow_period=slow)
        runner.add_analyzers()

        result = runner.run()
        metrics = runner.get_metrics(result)

        results.append({
            'fast': fast,
            'slow': slow,
            'return': metrics['returns']['total_return'],
            'sharpe': metrics['sharpe_ratio']
        })

# Find best parameters
import pandas as pd
df_results = pd.DataFrame(results)
best = df_results.sort_values('sharpe', ascending=False).head(5)
print(best)
```

**Warning:** Don't overfit! If small parameter changes drastically change results, strategy is too fragile.

### Step 5.2: Walk-Forward Validation

Test on different time periods:

**Split data:**
- Training period: 70% of data (e.g., Jan-Sep)
- Testing period: 30% of data (e.g., Oct-Dec)

**Optimize on training, validate on testing:**
```python
# Optimize on training data
# ... find best parameters

# Test on unseen testing data with those parameters
runner = BacktestRunner()
runner.load_data('data/RELIANCE_testing_period.csv', 'RELIANCE')
runner.add_strategy(MyStrategy, fast_period=best_fast, slow_period=best_slow)
result = runner.run()

# If testing results are significantly worse, strategy is overfit
```

### Step 5.3: Stress Testing

Test on volatile periods:

**High-volatility events:**
- Budget day (February 1st each year)
- Election results
- COVID crash (March 2020)
- Market corrections (any -10%+ drop)

**Goal:** Ensure strategy doesn't blow up during extreme events

```python
# Test on volatile period
runner = BacktestRunner()
runner.load_data('data/NIFTY50_march2020.csv', 'NIFTY50')  # COVID crash
result = runner.run()
metrics = runner.get_metrics(result)

# Max drawdown should still be <20% even in crash
print(f"Max Drawdown during crash: {metrics['drawdown']['max_drawdown']:.2f}%")
```

### Step 5.4: Multi-Symbol Validation

Test on different stocks to ensure robustness:

```python
symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'SBIN']
results = []

for symbol in symbols:
    runner = BacktestRunner()
    runner.load_data(f'data/{symbol}_90days.csv', symbol)
    runner.add_strategy(MyStrategy, param1=optimized_param1)
    runner.add_analyzers()

    result = runner.run()
    metrics = runner.get_metrics(result)
    results.append({
        'symbol': symbol,
        'return': metrics['returns']['total_return'],
        'sharpe': metrics['sharpe_ratio']
    })

# Strategy should work on multiple symbols, not just one
```

---

---

**Navigation:**
[← Backtesting](backtesting.md) | [README](README.md) | [Validation →](validation.md)
