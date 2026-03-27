# Validation

> Part of [Strategy Development Workflow](README.md) - Phase 6 of 6


Before deploying a strategy, verify:

### Performance Criteria
- [ ] **Positive total return** on backtest (>5% annually)
- [ ] **Sharpe ratio > 1.0** (preferably >1.5)
- [ ] **Max drawdown < 15%** (preferably <10%)
- [ ] **Win rate meets strategy minimums**:
  - Mean reversion: >55%
  - Momentum: >50%
  - Breakout: >45%
  - Trend following: >45%
- [ ] **Profit factor > 1.5** (preferably >2.0)

### Robustness Criteria
- [ ] **Tested on 1+ year of Indian market data**
- [ ] **Parameter sensitivity acceptable** (±10% param change doesn't flip results)
- [ ] **Walk-forward validation passed** (testing period results similar to training)
- [ ] **Stress tested on volatile periods** (drawdown still acceptable)
- [ ] **Multi-symbol validation** (works on 5+ different stocks)

### Risk Management Criteria
- [ ] **Max risk per trade ≤ 3%** of account
- [ ] **Max position size ≤ 10%** of account
- [ ] **Daily loss limit defined** (e.g., -5% stops trading for day)
- [ ] **Time filters implemented** (avoid illiquid windows, high-impact events)
- [ ] **Volume filters implemented** (min 5 lakh daily volume)

### Documentation Criteria
- [ ] **Strategy logic documented** in code comments
- [ ] **Entry/exit rules clearly defined**
- [ ] **Parameter rationale explained** (why these values?)
- [ ] **Backtest results saved** (metrics + trade log)
- [ ] **Known limitations documented** (what market conditions does it fail in?)

---

## Post-Validation: Deployment Considerations

**Before going live:**

1. **Paper trading**: Run strategy on live data without real money for 1-2 weeks
2. **Small position sizes**: Start with 25-50% of intended position size
3. **Monitor closely**: Watch first 10-20 trades for unexpected behavior
4. **Gradual scaling**: Increase position size only after consistent results

**Red flags to watch:**
- Slippage much worse than backtest (adjust commission in backtest)
- More losses in live than backtest (market regime may have changed)
- Orders not filling (liquidity issues, adjust position size)

**When to stop a strategy:**
- Drawdown exceeds backtest max by 50% (e.g., if backtest max was 10%, stop at 15%)
- Win rate drops below strategy minimum for 30+ trades
- Market regime changed (trending strategy in ranging market won't work)

---

## Indian Market-Specific Guidelines

See **INDIAN_MARKET_GUIDE.md** for comprehensive details.

**Quick Checklist:**
- [ ] Trading only during 9:30 AM - 3:30 PM IST
- [ ] Avoiding pre-market (9:15-9:30 AM)
- [ ] Position limits respect liquidity (max 10% of daily volume)
- [ ] Circuit breaker rules considered (5%/10%/20% limits)
- [ ] High-impact events calendared (RBI, budget, elections)
- [ ] Volatility patterns understood (weekly, seasonal)

---

## Resources

- **Strategy Templates**: `strategies/templates/`
- **Indian Market Guide**: `INDIAN_MARKET_GUIDE.md`
- **Backtrader Documentation**: https://www.backtrader.com/docu/
- **Dashboard**: `streamlit run dashboard/streamlit_app.py`

## Support

For questions or issues:
1. Check CLAUDE.md for architecture overview
2. Review strategy templates for implementation examples
3. Use dashboard for interactive backtesting
4. Consult Backtrader docs for advanced indicators

---

**Navigation:**
[← Optimization](optimization.md) | [README](README.md)
