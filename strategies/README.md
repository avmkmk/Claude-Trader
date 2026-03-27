# Trading Strategies

This directory contains trading strategy implementations for SimpleTrader's backtesting system.

## Quick Start

### Using a Template

**Step 1: Copy template**
```bash
cp templates/mean_reversion_template.py my_mean_reversion.py
```

**Step 2: Customize parameters**
```python
# Edit params tuple at top of class
params = (
    ('rsi_period', 14),
    ('rsi_oversold', 25),  # Changed from 30
    # ... other parameters
)
```

**Step 3: Test**
```python
python my_mean_reversion.py
# Or use dashboard: streamlit run dashboard/streamlit_app.py
```

## Available Templates

### 1. Mean Reversion (`templates/mean_reversion_template.py`)

**Strategy:** Buy oversold, sell at mean
- **Indicators:** RSI, Bollinger Bands, Volume
- **Best for:** Ranging, choppy markets
- **Timeframe:** 15-min to 1-hour
- **Win rate target:** 55-65%
- **Risk:Reward:** 1:1.5 to 1:2

**Key Parameters:**
- `rsi_oversold`: RSI level to enter (default: 30)
- `rsi_exit`: RSI level to exit (default: 50)
- `bb_period`: Bollinger Bands period (default: 20)
- `max_hold_bars`: Maximum hold time (default: 60)

**When to use:** Market is range-bound, price oscillating between support/resistance

---

### 2. Momentum (`templates/momentum_template.py`)

**Strategy:** Trade with the trend using MACD
- **Indicators:** MACD, RSI, Volume, ATR
- **Best for:** Trending markets (up or down)
- **Timeframe:** 5-min to 30-min
- **Win rate target:** 50-60%
- **Risk:Reward:** 1:2 to 1:3

**Key Parameters:**
- `macd_fast`: MACD fast period (default: 12)
- `macd_slow`: MACD slow period (default: 26)
- `rsi_min/max`: Healthy RSI range (default: 40-70)
- `atr_stop_mult`: Stop loss ATR multiplier (default: 1.5)
- `atr_target_mult`: Target ATR multiplier (default: 2.5)

**When to use:** Market is trending, price making higher highs/lows consistently

---

### 3. Breakout (`templates/breakout_template.py`)

**Strategy:** Trade breakouts of consolidation ranges
- **Indicators:** Channel highs/lows, ATR, Volume, Bollinger Bands
- **Best for:** Volatile markets after consolidation
- **Timeframe:** 15-min to 1-hour
- **Win rate target:** 45-55%
- **Risk:Reward:** 1:2 to 1:3

**Key Parameters:**
- `channel_period`: Lookback for resistance (default: 20)
- `volume_threshold`: Volume confirmation multiplier (default: 1.2)
- `atr_threshold`: ATR expansion threshold (default: 1.2)
- `atr_stop_mult`: Stop below breakout (default: 1.0)

**When to use:** Price consolidating in narrow range, volatility contracting

---

## Creating a Custom Strategy

### Step 1: Understand Backtrader Structure

Every strategy must:
- Inherit from `bt.Strategy`
- Define `params` tuple with configurable parameters
- Implement `__init__()` to initialize indicators
- Implement `next()` with trading logic

### Step 2: Choose Your Template

Pick the template closest to your strategy idea:
- **Mean reversion** - For counter-trend strategies
- **Momentum** - For trend-following strategies
- **Breakout** - For volatility-based strategies

### Step 3: Add Your Indicators

Backtrader has 100+ built-in indicators. Common ones:

```python
# Moving averages
self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=20)
self.ema = bt.indicators.ExponentialMovingAverage(self.data.close, period=20)

# Oscillators
self.rsi = bt.indicators.RSI(self.data.close, period=14)
self.stoch = bt.indicators.Stochastic(self.data)

# Trend
self.macd = bt.indicators.MACD(self.data.close)
self.adx = bt.indicators.ADX(self.data)

# Volatility
self.atr = bt.indicators.ATR(self.data, period=14)
self.bb = bt.indicators.BollingerBands(self.data.close, period=20)

# Volume
self.obv = bt.indicators.OnBalanceVolume(self.data)
```

### Step 4: Implement Trading Logic

```python
def next(self):
    # === TIME FILTERS ===
    # Indian market hours: 9:30 AM - 3:30 PM IST
    current_time = self.data.datetime.time()
    if current_time < datetime.time(9, 45) or current_time > datetime.time(14, 30):
        return

    # === ENTRY LOGIC ===
    if not self.position:  # Not in market
        # Your entry conditions
        if self.indicator1 > threshold and self.indicator2 < threshold:
            self.buy()
            self.entry_price = self.data.close[0]

    # === EXIT LOGIC ===
    else:  # In market
        # Your exit conditions
        if self.data.close[0] >= self.entry_price * 1.02:  # 2% profit
            self.sell()
        elif self.data.close[0] <= self.entry_price * 0.98:  # 2% loss
            self.sell()
```

