# Indian Market Essentials

Critical rules for algorithmic trading in Indian equity markets (NSE/BSE).

## Trading Hours

**Main session:** 9:30 AM - 3:30 PM IST

**Avoid:** 9:15-9:30 AM (pre-market - low liquidity, high volatility)

**Best windows:**

| Time | Characteristics | Best For |
|------|-----------------|----------|
| 9:30-11:00 AM | Opening rush, highest volume | Momentum strategies |
| 11:00 AM-2:00 PM | Often choppy, lower volume | Mean reversion |
| 2:00-3:30 PM | Institutional activity | Momentum, exits |

[Full details →](../indian_markets/trading_hours.md)

---

## Liquidity Requirements

**Minimum daily volume:** 5 lakh shares
- Ensures you can enter/exit without excessive slippage

**Position limit:** Max 10% of stock's daily volume
- Prevents market impact

**Prefer Nifty 50 stocks:**
- High liquidity, predictable behavior
- Mid-caps: Wider spreads, adjust position sizing

[Full details →](../indian_markets/liquidity.md)

---

## Circuit Breakers (CRITICAL)

**Stock-level circuits:**
- ±5%, ±10%, ±20% from previous close
- Trading halts for 15 minutes when hit

**Impact:**
- **Can't exit positions during halt** (trapped)
- Gap risk after resumption

**Strategy:**
- Use wider stops (2x ATR instead of 1.5x)
- Smaller positions (max 10% account per stock)
- Avoid stocks near ±4% move

**Detection:**
```python
def check_circuit_risk(current_price, day_open):
    pct_move = ((current_price - day_open) / day_open) * 100
    if abs(pct_move) > 4.0:
        return "HIGH_RISK"  # Avoid new entries
    return "NORMAL"
```

[Full details →](../indian_markets/circuit_breakers.md)

---

## Risk Management Rules

**Per-trade risk:** Max 3% of account
```python
position_size = account_risk / (entry_price - stop_loss)
```

**Per-position limit:** Max 10% of account in single stock

**Daily loss limit:** -5% of account = STOP TRADING
- Do not attempt to "recover" same day

**Stop loss:** ATR-based
- Conservative: 2.0-2.5x ATR (large-cap)
- Moderate: 1.5-2.0x ATR (standard)
- Never move stop away from entry

[Full details →](../indian_markets/risk_management.md)

---

## High-Impact Events (Avoid Trading)

**Scheduled:**
- RBI Monetary Policy (6 times/year, announcement at 10:00 AM)
- Union Budget (Feb 1st, announcement at 11:00 AM)
- State/National Elections (results day)
- Quarterly Earnings (avoid stocks announcing that day)

**Unscheduled:**
- Fed interest rate decisions
- Major geopolitical events
- Oil price shocks (>10% moves)

**Detection:**
```python
# Check for abnormal volatility
if atr_today > 2 * atr_average:
    print("High volatility - avoid new entries")
```

[Full calendar →](../indian_markets/events.md)

---

## Quick Reference

**Volatility (typical intraday ranges):**
- Large-cap (Nifty 50): 1-3%
- Mid-cap: 2-5%

**Time filters for strategies:**
```python
current_time = self.data.datetime.time()
if current_time < datetime.time(9, 45) or current_time > datetime.time(14, 30):
    return  # Skip this bar
```

**Volume filter:**
```python
if self.data.volume[0] < (self.volume_sma[0] * 0.5):
    return  # Skip low volume bars
```

---

**Navigation:**
[CLAUDE.md](../../CLAUDE.md) | [Development Workflow](development_workflow.md) | [Full Indian Markets Guide](../indian_markets/README.md)
