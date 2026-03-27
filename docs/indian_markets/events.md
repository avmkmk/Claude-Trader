# High-Impact Events

> Part of [Indian Market Trading Guide](README.md)

## Overview

Calendar of scheduled and unscheduled high-impact events that significantly affect Indian market volatility. Algorithmic strategies should avoid or adapt during these periods.

---

---

## High-Impact Events (Avoid Trading)

### Scheduled Events

**RBI Monetary Policy:**
- Typically 6 meetings per year (Feb, Apr, Jun, Aug, Oct, Dec)
- Announcement at 10:00 AM
- **Impact:** ±1-2% index move, financial stocks heavily affected
- **Action:** Close positions before 9:30 AM, avoid new entries until 12:00 PM

**Union Budget:**
- February 1st (or last working day of January)
- Announcement at 11:00 AM
- **Impact:** ±3-5% index move, sector-specific shocks
- **Action:** No trading on budget day

**State Elections / National Elections:**
- Results day: extreme volatility
- **Impact:** ±5-10% index moves
- **Action:** No trading on results day and following day

**Quarterly Earnings:**
- Jan, Apr, Jul, Oct (earnings season)
- Individual stock risk
- **Action:** Avoid stocks announcing earnings that day

**Index Rebalancing:**
- Quarterly (end of Mar, Jun, Sep, Dec)
- Stocks entering/exiting Nifty 50
- **Impact:** Temporary volume spike, price impact
- **Action:** Avoid affected stocks on rebalancing day

### Unscheduled Events

**Global Events:**
- Fed interest rate decisions (usually 2:00 AM IST)
- Major geopolitical events (war, terrorist attacks)
- Oil price shocks (>10% moves)
- US market crashes (>3% down)

**Detection:**
```python
# Check for abnormal volatility
if atr_today > 2 * atr_average:
    print("High volatility - avoid new entries")
    # Tighten stops on existing positions
```


---

**Navigation:**
[← Risk Management](risk_management.md) | [README](README.md)

**Related:** [Market Essentials](../quick_start/market_essentials.md)
