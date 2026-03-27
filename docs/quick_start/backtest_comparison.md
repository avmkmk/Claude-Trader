# Backtest Comparison Quick Start

## 5-Minute Guide: Compare Strategies Across Timeframes

### What This Guide Covers

Learn how to compare any trading strategy across multiple timeframes (15m, 1h, 4h, 1d) using the generic strategy comparison CLI.

**Time Required**: 5 minutes
**Prerequisites**: Python environment set up, historical data scraped

---

## Basic Command Structure

```bash
python scripts/compare_strategy.py \
  --symbol <SYMBOL> \
  --strategy-module <PATH_TO_STRATEGY> \
  --strategy-class <CLASS_NAME>
```

**Required Arguments**:
- `--symbol`: Trading symbol (HDFCBANK, RELIANCE, INFY, TCS, etc.)
- `--strategy-module`: Path to Python file (e.g., strategies/sma_crossover.py)
- `--strategy-class`: Strategy class name (e.g., SMACrossoverStrategy)

**Optional Arguments**:
- `--intervals`: Timeframes to test (default: 15m 1h 4h 1d)
- `--strategy-params`: JSON parameters (default: {})
- `--initial-cash`: Starting capital (default: Rs 50 lakhs)
- `--commission`: Trading commission (default: 0.1%)

---

## Real-World Examples

### Example 1: SMA Crossover on HDFCBANK

**Test golden cross/death cross strategy across all timeframes:**

```bash
python scripts/compare_strategy.py \
  --symbol HDFCBANK \
  --strategy-module strategies/sma_crossover.py \
  --strategy-class SMACrossoverStrategy
```

**What it does**:
- Tests SMA crossover (fast=10, slow=30) on HDFCBANK
- Runs backtest on 15m, 1h, 4h, 1d candles
- Displays comparison table with metrics
- Identifies best-performing timeframe

**Expected Output**:
```
================================================================================
STRATEGY COMPARISON: SMACrossoverStrategy for HDFCBANK
================================================================================

[15m] Running backtest... Trades: 42, Return: 8.3%, Sharpe: 0.95
[1h]  Running backtest... Trades: 28, Return: 12.7%, Sharpe: 1.34
[4h]  Running backtest... Trades: 18, Return: 15.2%, Sharpe: 1.58
[1d]  Running backtest... Trades: 12, Return: 10.1%, Sharpe: 1.21

================================================================================
SUMMARY - HDFCBANK (SMACrossoverStrategy)
================================================================================
Interval   Trades   Return    Sharpe    MaxDD     Win%     Status
--------------------------------------------------------------------------------
15m        42       8.3%      0.95      -6.2%     54.8%    OK
1h         28       12.7%     1.34      -5.1%     60.7%    OK
4h         18       15.2%     1.58      -4.3%     66.7%    OK
1d         12       10.1%     1.21      -5.8%     58.3%    OK

BEST INTERVAL: 4h with Sharpe ratio 1.58
```

---

### Example 2: RSI Mean Reversion with Custom Parameters

**Test mean reversion with tighter oversold level:**

```bash
python scripts/compare_strategy.py \
  --symbol RELIANCE \
  --strategy-module strategies/rsi_mean_reversion_india.py \
  --strategy-class RSIMeanReversionIndia \
  --strategy-params '{"rsi_period": 21, "rsi_oversold": 25, "rsi_exit": 55}'
```

**What's different**:
- Custom RSI period (21 instead of default 14)
- Tighter oversold threshold (25 instead of 30)
- Hold longer before exit (55 instead of 50)

---

### Example 3: Single Timeframe Test

**Test only daily timeframe for faster results:**

```bash
python scripts/compare_strategy.py \
  --symbol INFY \
  --strategy-module strategies/sma_crossover.py \
  --strategy-class SMACrossoverStrategy \
  --intervals 1d
```

**Use case**: Quick validation before running full multi-timeframe test.

---

