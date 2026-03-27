# Indian Market Trading Guide

Comprehensive reference for algorithmic trading in Indian equity markets (NSE/BSE).

## Overview

This guide covers market-specific rules, patterns, and constraints essential for algorithmic trading in Indian markets. Understanding these is critical for strategy success.

**Quick Start:** For critical rules only, see [Market Essentials](../quick_start/market_essentials.md)

---

## Topics

### Trading Hours & Sessions

Official market timing, best trading windows for different strategies, session characteristics and liquidity patterns throughout the day.

**Key Points:** Main session 9:30 AM - 3:30 PM IST, avoid pre-market 9:15-9:30 AM, best algo window 9:45 AM - 2:30 PM.

[Full guide →](trading_hours.md)

### Liquidity Requirements

Stock selection criteria, position limits based on daily volume, minimum volume requirements for algorithmic trading.

**Key Points:** Min 5 lakh daily volume, prefer Nifty 50 stocks, max 10% of daily volume per position.

[Full guide →](liquidity.md)

### Circuit Breakers & Trading Halts

Price band limits, stock-level and index-level circuits, halt mechanics and strategy impact.

**Key Points:** ±5/10/20% bands, trading halts 15 min, avoid stocks near ±4% intraday move.

[Full guide →](circuit_breakers.md)

### Volatility Patterns

Intraday volatility ranges, weekly patterns, seasonal volatility, ATR reference values for Indian stocks.

**Key Points:** Large-cap 1-3% daily range, mid-cap 2-5%, higher volatility on Mondays and budget days.

[Full guide →](volatility.md)

### Risk Management Rules

Position sizing formulas, ATR-based stops, account limits, daily/weekly review processes, sector correlations.

**Key Points:** Max 3% risk per trade, max 10% per position, -5% daily loss = stop trading.

[Full guide →](risk_management.md)

### High-Impact Events

Scheduled events (RBI, Budget, Elections, Earnings), unscheduled shocks, event calendar and detection methods.

**Key Points:** Avoid trading on RBI policy days, Budget day, election results, stock-specific earnings.

[Full guide →](events.md)

---

## Quick Reference

**Critical Numbers:**
- Trading hours: 9:30 AM - 3:30 PM IST
- Algo-friendly window: 9:45 AM - 2:30 PM
- Min daily volume: 5 lakh shares
- Circuit breakers: ±5%, ±10%, ±20%
- Max risk per trade: 3%
- Max per position: 10%
- Daily loss limit: -5%

**Volatility Ranges:**
- Nifty 50 stocks: 1-3% intraday
- Mid-cap: 2-5% intraday
- ATR (14-period): ~1-3% of price for large-caps

**Volume Requirements:**
- Minimum: 5 lakh shares/day
- Position limit: 10% of daily volume
- Entry confirmation: Current volume > average

---

## Strategy Adaptation

**For High Volatility (Budget, RBI, Elections):**
- Use 2x ATR stops instead of 1.5x
- Reduce position sizes by 50%
- Tighten time filters
- Consider sitting out entirely

**For Low Liquidity Stocks:**
- Increase min volume to 10 lakh daily
- Reduce position limit to 5% of volume
- Wider spreads - account for slippage
- Prefer limit orders over market orders

**For Circuit Breaker Risk:**
- Monitor intraday move vs daily open
- Avoid entries if stock moved >±4% already
- Use wider stops (can't exit during halt)
- Smaller position sizes

---

## Related Documentation

**Quick Start:**
- [Market Essentials](../quick_start/market_essentials.md) - Condensed critical rules
- [Development Workflow](../quick_start/development_workflow.md) - Strategy development overview

**Strategy Development:**
- [Strategy Development Guide](../strategy_development/README.md) - Complete workflow
- [Parameter Design](../strategy_development/parameter_design.md) - Risk filters and time windows

**System:**
- [Backtesting System](../backtesting/README.md) - Test strategies on historical data

---

**Navigation:**
[CLAUDE.md](../../CLAUDE.md) | [Trading Hours →](trading_hours.md) | [Quick Start](../quick_start/market_essentials.md)
