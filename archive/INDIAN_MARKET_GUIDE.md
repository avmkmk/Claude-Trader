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

## Volatility Patterns

### Intraday Volatility

**Large-cap (Nifty 50 stocks):**
- Typical intraday range: 1-3%
- During high volatility: 3-5%
- Earnings day: 5-10%

**Mid-cap:**
- Typical intraday range: 2-5%
- During high volatility: 5-8%

**ATR Reference Values:**
- Nifty 50 index: 100-200 points (daily ATR)
- Large-cap stock: 1-3% of price
- Mid-cap stock: 2-5% of price

### Weekly Patterns

| Day | Volatility | Direction Bias | Best Strategy |
|-----|-----------|----------------|---------------|
| **Monday** | Slightly higher | Gap risk (weekend news) | Avoid first hour |
| **Tuesday** | Normal-High | Often trending | Momentum, Trend |
| **Wednesday** | Normal | Most consistent | All strategies |
| **Thursday** | Normal-High | Trend continuation | Momentum, Trend |
| **Friday** | Lower | Profit-taking | Mean reversion, Exits |

### Seasonal Volatility

**High Volatility Periods:**
- Budget announcement (Feb 1st) - ±3-5% moves
- Quarterly earnings (Jan, Apr, Jul, Oct) - stock-specific
- Elections - weeks before and after results
- Monsoon season (Jun-Sep) - agriculture sector impact
- Year-end (Dec) - tax-loss harvesting

**Low Volatility Periods:**
- Post-budget (Feb-Mar) - consolidation
- Summer (May) - lower volumes
- Festival season (Oct-Nov) - mixed (Diwali rally possible)

**Strategy Adaptation:**
- High volatility: Use wider stops (2x ATR instead of 1.5x)
- Low volatility: Can use tighter stops, mean reversion works better

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

## Tax Implications (Awareness Only)

**Short-Term Capital Gains (STCG):**
- Holding period: < 1 year
- Tax: 15% (as of 2024)

**Long-Term Capital Gains (LTCG):**
- Holding period: > 1 year
- Tax: 10% (above Rs 1 lakh exemption)

**Intraday Trading:**
- Treated as speculative business income
- Tax: Per income tax slab rate

**Note:** Algo trading is typically short-term or intraday, so STCG/speculative income rules apply. Consult tax professional for compliance.

---

## Practical Checklist for Strategy Development

### Before Live Trading

- [ ] Tested on 1+ year NSE historical data
- [ ] Tested on multiple Nifty 50 stocks (min 5)
- [ ] Time filters: 9:45 AM - 2:30 PM only
- [ ] Volume filter: Min 5 lakh daily, min 0.5x avg per bar
- [ ] Stop loss enforced: Max 3% risk per trade
- [ ] Position size: Max 10% account per stock
- [ ] Daily loss limit: -5% account = stop trading
- [ ] Circuit breaker awareness: Avoid stocks near ±4%
- [ ] High-impact events calendared (RBI, Budget, Elections)
- [ ] Backtested Sharpe > 1.0, Max DD < 15%
- [ ] Paper traded 1-2 weeks with realistic slippage

### During Live Trading

- [ ] Monitor first 10 trades closely
- [ ] Log slippage (difference between backtest and live fills)
- [ ] Track win rate vs backtest target
- [ ] Check max drawdown daily
- [ ] Review trades weekly
- [ ] Stop strategy if drawdown exceeds 1.5x backtest max

---

## Resources

- **NSE Website:** https://www.nseindia.com/
- **Market Hours:** https://www.nseindia.com/market-data/live-equity-market
- **Circuit Breakers:** https://www.nseindia.com/regulations/listing-compliance/price-bands
- **Nifty 50 Constituents:** https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-50
- **Economic Calendar:** https://www.moneycontrol.com/economy/calendar/

## Support

For strategy development questions:
- See `STRATEGY_DEVELOPMENT.md` for workflow
- See `strategies/README.md` for implementation guidance
- See `CLAUDE.md` for system architecture