### Example 4: Custom Capital and Commission

**Test with 10 lakh capital and higher commission:**

```bash
python scripts/compare_strategy.py \
  --symbol TCS \
  --strategy-module strategies/sma_crossover.py \
  --strategy-class SMACrossoverStrategy \
  --initial-cash 1000000 \
  --commission 0.0015
```

**Use case**: Match your actual broker capital and commission rates.

---

## Interpreting Results

### Key Metrics

**Sharpe Ratio** (Risk-Adjusted Returns)
- **Target**: > 1.0
- **Meaning**: Return per unit of risk
- **1.5+**: Excellent, 1.0-1.5: Good, <1.0: Poor
- **Use**: Primary metric for strategy comparison

**Total Return** (Percentage Gain/Loss)
- **Target**: Beat FD rate (~7-8% annually)
- **Meaning**: Overall profit/loss percentage
- **Calculation**: (Final Value - Initial Capital) / Initial Capital
- **Use**: Absolute performance measure

**Max Drawdown** (Largest Peak-to-Trough Decline)
- **Target**: < 15% for retail traders
- **Meaning**: Worst consecutive loss streak
- **Impact**: Risk of hitting circuit breakers or margin calls
- **Use**: Risk assessment, position sizing

**Win Rate** (Percentage of Profitable Trades)
- **Target**: 50-60% for mean reversion, 40-50% for trend following
- **Meaning**: % of trades that made profit
- **Calculation**: Won Trades / Total Trades
- **Use**: Strategy style indicator, not primary metric

**Trade Count**
- **Target**: 20+ for 365 days (daily), 50+ for intraday
- **Meaning**: Number of entry/exit cycles
- **Importance**: Statistical significance (more trades = more confidence)

---

### Best Interval Identification

The script automatically identifies the **best interval** by Sharpe ratio:

```
BEST INTERVAL: 4h with Sharpe ratio 1.58
```

**What to do next**:
1. Focus parameter optimization on the best interval
2. Validate on other symbols at same interval
3. Use this interval for paper/live trading

**Why 4h might win**:
- Filters out intraday noise (better than 15m, 1h)
- More trades than daily (better statistical confidence)
- Sweet spot for Indian markets (9:30 AM - 3:30 PM = 6 hours trading)

---

## Common Issues & Solutions

### Problem: `ERROR: Data file not found for interval '15m'`

**Cause**: Missing CSV file for that symbol/timeframe combination

**Solution**:
```bash
# For multi-timeframe data (15m, 1h, 4h, 1d)
python scripts/hdfc_multi_timeframe_scraper.py

# For daily data only
python scripts/batch_data_scraper.py
```

**Verify**:
```bash
ls scripts/data/HDFCBANK_365days_*.csv
# Should show: 15m.csv, 1h.csv, 4h.csv, 1d.csv
```

---

### Problem: `ERROR: Strategy class 'SMACrossover' not found`

**Cause**: Class name doesn't match or wrong file path

**Solution**:
1. Check exact class name (case-sensitive):
   ```bash
   grep "class " strategies/sma_crossover.py
   # Output: class SMACrossoverStrategy(bt.Strategy):
   ```

2. Use correct class name:
   ```bash
   --strategy-class SMACrossoverStrategy  # ✓ Correct
   --strategy-class SMACrossover          # ✗ Wrong
   ```

---

### Problem: `ERROR: Invalid JSON in --strategy-params`

**Cause**: Malformed JSON syntax or quoting issues

**Solution**:
```bash
# ✓ Correct: Single quotes outside, double quotes inside
--strategy-params '{"fast_period": 10, "slow_period": 30}'

# ✗ Wrong: Double quotes outside
--strategy-params "{\"fast_period\": 10}"

# ✗ Wrong: Single quotes inside
--strategy-params "{'fast_period': 10}"
```

---

### Problem: No trades executed (0 trades)

**Cause**: Strategy entry conditions never triggered

