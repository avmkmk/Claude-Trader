# Trading Strategy Development Workflow

This document guides you through developing profitable trading strategies for Indian markets using SimpleTrader's backtesting system.

## Overview

**Goal:** Create strategies that show positive PnL when backtested on historical Indian market data.

**Workflow:** Research → Design → Implement → Backtest → Optimize → Validate

**Time Investment:** 2-4 hours for a well-researched strategy

---

## Phase 1: Research & Selection

### Step 1.1: Identify Market Regime

Analyze recent market behavior to determine current regime:

**Trending Market** (clear direction, sustained moves):
- Price makes higher highs and higher lows (uptrend) or lower lows and lower highs (downtrend)
- Moving averages are diverging (short-term MA pulling away from long-term)
- ADX > 25 (strong trend)
- **Best strategies**: Trend following, momentum

**Ranging Market** (sideways, choppy):
- Price oscillates between support and resistance
- Moving averages are flat or converging
- ADX < 20 (weak trend)
- **Best strategies**: Mean reversion, range trading

**Volatile Market** (large swings, breakouts):
- ATR expanding rapidly
- Price making large intraday moves
- News-driven or event-based volatility
- **Best strategies**: Breakout, volatility-based

**How to check:**
```python
# Quick market regime check
from backtesting.backtest_runner import BacktestRunner
import pandas as pd

df = pd.read_csv('data/NIFTY50_90days.csv', index_col=0, parse_dates=True)
df['sma_20'] = df['close'].rolling(20).mean()
df['sma_50'] = df['close'].rolling(50).mean()
df['atr_14'] = df['high'].rolling(14).max() - df['low'].rolling(14).min()

# Trending if SMA20 > SMA50 consistently, ranging if crossing frequently
# Volatile if ATR expanding
print(df[['close', 'sma_20', 'sma_50', 'atr_14']].tail(20))
```

### Step 1.2: Select Strategy Type

Based on market regime, choose strategy type:

| Strategy Type | Market Regime | Win Rate Target | Risk:Reward | Timeframe |
|---------------|---------------|-----------------|-------------|-----------|
| **Mean Reversion** | Ranging, choppy | 55-65% | 1:1.5 to 1:2 | 15-min to 1-hour |
| **Momentum** | Trending up/down | 50-60% | 1:2 to 1:3 | 5-min to 30-min |
| **Breakout** | Volatile, ranging | 45-55% | 1:2 to 1:3 | 15-min to 1-hour |
| **Trend Following** | Strong trending | 45-55% | 1:3 to 1:5 | 1-hour to 4-hour |

### Step 1.3: Choose Indicators

Select 2-3 indicators based on strategy type:

**Mean Reversion:**
- Primary: RSI (14), Bollinger Bands (20, 2)
- Confirmation: Volume, Support/Resistance levels

**Momentum:**
- Primary: MACD (12, 26, 9), Price > Moving Average
- Confirmation: Volume, RSI (40-60 range)

**Breakout:**
- Primary: ATR (14), Bollinger Bands, Price channels
- Confirmation: Volume expansion (>1.2x average)

**Trend Following:**
- Primary: SMA crossovers (20/50/200), ADX (14)
- Confirmation: Price structure (higher highs/lows)

### Step 1.4: Define Timeframe

Choose based on strategy type and trading style:

- **Scalping** (5-15 seconds hold): 1-min charts (high skill, not recommended for algo)
- **Intraday swing** (15 min - 2 hours): 5-min to 15-min charts (best for momentum/breakout)
- **Day trading** (2-6 hours): 15-min to 1-hour charts (best for mean reversion/trend)
- **Swing trading** (1-5 days): 4-hour to daily charts (trend following)

**Recommendation for Indian markets**: 15-min to 1-hour (best signal-to-noise ratio)

---

## Phase 2: Parameter Design

### Step 2.1: Entry Conditions

Define **primary signal + confirmation**:

**Example (Mean Reversion):**
```
Primary Signal:
- RSI < 30 (oversold) OR
- Price < Lower Bollinger Band

Confirmation:
- MACD histogram not negative (no strong downtrend)
- Volume > 0.8x average (adequate liquidity)
- Time: Between 9:45 AM - 2:30 PM IST (liquidity window)

Trend Filter:
- Price > 50-SMA (don't buy in strong downtrend)
```

**Example (Momentum):**
```
Primary Signal:
- MACD line > Signal line AND
- MACD histogram increasing

Confirmation:
- RSI 40-60 (not overbought)
- Volume > 20-period average
- Price > 20-SMA (uptrend confirmed)
```

### Step 2.2: Exit Conditions

Define **profit targets + stop loss + time-based**:

**Profit Targets:**
- Fixed ratio: 1:2 or 1:3 risk/reward
- ATR-based: 1.5-2.5x ATR above entry
- Trailing stop: 1x ATR below highest price (lets winners run)

