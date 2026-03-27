# Strategy Development

Complete workflow for creating profitable trading strategies for Indian markets.

## Overview

This guide provides a systematic 6-phase process for developing trading strategies that show positive PnL when backtested on historical Indian market data. Each phase ensures your strategy is properly researched, tested, and validated before deployment.

**Goal:** Create strategies with positive returns, strong risk-adjusted performance, and robust behavior across different market conditions.

**Workflow:** Research → Design → Implement → Backtest → Optimize → Validate

**Time Investment:** 2-4 hours for a well-researched strategy

---

## Process Phases

### Phase 1: Research & Selection

Identify market regime (trending, ranging, volatile) and select appropriate strategy type (momentum, mean reversion, breakout, trend following). Choose indicators and timeframe based on regime analysis.

**Key Outputs:** Strategy type, indicator selection, timeframe

[Full guide →](research_selection.md)

### Phase 2: Parameter Design

Define entry/exit conditions with primary signal and confirmation filters. Set position sizing formulas based on account risk and ATR. Add market filters for time (9:45 AM-2:30 PM), volume (>5 lakh daily), and volatility (circuit breaker awareness).

**Key Outputs:** Entry/exit logic, position sizing formula, filter rules

[Full guide →](parameter_design.md)

### Phase 3: Implementation

Create strategy class inheriting from `bt.Strategy`. Implement `__init__()` for indicator setup and `next()` for trading logic. Add time filters for Indian market hours, volume filters, and order management.

**Key Outputs:** Working strategy class, indicator calculations, trading logic

[Full guide →](implementation.md)

### Phase 4: Backtesting

Run strategy on 1+ year of historical data. Analyze performance metrics: Sharpe ratio, max drawdown, win rate, profit factor, total return. Use BacktestRunner for execution and get_metrics() for analysis.

**Key Outputs:** Performance metrics, trade log, equity curve

[Full guide →](backtesting.md)

### Phase 5: Optimization

Test parameter sensitivity by varying one parameter at a time. Perform walk-forward validation (train on period 1, test on period 2). Stress test on volatile periods (Budget day, Elections, RBI policy). Prevent overfitting by ensuring small parameter changes don't drastically alter results.

**Key Outputs:** Optimal parameter ranges, robustness verification, stress test results

[Full guide →](optimization.md)

### Phase 6: Validation

Final checklist before deployment. Verify performance criteria (Sharpe > 1.0, drawdown < 15%, positive returns). Confirm robustness (tested on multiple symbols, works in different regimes). Check risk management (stops enforced, position limits respected).

**Key Outputs:** Deployment decision, final validation report

[Full guide →](validation.md)

---

## Success Criteria

Before deploying a strategy, ensure it meets these criteria:

**Performance:**
- [ ] Positive total return on backtest
- [ ] Sharpe ratio > 1.0
- [ ] Max drawdown < 15%
- [ ] Win rate meets strategy minimums:
  - Momentum/Mean Reversion: >50%
  - Breakout: >45%
- [ ] Profit factor > 1.5

**Robustness:**
- [ ] Tested on 1+ year Indian market data
- [ ] Tested on 5+ different stocks (Nifty 50)
- [ ] Parameter changes of ±10% don't flip results
- [ ] Works in different market regimes

**Risk Management:**
- [ ] Time filters: 9:45 AM - 2:30 PM IST
- [ ] Volume filter: Min 5 lakh daily
- [ ] Stop loss enforced (no exceptions)
- [ ] Max hold time defined
- [ ] Circuit breaker awareness (avoid ±4% stocks)

**Documentation:**
- [ ] Strategy logic documented
- [ ] Entry/exit conditions clear
- [ ] Risk parameters defined
- [ ] Backtest results saved

---

## Strategy Templates

Use pre-built templates for quick start:

- **Mean Reversion**: RSI + Bollinger Bands ([template](../../strategies/templates/mean_reversion_template.py))
- **Momentum**: MACD + Volume ([template](../../strategies/templates/momentum_template.py))
- **Breakout**: ATR + Volume ([template](../../strategies/templates/breakout_template.py))

[Template usage guide →](../../strategies/README.md)

---

## Quick Reference

**Market Regimes:**
- **Trending**: ADX > 25, diverging MAs → Momentum, Trend Following
- **Ranging**: ADX < 20, flat MAs → Mean Reversion
- **Volatile**: Expanding ATR → Breakout, Volatility

**Indian Market Hours:**
- Trading: 9:30 AM - 3:30 PM IST
- Best for algo: 9:45 AM - 2:30 PM

**Risk Limits:**
- Max 3% per trade
- Max 10% per position
- -5% daily loss = stop trading

**Backtesting:**
```python
from backtesting.backtest_runner import BacktestRunner

runner = BacktestRunner(initial_cash=100000)
runner.load_data('data/SYMBOL_90days.csv', 'SYMBOL')
runner.add_strategy(YourStrategy, param1=value1)
runner.add_analyzers()

result = runner.run()
metrics = runner.get_metrics(result)
```

---

## Related Documentation

**Quick Start:**
- [Development Workflow](../quick_start/development_workflow.md) - Condensed version
- [Market Essentials](../quick_start/market_essentials.md) - Critical Indian market rules
- [Common Commands](../quick_start/common_commands.md) - Quick command reference

**Detailed Guides:**
- [Indian Market Trading Guide](../indian_markets/README.md) - Full market reference
- [Backtesting System](../backtesting/README.md) - System architecture
- [Creating Strategies](../backtesting/creating_strategies.md) - Implementation patterns

---

**Navigation:**
[CLAUDE.md](../../CLAUDE.md) | [Phase 1: Research →](research_selection.md) | [Indian Markets](../indian_markets/README.md)