**Solutions**:
1. **Try different timeframe**: Daily may have more signals than intraday
   ```bash
   --intervals 1d
   ```

2. **Relax parameters**: Looser thresholds = more trades
   ```bash
   # For RSI: Increase oversold threshold
   --strategy-params '{"rsi_oversold": 35}'  # Was 30

   # For SMA: Tighten crossover periods
   --strategy-params '{"fast_period": 5, "slow_period": 15}'  # Was 10/30
   ```

3. **Check data quality**: Ensure volume and prices are reasonable
   ```bash
   python scripts/validate_data.py
   ```

---

### Problem: Very low Sharpe ratio (<0) or high drawdown (>20%)

**Cause**: Strategy not suited for this symbol/timeframe

**Solutions**:
1. **Try different symbol**: Some strategies work better on certain stocks
2. **Test other timeframes**: Maybe daily works better than intraday
3. **Adjust parameters**: Current settings may not fit market conditions
4. **Consider different strategy**: Not all strategies fit all markets

**Note**: Negative Sharpe = strategy loses money on average. Don't deploy!

---

## Workflow: From Backtest to Deployment

### Step 1: Initial Test (5 minutes)
```bash
python scripts/compare_strategy.py \
  --symbol HDFCBANK \
  --strategy-module strategies/sma_crossover.py \
  --strategy-class SMACrossoverStrategy
```

**Goal**: Find best timeframe, verify strategy logic works

---

### Step 2: Parameter Optimization (30 minutes)
```bash
# Test different SMA periods
--strategy-params '{"fast_period": 5, "slow_period": 15}'
--strategy-params '{"fast_period": 10, "slow_period": 30}'
--strategy-params '{"fast_period": 20, "slow_period": 50}'
```

**Goal**: Find optimal parameters for best timeframe

---

### Step 3: Multi-Symbol Validation (15 minutes)
```bash
# Test same strategy on 3-4 similar stocks
--symbol ICICIBANK
--symbol SBIN
--symbol HDFCBANK
```

**Goal**: Ensure robustness (70%+ symbols should have Sharpe > 0.5)

---

### Step 4: Paper Trading (30 days)
- Deploy strategy on best interval with optimal parameters
- Monitor slippage, execution quality
- Compare live results vs backtest

**Goal**: Validate strategy in real market conditions

---

### Step 5: Live Trading (Start small)
- Begin with 1 lakh capital
- Scale only after 3 months of consistent positive returns
- Always use stop losses and position limits

---

## Next Steps

**If backtest results are positive (Sharpe > 1.0, drawdown < 15%)**:
1. Optimize parameters on best interval
2. Validate on 3-4 other symbols
3. Read [Strategy Development Workflow](../strategy_development/README.md)
4. Start paper trading for 30 days

**If backtest results are negative (Sharpe < 0.5)**:
1. Try different timeframes
2. Test on other symbols
3. Adjust strategy parameters
4. Consider different strategy type (mean reversion vs momentum)

**For more details**:
- Complete workflow: `docs/strategy_development/README.md`
- Parameter optimization: `docs/strategy_development/optimization.md`
- Risk management: `docs/indian_markets/risk_management.md`

---

## Quick Reference Card

```bash
# Basic test
python scripts/compare_strategy.py \
  --symbol HDFCBANK \
  --strategy-module strategies/sma_crossover.py \
  --strategy-class SMACrossoverStrategy

# Custom parameters
--strategy-params '{"fast_period": 10, "slow_period": 30}'

# Single timeframe
--intervals 1d

# View help
python scripts/compare_strategy.py --help

# Available strategies
ls strategies/*.py

# Check data files
ls scripts/data/*.csv
```

**Target Metrics**: Sharpe > 1.0, Drawdown < 15%, Trades > 20, Win Rate > 50%

**Red Flags**: Sharpe < 0, Drawdown > 20%, Zero trades, Win Rate < 40%
