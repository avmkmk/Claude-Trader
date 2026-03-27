# Risk Management Rules

> Part of [Indian Market Trading Guide](README.md)

## Overview

Comprehensive risk management rules for Indian market algorithmic trading, including position sizing, stop loss rules, account limits, and sector correlation considerations.

---

---

## Risk Management Rules for Indian Markets

### Position Sizing

**Per-Trade Risk:**
```
Max Risk Per Trade = 2-3% of account

Position Size = Account Risk / (Entry Price - Stop Loss)

Example:
- Account: Rs 1,00,000
- Risk: 2% = Rs 2,000
- Entry: Rs 1000
- Stop: Rs 980 (2% below entry, 1.5x ATR)
- Position Size: Rs 2,000 / Rs 20 = 100 shares
- Total Investment: 100 × Rs 1000 = Rs 1,00,000 (100% account)

If this exceeds limits, reduce position size to max 10% of account.
```

**Account-Level Limits:**
```
Max per stock: 10% of account
Max in single sector: 25% of account
Max total positions: 10-20 concurrent
```

### Stop Loss Rules

**ATR-Based:**
```
Stop Loss = Entry Price - (ATR × Multiplier)

Conservative: 2.0-2.5x ATR (large-cap)
Moderate: 1.5-2.0x ATR (standard)
Aggressive: 1.0-1.5x ATR (mid-cap, higher risk)
```

**Hard Rules:**
- **Never move stop loss away** from entry (only towards)
- **Never risk >3% per trade** (no exceptions)
- **Always honor stops** (no "wait and see")

### Daily Limits

```
Daily Loss Limit = -5% of account
- If hit: Stop all trading for the day
- Do not attempt to "recover" losses same day

Daily Profit Target = +3-5% of account (optional)
- If hit: Consider closing early (avoid giving back gains)

Max Trades Per Day = 10-20
- If hit: Likely over-trading, stop
```

### Weekly/Monthly Review

**Every Week:**
- Review all closed trades
- Calculate win rate, average P&L
- Identify pattern in losses (time of day, stock type)
- Adjust strategy if win rate drops below minimum

**Every Month:**
- Calculate monthly return, Sharpe ratio
- Max drawdown vs backtest max
- If live results significantly worse than backtest:
  - Check for slippage issues
  - Verify market regime hasn't changed
  - Consider pausing strategy

---

## Margin & Leverage

### Cash Market (Equity Delivery)

**Margin:** 100% (no leverage)
- Buy Rs 1 lakh worth of stock = need Rs 1 lakh cash
- **Best for:** Position trades (multi-day holds)

### Intraday Trading (MIS - Margin Intraday Square-off)

**Margin:** 20-50% (2-5x leverage)
- Example: Rs 20,000 margin can buy Rs 1 lakh worth
- **Must square off by 3:20 PM** (broker auto-squares off)
- **Risk:** If stock moves against you, losses magnified

**Recommendation for Algo:**
- Avoid high leverage (max 2x)
- Ensure stop losses tight enough to not exceed margin
- Always square off before 3:15 PM (don't rely on broker)

### Futures & Options

**Futures Margin:** 10-40% (2.5-10x leverage)
**Options Buying:** 100% premium (no leverage, limited risk)
**Options Selling:** High margin + unlimited risk

**Recommendation:**
- Start with cash/MIS only
- Avoid F&O until profitable in cash
- Options selling requires advanced risk management

---

## Sector Rotation & Correlations

### Sector Behavior

**Cyclical Sectors** (economy-dependent):
- Auto, Metals, Real Estate, Banking
- High volatility, trending behavior
- **Best strategies:** Momentum, trend following

**Defensive Sectors** (stable):
- Pharma, FMCG, IT Services
- Lower volatility, range-bound
- **Best strategies:** Mean reversion

**Financial Sector:**
- Banks, NBFCs, Insurance
- Highly correlated with Nifty (0.8+ correlation)
- Sensitive to interest rates (RBI policy)

### Index Correlation

**High Correlation (>0.7):**
- Large-cap stocks to Nifty 50
- Banking stocks to Bank Nifty
- IT stocks to Nifty IT

**Implication:** When index moves ±2%, these stocks move ±1.5-2.5%

**Strategy:**
- If Nifty trending up strongly, look for momentum longs in high-beta large-caps
- If Nifty choppy, prefer low-correlation stocks for mean reversion


---

**Navigation:**
[← Volatility](volatility.md) | [README](README.md) | [Events →](events.md)

**Related:** [Parameter Design](../strategy_development/parameter_design.md)