### Step 5: Test Your Strategy

**Command line:**
```python
python my_strategy.py
```

**Via dashboard:**
```bash
streamlit run dashboard/streamlit_app.py
# Navigate to Backtesting page
# Select your data file and run
```

---

## Parameter Tuning Guidelines

### General Rules

1. **Start with defaults**: Template defaults are sensible starting points
2. **Change one at a time**: Isolate which parameter changes improve performance
3. **Avoid overfitting**: If small changes drastically change results, strategy is fragile
4. **Test on multiple symbols**: Strategy should work on 5+ different stocks

### Parameter Ranges

**Indicator Periods:**
- Fast periods: 5-20 (more sensitive, more signals)
- Slow periods: 20-200 (less sensitive, fewer signals)
- Volume periods: 10-30 (smoothing)

**Risk Management:**
- ATR stop multiplier: 1.0-2.5 (wider = fewer stops, more risk)
- ATR target multiplier: 1.5-5.0 (wider = fewer wins, bigger wins)
- Max hold bars: 30-120 (timeframe dependent)

**Thresholds:**
- RSI oversold: 20-35 (lower = stronger signal, fewer trades)
- RSI overbought: 65-80 (higher = stronger signal, fewer trades)
- Volume multiplier: 0.5-2.0 (higher = more confirmation needed)

### Optimization Workflow

```python
# Test parameter sensitivity
results = []

for rsi_level in range(20, 41, 5):  # 20, 25, 30, 35, 40
    for bb_std in [1.5, 2.0, 2.5]:
        runner = BacktestRunner()
        runner.load_data('data/SYMBOL_90days.csv', 'SYMBOL')
        runner.add_strategy(MyStrategy,
                          rsi_oversold=rsi_level,
                          bb_std=bb_std)
        runner.add_analyzers()

        result = runner.run()
        metrics = runner.get_metrics(result)

        results.append({
            'rsi_oversold': rsi_level,
            'bb_std': bb_std,
            'sharpe': metrics['sharpe_ratio'],
            'return': metrics['returns']['total_return']
        })

# Find best parameters
import pandas as pd
df = pd.DataFrame(results)
best = df.sort_values('sharpe', ascending=False).head(5)
print(best)
```

---

## Common Mistakes

### 1. Overfitting
**Problem:** Strategy works perfectly on one stock/period but fails everywhere else
**Solution:** Test on multiple symbols and time periods before optimizing

### 2. Look-Ahead Bias
**Problem:** Using future information in indicators (e.g., `self.data.close[1]` when you mean `[0]`)
**Solution:** Always use `[0]` for current bar, `[-1]` for previous

### 3. No Position Sizing
**Problem:** Same position size regardless of volatility
**Solution:** Scale position size based on ATR (higher volatility = smaller size)

### 4. Ignoring Commissions
**Problem:** Backtest shows profit but live trading loses due to spreads/commissions
**Solution:** Set realistic commission in BacktestRunner (0.1% or higher)

### 5. No Time Filters
**Problem:** Trading during illiquid hours (pre-market, last 5 minutes)
**Solution:** Add time filters to avoid 9:15-9:30 AM and after 3:25 PM

### 6. Too Many Indicators
**Problem:** Strategy requires 10+ indicators to align
**Solution:** Keep it simple - 2-3 indicators with clear entry/exit rules

---

## Testing Checklist

Before deploying a strategy:

- [ ] Tested on 1+ year of data
- [ ] Tested on 5+ different stocks
- [ ] Sharpe ratio > 1.0
- [ ] Max drawdown < 15%
- [ ] Win rate meets strategy minimum
- [ ] Profit factor > 1.5
- [ ] Time filters implemented (9:45 AM - 2:30 PM)
- [ ] Volume filters implemented (min 5 lakh daily)
- [ ] Stop loss enforced (no exceptions)
- [ ] Max hold time defined
- [ ] Parameter sensitivity tested (±10% doesn't flip results)

---

## Resources

- **Strategy Development Workflow**: `STRATEGY_DEVELOPMENT.md`
- **Indian Market Guide**: `INDIAN_MARKET_GUIDE.md`
- **Backtrader Documentation**: https://www.backtrader.com/docu/
- **Indicators Reference**: https://www.backtrader.com/docu/indautoref/

## Support

For questions:
1. Check `STRATEGY_DEVELOPMENT.md` for workflow guidance
2. Review template code comments for implementation details
3. Use dashboard for interactive testing
4. Refer to `CLAUDE.md` for system architecture