**Stop Loss:**
- ATR-based: 1.5-2x ATR below entry (most common)
- Support-based: Just below nearest support level
- Percentage-based: 1-2% for large-caps, 2-3% for mid-caps
- **Critical**: Never risk >3% of account per trade

**Time-Based Exits:**
- Max hold time: 60 minutes if no profit, exit with small loss
- End of day: Close all positions by 3:15 PM (avoid overnight risk)

### Step 2.3: Position Sizing

Calculate position size based on risk:

**Formula:**
```
Position Size = Account Risk (Rs) / (Stop Loss Distance in Rs)

Example:
- Account: Rs 1,00,000
- Risk per trade: 2% = Rs 2,000
- Stop loss: 1.5x ATR = Rs 100
- Position size: Rs 2,000 / Rs 100 = 20 shares
```

**Rules:**
- Never risk >3% per trade
- Never have >10% of account in single position
- Reduce position size in volatile stocks (higher ATR)

### Step 2.4: Risk Management Filters

Add filters to avoid bad setups:

**Time Filters:**
- Avoid 9:15-9:30 AM (pre-market, low liquidity)
- Avoid last 5 minutes (3:25-3:30 PM) - gap/reversal risk
- Avoid high-impact event days (RBI announcements, budget, elections)

**Volatility Filters:**
- Skip if ATR > 2x average ATR (excessive volatility)
- Skip if circuit breaker triggered in last 30 minutes

**Volume Filters:**
- Skip if volume < 0.5x average volume (illiquid)
- Minimum daily volume: 5 lakh shares for algo trading

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

## Phase 4: Backtesting

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

## Phase 5: Optimization

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

## Phase 6: Validation Checklist

Before deploying a strategy, verify:

### Performance Criteria
- [ ] **Positive total return** on backtest (>5% annually)
- [ ] **Sharpe ratio > 1.0** (preferably >1.5)
- [ ] **Max drawdown < 15%** (preferably <10%)
- [ ] **Win rate meets strategy minimums**:
  - Mean reversion: >55%
  - Momentum: >50%
  - Breakout: >45%
  - Trend following: >45%
- [ ] **Profit factor > 1.5** (preferably >2.0)

### Robustness Criteria
- [ ] **Tested on 1+ year of Indian market data**
- [ ] **Parameter sensitivity acceptable** (±10% param change doesn't flip results)
- [ ] **Walk-forward validation passed** (testing period results similar to training)
- [ ] **Stress tested on volatile periods** (drawdown still acceptable)
- [ ] **Multi-symbol validation** (works on 5+ different stocks)

### Risk Management Criteria
- [ ] **Max risk per trade ≤ 3%** of account
- [ ] **Max position size ≤ 10%** of account
- [ ] **Daily loss limit defined** (e.g., -5% stops trading for day)
- [ ] **Time filters implemented** (avoid illiquid windows, high-impact events)
- [ ] **Volume filters implemented** (min 5 lakh daily volume)

### Documentation Criteria
- [ ] **Strategy logic documented** in code comments
- [ ] **Entry/exit rules clearly defined**
- [ ] **Parameter rationale explained** (why these values?)
- [ ] **Backtest results saved** (metrics + trade log)
- [ ] **Known limitations documented** (what market conditions does it fail in?)

---

## Post-Validation: Deployment Considerations

**Before going live:**

1. **Paper trading**: Run strategy on live data without real money for 1-2 weeks
2. **Small position sizes**: Start with 25-50% of intended position size
3. **Monitor closely**: Watch first 10-20 trades for unexpected behavior
4. **Gradual scaling**: Increase position size only after consistent results

**Red flags to watch:**
- Slippage much worse than backtest (adjust commission in backtest)
- More losses in live than backtest (market regime may have changed)
- Orders not filling (liquidity issues, adjust position size)

**When to stop a strategy:**
- Drawdown exceeds backtest max by 50% (e.g., if backtest max was 10%, stop at 15%)
- Win rate drops below strategy minimum for 30+ trades
- Market regime changed (trending strategy in ranging market won't work)

---

## Indian Market-Specific Guidelines

See **INDIAN_MARKET_GUIDE.md** for comprehensive details.

**Quick Checklist:**
- [ ] Trading only during 9:30 AM - 3:30 PM IST
- [ ] Avoiding pre-market (9:15-9:30 AM)
- [ ] Position limits respect liquidity (max 10% of daily volume)
- [ ] Circuit breaker rules considered (5%/10%/20% limits)
- [ ] High-impact events calendared (RBI, budget, elections)
- [ ] Volatility patterns understood (weekly, seasonal)

---

## Resources

- **Strategy Templates**: `strategies/templates/`
- **Indian Market Guide**: `INDIAN_MARKET_GUIDE.md`
- **Backtrader Documentation**: https://www.backtrader.com/docu/
- **Dashboard**: `streamlit run dashboard/streamlit_app.py`

## Support

For questions or issues:
1. Check CLAUDE.md for architecture overview
2. Review strategy templates for implementation examples
3. Use dashboard for interactive backtesting
4. Consult Backtrader docs for advanced indicators
