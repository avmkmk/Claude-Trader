# Circuit Breakers & Trading Halts

> Part of [Indian Market Trading Guide](README.md)

## Overview

Circuit breakers pause trading when prices move beyond specified limits. Understanding these is critical for risk management in algorithmic strategies.

---


## Circuit Breakers & Trading Halts

### Stock-Level Circuits

**Price Bands:**
```
Category | Lower Limit | Upper Limit | Trading Halt
---------|-------------|-------------|-------------
Most stocks | -5% | +5% | 15 minutes
Volatile stocks | -10% | +10% | 15 minutes
High value | -20% | +20% | 15 minutes
```

**When Hit:**
1. Trading halts for 15 minutes
2. New price band created (±5% from halt price)
3. If hit again: Another 15-minute halt
4. Maximum 3 halts per day, then trading suspended

**Impact on Strategies:**
- Can't exit positions during halt (trapped)
- Gap risk after resumption
- **Solution:** Don't exceed 5% position size per stock, use wider stops

### Index-Level Circuits

**Market-Wide Halts:**
```
Nifty 50 Movement | Action | Duration
------------------|--------|----------
-10% from previous close | Trading halt | 45 minutes
-15% from previous close | Trading halt | 1 hour 45 minutes
-20% from previous close | Trading suspended | Rest of day
```

**Asymmetric:** Only downward movements trigger index circuits (no upward halts)

**Impact on Strategies:**
- All trades paused
- Can't close positions
- **Solution:** Daily loss limit (-5% account = stop all trading)

### Circuit Breaker Strategy

```python
# Example circuit breaker detection
def check_circuit_risk(symbol_data):
    today_open = symbol_data['open'][0]
    current_price = symbol_data['close'][0]
    pct_move = ((current_price - today_open) / today_open) * 100

    # Approaching circuit limits
    if abs(pct_move) > 4.0:  # Within 1% of 5% circuit
        return "HIGH_RISK"  # Avoid new entries
    elif abs(pct_move) > 3.0:  # Within 2% of 5% circuit
        return "MEDIUM_RISK"  # Tighten stops
    else:
        return "NORMAL"
```

---

**Navigation:**
[← Liquidity](liquidity.md) | [README](README.md) | [Volatility →](volatility.md)

**Related:** [Market Essentials](../quick_start/market_essentials.md)
