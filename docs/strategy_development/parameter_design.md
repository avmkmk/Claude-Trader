# Parameter Design

> Part of [Strategy Development Workflow](README.md) - Phase 2 of 6

## Overview

Phase 2 defines specific entry/exit conditions, position sizing formulas, and risk management filters. Clear parameter definitions ensure consistent strategy execution and proper risk control.

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

## Next Steps

With parameters defined, proceed to Phase 3 to implement the strategy in code.

---

**Navigation:**
[← Research & Selection](research_selection.md) | [README](README.md) | [Implementation →](implementation.md)

**Related:** [Quick Start](../quick_start/development_workflow.md) | [Risk Management](../indian_markets/risk_management.md)
