# Liquidity Requirements

> Part of [Indian Market Trading Guide](README.md)

## Overview

Liquidity requirements ensure you can enter and exit positions without excessive slippage or market impact. Indian market liquidity varies significantly by stock capitalization and exchange.

---

---

## Liquidity Requirements

### Stock Selection Criteria

**Large-cap (Nifty 50):**
- Average daily volume: >50 lakh shares
- Position size: Up to 10% of daily volume
- Spread: Typically 0.01-0.05%
- **Best for algo trading** - highly liquid, predictable

**Mid-cap (Nifty Midcap 100):**
- Average daily volume: >10 lakh shares
- Position size: Max 5% of daily volume
- Spread: 0.05-0.15%
- **Usable with caution** - moderate liquidity

**Small-cap:**
- Average daily volume: <5 lakh shares
- **AVOID for algo trading** - illiquid, manipulated, wide spreads

### Position Limits

**By Liquidity:**
```
Max Position Size = min(
    10% of account,
    5% of stock's daily average volume,
    Rs 10 lakh per stock
)
```

**Example:**
- Account: Rs 10 lakh
- Max per stock: Rs 1 lakh (10% of account)
- If RELIANCE daily volume = 1 crore shares worth Rs 250 crore
- Max position: Rs 1 lakh (well within 5% of daily volume)

### Volume Filters for Strategies

**Minimum Requirements:**
- Minimum daily volume: 5 lakh shares
- Minimum current bar volume: 0.5x average volume
- For entry: Current volume > average volume (momentum confirmation)
- For breakouts: Current volume > 1.2x average volume

---

---

**Navigation:**
[← Trading Hours](trading_hours.md) | [README](README.md) | [Circuit Breakers →](circuit_breakers.md)
