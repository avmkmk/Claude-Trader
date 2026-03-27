# Research & Selection

> Part of [Strategy Development Workflow](README.md) - Phase 1 of 6

## Overview

The first phase identifies the current market regime and selects an appropriate strategy type, indicators, and timeframe. Proper regime identification is critical - using a momentum strategy in a ranging market or mean reversion in a trending market leads to poor performance.

---

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

## Next Steps

Once you've identified the market regime and selected strategy type/indicators/timeframe, proceed to Phase 2 to design specific entry/exit parameters.

---

**Navigation:**
[README](README.md) | [Next: Parameter Design →](parameter_design.md)

**Related:** [Quick Start](../quick_start/development_workflow.md) | [Market Essentials](../quick_start/market_essentials.md)
