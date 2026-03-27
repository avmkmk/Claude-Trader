# Trading Hours & Sessions

> Part of [Indian Market Trading Guide](README.md)

## Overview

Understanding Indian market sessions and timing is critical for algorithmic trading. Different times of day have distinct characteristics in terms of liquidity, volatility, and directional bias.

---

# Indian Market Trading Guide

Comprehensive reference for algorithmic trading in Indian equity markets (NSE/BSE).

## Market Hours & Sessions

### Official Trading Hours

```
Pre-market Session:   9:00 AM - 9:15 AM (orders placed, no execution)
Pre-open Session:     9:15 AM - 9:30 AM (price discovery, high volatility)
Main Trading:         9:30 AM - 3:30 PM (regular trading)
Closing Session:      3:30 PM - 3:40 PM (closing price determination)
Post-close Session:   3:40 PM - 4:00 PM (at closing price only)
```

### Best Trading Windows

| Time Window | Characteristics | Best For |
|-------------|-----------------|----------|
| **9:15-9:30 AM** | Price discovery, high volatility, low liquidity | **AVOID** - Unpredictable |
| **9:30-10:00 AM** | Opening rush, highest volume, trend establishment | Momentum strategies |
| **10:00-11:00 AM** | Strong directional moves continue | Trend following |
| **11:00 AM-2:00 PM** | Often choppy, lower volume | Mean reversion |
| **2:00-3:00 PM** | Institutional activity picks up | Momentum/Trend |
| **3:00-3:30 PM** | Closing hour, volume spike | Reversals/Exits |
| **3:25-3:30 PM** | Last 5 minutes | **AVOID** - Gap risk |

### Recommended Trading Hours for Algo

**Conservative:** 9:45 AM - 2:30 PM
- Skips volatile opening and closing
- Captures main liquidity windows
- Avoids pre-market and last-minute gaps

**Aggressive:** 9:30 AM - 3:25 PM
- Full trading day
- Higher returns potential
- Requires robust risk management


---

**Navigation:**
[README](README.md) | [Liquidity →](liquidity.md)

**Related:** [Market Essentials](../quick_start/market_essentials.md)
