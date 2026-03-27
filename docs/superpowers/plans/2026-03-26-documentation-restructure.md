# Documentation Restructuring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure SimpleTrader documentation into hierarchical, lazy-loading system with no file exceeding 200 lines

**Architecture:** Split existing monolithic markdown files (STRATEGY_DEVELOPMENT.md, INDIAN_MARKET_GUIDE.md, CLAUDE.md) into organized subdirectories under docs/ with parent README files containing brief summaries and links to child documents. Create quick_start/ for condensed guides.

**Tech Stack:** Markdown, Git, Bash

**Spec:** `docs/superpowers/specs/2026-03-26-doc-restructure-design.md`

---

## File Structure

**Directories to Create:**
- `docs/quick_start/` - Condensed actionable guides
- `docs/strategy_development/` - Detailed workflow (7 files)
- `docs/indian_markets/` - Market reference (8 files)
- `docs/backtesting/` - System documentation (3 files)
- `archive/` - Old documentation files

**Files to Create (21 new files):**
- `CLAUDE.md` (rewrite, ~150 lines)
- `docs/quick_start/development_workflow.md` (~150 lines)
- `docs/quick_start/market_essentials.md` (~150 lines)
- `docs/quick_start/common_commands.md` (~100 lines)
- `docs/strategy_development/README.md` (~150 lines)
- `docs/strategy_development/research_selection.md` (~180 lines)
- `docs/strategy_development/parameter_design.md` (~150 lines)
- `docs/strategy_development/implementation.md` (~120 lines)
- `docs/strategy_development/backtesting.md` (~100 lines)
- `docs/strategy_development/optimization.md` (~150 lines)
- `docs/strategy_development/validation.md` (~120 lines)
- `docs/indian_markets/README.md` (~100 lines)
- `docs/indian_markets/trading_hours.md` (~120 lines)
- `docs/indian_markets/liquidity.md` (~100 lines)
- `docs/indian_markets/circuit_breakers.md` (~120 lines)
- `docs/indian_markets/volatility.md` (~120 lines)
- `docs/indian_markets/risk_management.md` (~150 lines)
- `docs/indian_markets/events.md` (~80 lines)
- `docs/backtesting/README.md` (~150 lines)
- `docs/backtesting/architecture.md` (~120 lines)
- `docs/backtesting/creating_strategies.md` (~180 lines)

**Files to Modify:**
- `strategies/README.md` (consolidate to ~180 lines)

**Files to Archive:**
- `STRATEGY_DEVELOPMENT.md` → `archive/STRATEGY_DEVELOPMENT.md`
- `INDIAN_MARKET_GUIDE.md` → `archive/INDIAN_MARKET_GUIDE.md`
- `CLAUDE.md` → `archive/CLAUDE.md.old`

---

## Task 1: Create Directory Structure

**Files:**
- Create: `docs/quick_start/`
- Create: `docs/strategy_development/`
- Create: `docs/indian_markets/`
- Create: `docs/backtesting/`
- Create: `archive/`

- [ ] **Step 1: Create all directories**

```bash
mkdir -p docs/quick_start
mkdir -p docs/strategy_development
mkdir -p docs/indian_markets
mkdir -p docs/backtesting
mkdir -p archive
```

Expected: Directories created successfully

- [ ] **Step 2: Verify directory structure**

```bash
ls -la docs/
```

Expected output:
```
quick_start/
strategy_development/
indian_markets/
backtesting/
superpowers/
```

- [ ] **Step 3: Commit directory structure**

```bash
git add docs/ archive/
git commit -m "docs: create directory structure for hierarchical documentation"
```

---

## Task 2: Create Quick Start - Development Workflow

**Files:**
- Create: `docs/quick_start/development_workflow.md`

- [ ] **Step 1: Create development_workflow.md with content**

```bash
cat > "docs/quick_start/development_workflow.md" << 'EOF'
# Development Workflow - Quick Start

Quick reference for developing trading strategies in SimpleTrader.

## Setup

**Activate environment:**
```bash
source venv/Scripts/activate  # Git Bash
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Configuration:**
Create `.env` with broker credentials:
```
NUBRA_CLIENT_ID="your_client_id"
NUBRA_MPIN="your_mpin"
UPSTOX_ACCESS_TOKEN="your_token"
```

---

## Strategy Development (Condensed)

### 1. Research & Selection
- Identify market regime (trending, ranging, volatile)
- Select strategy type (momentum, mean reversion, breakout)
- Choose appropriate indicators and timeframe

[Full guide →](../strategy_development/research_selection.md)

### 2. Parameter Design
- Define entry/exit conditions (primary signal + confirmation)
- Set position sizing (risk per trade, ATR-based)
- Add filters (time: 9:45 AM-2:30 PM, volume: >5 lakh daily)

[Full guide →](../strategy_development/parameter_design.md)

### 3. Implementation
Create strategy class:
```python
import backtrader as bt
import datetime

class MyStrategy(bt.Strategy):
    params = (('period', 20),)

    def __init__(self):
        self.indicator = bt.indicators.SMA(self.data.close, period=self.params.period)

    def next(self):
        # Time filter (Indian market hours)
        current_time = self.data.datetime.time()
        if current_time < datetime.time(9, 45) or current_time > datetime.time(14, 30):
            return

        # Entry/exit logic
        if not self.position:
            if self.data.close[0] > self.indicator[0]:
                self.buy()
        else:
            if self.data.close[0] < self.indicator[0]:
                self.sell()
```

[Full guide →](../strategy_development/implementation.md)

### 4. Backtesting
Run backtest:
```python
from backtesting.backtest_runner import BacktestRunner

runner = BacktestRunner(initial_cash=100000)
runner.load_data('data/GRAPHITE_90days.csv', 'GRAPHITE')
runner.add_strategy(MyStrategy, period=20)
runner.add_analyzers()

result = runner.run()
metrics = runner.get_metrics(result)
```

Key metrics:
- **Sharpe ratio**: >1.0 (good)
- **Max drawdown**: <15% (target)
- **Win rate**: >50% (depends on strategy type)

[Full guide →](../strategy_development/backtesting.md)

### 5. Optimization
- Parameter sensitivity testing (vary one parameter at a time)
- Walk-forward validation (train on period 1, test on period 2)
- Stress test on volatile periods (Budget day, Elections)

[Full guide →](../strategy_development/optimization.md)

### 6. Validation Checklist
- [ ] Positive total return on backtest
- [ ] Sharpe ratio > 1.0
- [ ] Max drawdown < 15%
- [ ] Win rate > 50% (momentum/mean reversion) or >45% (breakout)
- [ ] Profit factor > 1.5
- [ ] Tested on 1+ year Indian market data
- [ ] Time filters: 9:45 AM - 2:30 PM IST
- [ ] Volume filter: Min 5 lakh daily

[Full criteria →](../strategy_development/validation.md)

---

## Common Commands

**Launch dashboard (recommended):**
```bash
streamlit run dashboard/streamlit_app.py
# Access at http://localhost:8501
```

**Quick backtest (command line):**
```bash
python -c "from backtesting.backtest_runner import BacktestRunner; from strategies.sma_crossover import SMACrossoverStrategy; r = BacktestRunner(); r.load_data('data/GRAPHITE_3months.csv', 'GRAPHITE'); r.add_strategy(SMACrossoverStrategy); r.add_analyzers(); result = r.run(); print(r.get_metrics(result))"
```

**Scrape single equity:**
```bash
python -c "from apis.nubra_api import NubraAPIHandler; from backtesting.data_scraper import EquityDataScraper; n = NubraAPIHandler(); n.initialize_sdk(); s = EquityDataScraper(n); df = s.scrape_equity('RELIANCE'); s.save_to_csv(df, 'RELIANCE', 90)"
```

[Full commands →](common_commands.md)

---

## Templates

Use strategy templates for quick start:
- **Mean Reversion**: `strategies/templates/mean_reversion_template.py`
- **Momentum**: `strategies/templates/momentum_template.py`
- **Breakout**: `strategies/templates/breakout_template.py`

[Template usage →](../../strategies/README.md)

---

**Navigation:**
[CLAUDE.md](../../CLAUDE.md) | [Strategy Development](../strategy_development/README.md) | [Indian Markets](../indian_markets/README.md)
EOF
```

- [ ] **Step 2: Verify file created and line count**

```bash
wc -l docs/quick_start/development_workflow.md
```

Expected: ~150 lines (accept 140-160)

- [ ] **Step 3: Commit**

```bash
git add docs/quick_start/development_workflow.md
git commit -m "docs: add development workflow quick start guide"
```

---

## Task 3: Create Quick Start - Market Essentials

**Files:**
- Create: `docs/quick_start/market_essentials.md`

- [ ] **Step 1: Create market_essentials.md with content**

```bash
cat > "docs/quick_start/market_essentials.md" << 'EOF'
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
EOF
```

- [ ] **Step 2: Verify line count**

```bash
wc -l docs/quick_start/market_essentials.md
```

Expected: ~150 lines (accept 140-160)

- [ ] **Step 3: Commit**

```bash
git add docs/quick_start/market_essentials.md
git commit -m "docs: add Indian market essentials quick start guide"
```

---

## Task 4: Create Quick Start - Common Commands

**Files:**
- Create: `docs/quick_start/common_commands.md`

- [ ] **Step 1: Create common_commands.md with content**

```bash
cat > "docs/quick_start/common_commands.md" << 'EOF'
# Common Commands

Quick command reference for SimpleTrader development.

## Dashboard (Recommended Interface)

```bash
streamlit run dashboard/streamlit_app.py
```

Access at: http://localhost:8501

**Features:**
- Nubra authentication
- Batch data scraping (50+ equities)
- Interactive backtesting with charts
- Real-time metrics display

---

## Testing Strategies

### Via Dashboard (Preferred)
1. Launch dashboard: `streamlit run dashboard/streamlit_app.py`
2. Navigate to "Backtesting" page
3. Select data file and strategy
4. Click "Run Backtest"
5. View metrics and charts

### Command Line (Quick Test)
```bash
python -c "from backtesting.backtest_runner import BacktestRunner; \
from strategies.sma_crossover import SMACrossoverStrategy; \
r = BacktestRunner(); \
r.load_data('data/GRAPHITE_3months.csv', 'GRAPHITE'); \
r.add_strategy(SMACrossoverStrategy); \
r.add_analyzers(); \
result = r.run(); \
metrics = r.get_metrics(result); \
print(f\"Sharpe: {metrics['sharpe_ratio']}, Return: {metrics['returns']['total_return']:.2%}\")"
```

### Test Custom Strategy
```python
python my_strategy.py  # If strategy includes __main__ block
```

---

## Data Scraping

### Single Equity
```bash
python -c "from apis.nubra_api import NubraAPIHandler; \
from backtesting.data_scraper import EquityDataScraper; \
n = NubraAPIHandler(); \
n.initialize_sdk(); \
s = EquityDataScraper(n); \
df = s.scrape_equity('RELIANCE'); \
s.save_to_csv(df, 'RELIANCE', 90)"
```

Saves to: `data/RELIANCE_90days.csv`

### Batch Scraping (Via Dashboard)
1. Launch dashboard
2. Go to "Data Scraping" page
3. Select equities from dropdown (multi-select)
4. Choose period (90 days, 180 days, 1 year)
5. Click "Start Scraping"
6. Monitor progress bar

**Rate limit:** 60 requests/minute (Nubra API limit)

---

## Authentication Testing

```bash
python -c "from apis.nubra_api import NubraAPIHandler; \
n = NubraAPIHandler(); \
print('Auth:', n.initialize_sdk())"
```

Expected output: `Auth: True`

If fails: Check `.env` file has correct `NUBRA_CLIENT_ID` and `NUBRA_MPIN`

---

## Development

### Activate Virtual Environment
```bash
source venv/Scripts/activate  # Git Bash
# Or: venv\Scripts\activate.bat  # Windows CMD
# Or: venv\Scripts\Activate.ps1  # PowerShell
```

### Install/Update Dependencies
```bash
pip install -r requirements.txt
```

### Check Installed Packages
```bash
pip list | grep -E "backtrader|streamlit|nubra|upstox"
```

---

## Troubleshooting

### "Module not found" Error
```bash
# Ensure venv is activated
source venv/Scripts/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Nubra Authentication Fails
```bash
# Check environment variables
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('CLIENT_ID:', os.getenv('NUBRA_CLIENT_ID')[:10] if os.getenv('NUBRA_CLIENT_ID') else 'NOT SET')"
```

Ensure `.env` exists in project root with:
```
NUBRA_CLIENT_ID="your_client_id"
NUBRA_MPIN="your_mpin"
```

### Dashboard Port Already in Use
```bash
# Use different port
streamlit run dashboard/streamlit_app.py --server.port 8502
```

### Data File Not Found
```bash
# List available data files
ls -lh data/*.csv

# Check file path in backtest code
# Ensure relative path from project root: data/SYMBOL_XXdays.csv
```

---

**Navigation:**
[CLAUDE.md](../../CLAUDE.md) | [Development Workflow](development_workflow.md) | [Market Essentials](market_essentials.md)
EOF
```

- [ ] **Step 2: Verify line count**

```bash
wc -l docs/quick_start/common_commands.md
```

Expected: ~100 lines (accept 90-110)

- [ ] **Step 3: Commit**

```bash
git add docs/quick_start/common_commands.md
git commit -m "docs: add common commands quick start guide"
```

---

## Task 5: Create Strategy Development README

**Files:**
- Create: `docs/strategy_development/README.md`

- [ ] **Step 1: Read current STRATEGY_DEVELOPMENT.md for content**

```bash
head -50 STRATEGY_DEVELOPMENT.md
```

- [ ] **Step 2: Create README.md with overview content**

Create file with overview, phase summaries (2-3 sentences each), success criteria, and links to detailed phase documents.

Content structure:
- Overview paragraph
- Process Phases (6 phases with brief summary + link each)
- Success Criteria checklist
- Quick Start link

Target: ~150 lines

- [ ] **Step 3: Verify line count**

```bash
wc -l docs/strategy_development/README.md
```

Expected: ~150 lines (accept 140-160)

- [ ] **Step 4: Commit**

```bash
git add docs/strategy_development/README.md
git commit -m "docs: add strategy development README with workflow overview"
```

---

## Task 6: Split STRATEGY_DEVELOPMENT.md into Phase Files

**Files:**
- Read: `STRATEGY_DEVELOPMENT.md`
- Create: `docs/strategy_development/research_selection.md` (Phase 1)
- Create: `docs/strategy_development/parameter_design.md` (Phase 2)
- Create: `docs/strategy_development/implementation.md` (Phase 3)
- Create: `docs/strategy_development/backtesting.md` (Phase 4)
- Create: `docs/strategy_development/optimization.md` (Phase 5)
- Create: `docs/strategy_development/validation.md` (Phase 6)

- [ ] **Step 1: Extract Phase 1 content to research_selection.md**

Extract lines covering "Research & Selection" from STRATEGY_DEVELOPMENT.md.
Add:
- Header: `# Research & Selection`
- Context note: `> Part of [Strategy Development Workflow](README.md) - Phase 1 of 6`
- Overview paragraph
- Content organized into subsections
- Footer navigation with links

Target: ~180 lines

- [ ] **Step 2: Extract Phase 2 content to parameter_design.md**

Extract "Parameter Design" content.
Similar structure as Phase 1.
Target: ~150 lines

- [ ] **Step 3: Extract Phase 3 content to implementation.md**

Extract "Implementation" content.
Include code examples for strategy class structure.
Target: ~120 lines

- [ ] **Step 4: Extract Phase 4 content to backtesting.md**

Extract "Backtesting" content.
Include commands and metrics explanation.
Target: ~100 lines

- [ ] **Step 5: Extract Phase 5 content to optimization.md**

Extract "Optimization" content.
Include parameter tuning code examples.
Target: ~150 lines

- [ ] **Step 6: Extract Phase 6 content to validation.md**

Extract "Validation" content.
Include complete checklist and deployment criteria.
Target: ~120 lines

- [ ] **Step 7: Verify all line counts**

```bash
wc -l docs/strategy_development/*.md
```

Expected: Each file under 200 lines

- [ ] **Step 8: Commit all phase files**

```bash
git add docs/strategy_development/
git commit -m "docs: split strategy development workflow into phase files"
```

---

## Task 7: Create Indian Markets README

**Files:**
- Create: `docs/indian_markets/README.md`

- [ ] **Step 1: Read current INDIAN_MARKET_GUIDE.md for overview**

```bash
head -100 INDIAN_MARKET_GUIDE.md
```

- [ ] **Step 2: Create README.md with overview and TOC**

Content structure:
- Brief intro (NSE/BSE context)
- Topics list with 2-3 sentence description + link per topic:
  - Trading Hours & Sessions
  - Liquidity Requirements
  - Circuit Breakers & Trading Halts
  - Volatility Patterns
  - Risk Management Rules
  - High-Impact Events
- Key numbers summary
- Quick Start link

Target: ~100 lines

- [ ] **Step 3: Verify line count**

```bash
wc -l docs/indian_markets/README.md
```

Expected: ~100 lines (accept 90-110)

- [ ] **Step 4: Commit**

```bash
git add docs/indian_markets/README.md
git commit -m "docs: add Indian markets README with topics overview"
```

---

## Task 8: Split INDIAN_MARKET_GUIDE.md into Topic Files

**Files:**
- Read: `INDIAN_MARKET_GUIDE.md`
- Create: `docs/indian_markets/trading_hours.md`
- Create: `docs/indian_markets/liquidity.md`
- Create: `docs/indian_markets/circuit_breakers.md`
- Create: `docs/indian_markets/volatility.md`
- Create: `docs/indian_markets/risk_management.md`
- Create: `docs/indian_markets/events.md`

- [ ] **Step 1: Extract trading hours content to trading_hours.md**

Extract "Market Hours & Sessions" + "Best Trading Windows" sections.
Add header, context, organized subsections, footer navigation.
Target: ~120 lines

- [ ] **Step 2: Extract liquidity content to liquidity.md**

Extract "Liquidity Requirements" section.
Include stock selection criteria, position limits, volume filters.
Target: ~100 lines

- [ ] **Step 3: Extract circuit breakers content to circuit_breakers.md**

Extract "Circuit Breakers & Trading Halts" section.
Include stock-level and index-level circuits, strategy impact, detection code.
Target: ~120 lines

- [ ] **Step 4: Extract volatility content to volatility.md**

Extract "Volatility Patterns" section.
Include intraday, weekly, seasonal patterns, ATR values.
Target: ~120 lines

- [ ] **Step 5: Extract risk management content to risk_management.md**

Extract "Risk Management Rules" section + "Sector Rotation & Correlations".
Include position sizing formulas, stop loss rules, account limits, sector behavior.
Target: ~150 lines

- [ ] **Step 6: Extract events content to events.md**

Extract "High-Impact Events" section.
Include scheduled and unscheduled events, detection methods.
Target: ~80 lines

- [ ] **Step 7: Verify all line counts**

```bash
wc -l docs/indian_markets/*.md
```

Expected: Each file under 200 lines

- [ ] **Step 8: Commit all topic files**

```bash
git add docs/indian_markets/
git commit -m "docs: split Indian market guide into topic files"
```

---

## Task 9: Create Backtesting Documentation

**Files:**
- Create: `docs/backtesting/README.md`
- Create: `docs/backtesting/architecture.md`
- Create: `docs/backtesting/creating_strategies.md`

- [ ] **Step 1: Create backtesting README.md**

Extract backtesting system content from current CLAUDE.md.

Content structure:
- Architecture diagram (text format)
- Components overview (4-5 paragraphs):
  - Strategy Framework
  - Backtest Runner
  - Data Scraper
  - Dashboard
- Quick example (basic backtest code)
- Performance metrics explanation
- Links to detailed docs

Target: ~150 lines

- [ ] **Step 2: Create architecture.md**

Detailed component design:
- BacktestRunner API (methods, parameters)
- Data flow (diagram in text)
- Analyzer configuration
- Metrics calculation
- Integration with Backtrader

Target: ~120 lines

- [ ] **Step 3: Create creating_strategies.md**

Practical guide (consolidate from strategies/README.md where relevant):
- Strategy class structure (Backtrader concepts)
- Indicator usage patterns
- Entry/exit logic examples
- Time filters for Indian markets
- Volume filters
- Common mistakes
- Testing workflow

Target: ~180 lines

- [ ] **Step 4: Verify line counts**

```bash
wc -l docs/backtesting/*.md
```

Expected: Each file under 200 lines

- [ ] **Step 5: Commit backtesting docs**

```bash
git add docs/backtesting/
git commit -m "docs: add backtesting system documentation"
```

---

## Task 10: Rewrite CLAUDE.md

**Files:**
- Read: Current `CLAUDE.md`
- Create: New `CLAUDE.md` (~150 lines)
- Archive: `archive/CLAUDE.md.old`

- [ ] **Step 1: Archive current CLAUDE.md**

```bash
cp CLAUDE.md archive/CLAUDE.md.old
```

- [ ] **Step 2: Create new lean CLAUDE.md**

Content structure (as specified in design spec):
1. Header
2. Project Overview (2-3 paragraphs)
3. Quick Links section (bullet list to docs)
4. Project Structure (directory tree)
5. Core Concepts (4-5 paragraphs with links)
6. Development Setup (commands only)
7. Configuration (.env example)
8. Key Dependencies (bullet list)
9. Documentation Index (organized list)

Target: ~150 lines (hard limit: 180)

- [ ] **Step 3: Verify line count**

```bash
wc -l CLAUDE.md
```

Expected: ~150 lines (must be under 180)

- [ ] **Step 4: Test CLAUDE.md loads correctly**

Read the file to ensure no syntax errors:
```bash
cat CLAUDE.md | head -30
```

- [ ] **Step 5: Commit new CLAUDE.md**

```bash
git add CLAUDE.md archive/CLAUDE.md.old
git commit -m "docs: rewrite CLAUDE.md as lean entry point with navigation links"
```

---

## Task 11: Update strategies/README.md

**Files:**
- Modify: `strategies/README.md`

- [ ] **Step 1: Read current strategies/README.md**

```bash
wc -l strategies/README.md
cat strategies/README.md | head -50
```

Current: 293 lines

- [ ] **Step 2: Consolidate and trim to ~180 lines**

Changes:
- Remove content duplicating `docs/strategy_development/`
- Keep: Template descriptions, usage instructions, parameter tuning basics
- Add cross-references:
  - "For detailed strategy development workflow: [Strategy Development Guide](../docs/strategy_development/README.md)"
  - "For creating strategies from scratch: [Creating Strategies](../docs/backtesting/creating_strategies.md)"
- Consolidate guides/ content into main README (if guides/ exists)

Target: ~180 lines

- [ ] **Step 3: Verify line count**

```bash
wc -l strategies/README.md
```

Expected: ~180 lines (accept 170-190, must be under 200)

- [ ] **Step 4: Commit updated strategies README**

```bash
git add strategies/README.md
git commit -m "docs: consolidate strategies README and add cross-references"
```

---

## Task 12: Update Cross-References and Links

**Files:**
- Modify: All newly created markdown files

- [ ] **Step 1: Find all internal markdown links**

```bash
grep -r "\[.*\](.*.md)" docs/ strategies/README.md CLAUDE.md | grep -v "http" | cut -d: -f1 | sort -u
```

- [ ] **Step 2: Verify links use correct paths**

Check for common issues:
- Links in `docs/strategy_development/*.md` should use `../` for docs/
- Links in `docs/quick_start/*.md` should use `../../` for root files
- Links in root files should use `docs/` prefix

- [ ] **Step 3: Test sample links manually**

```bash
# Test that target files exist
ls -l docs/strategy_development/README.md
ls -l docs/quick_start/development_workflow.md
ls -l docs/indian_markets/circuit_breakers.md
```

- [ ] **Step 4: Add navigation footers to all detailed docs**

Each detailed doc should end with:
```markdown
---
**Navigation:**
[← Previous](previous.md) | [README](README.md) | [Next →](next.md)

**Related:** [Quick Start](../quick_start/xxx.md) | [Other Topics](../other/related.md)
```

Apply to:
- All strategy_development phase files (6 files)
- All indian_markets topic files (6 files)
- All backtesting docs (2 detail files)

- [ ] **Step 5: Commit link updates**

```bash
git add docs/ strategies/README.md CLAUDE.md
git commit -m "docs: update cross-references and add navigation footers"
```

---

## Task 13: Archive Old Documentation Files

**Files:**
- Move: `STRATEGY_DEVELOPMENT.md` → `archive/STRATEGY_DEVELOPMENT.md`
- Move: `INDIAN_MARKET_GUIDE.md` → `archive/INDIAN_MARKET_GUIDE.md`

- [ ] **Step 1: Move old documentation to archive**

```bash
mv STRATEGY_DEVELOPMENT.md archive/
mv INDIAN_MARKET_GUIDE.md archive/
```

- [ ] **Step 2: Verify files moved**

```bash
ls -l archive/
```

Expected:
- archive/CLAUDE.md.old
- archive/STRATEGY_DEVELOPMENT.md
- archive/INDIAN_MARKET_GUIDE.md

- [ ] **Step 3: Verify old files no longer in root**

```bash
ls -l *.md
```

Should NOT show STRATEGY_DEVELOPMENT.md or INDIAN_MARKET_GUIDE.md

- [ ] **Step 4: Commit archive changes**

```bash
git add archive/ STRATEGY_DEVELOPMENT.md INDIAN_MARKET_GUIDE.md
git commit -m "docs: archive old monolithic documentation files"
```

---

## Task 14: Verification and Testing

**Files:**
- Test: All markdown files

- [ ] **Step 1: Verify all files under 200 lines**

```bash
find docs/ strategies/ -name "*.md" -exec wc -l {} \; | awk '$1 > 200 {print "ERROR: "$2" has "$1" lines (exceeds 200)"}'
```

Expected: No output (all files under 200 lines)

- [ ] **Step 2: Verify CLAUDE.md under 150 lines**

```bash
wc -l CLAUDE.md
```

Expected: Under 150 lines (hard limit: 180)

- [ ] **Step 3: Check for broken links (basic verification)**

```bash
# Extract all .md links and check if files exist
grep -rh "\](.*\.md)" docs/ strategies/README.md CLAUDE.md | grep -v "http" | sed 's/.*](\(.*\.md\)).*/\1/' | sort -u > /tmp/links.txt

# This is a manual verification step - review the links
cat /tmp/links.txt
```

- [ ] **Step 4: Verify directory structure**

```bash
tree -L 3 docs/ -I '__pycache__'
```

Expected structure:
```
docs/
├── backtesting/
│   ├── README.md
│   ├── architecture.md
│   └── creating_strategies.md
├── indian_markets/
│   ├── README.md
│   ├── circuit_breakers.md
│   ├── events.md
│   ├── liquidity.md
│   ├── risk_management.md
│   ├── trading_hours.md
│   └── volatility.md
├── quick_start/
│   ├── common_commands.md
│   ├── development_workflow.md
│   └── market_essentials.md
├── strategy_development/
│   ├── README.md
│   ├── backtesting.md
│   ├── implementation.md
│   ├── optimization.md
│   ├── parameter_design.md
│   ├── research_selection.md
│   └── validation.md
└── superpowers/
    ├── plans/
    └── specs/
```

- [ ] **Step 5: Test lazy loading behavior (conceptual check)**

Verify CLAUDE.md:
1. Contains only essential guidance (~150 lines)
2. Links to detailed docs (doesn't embed full content)
3. Provides clear navigation to topics

```bash
grep -c "docs/" CLAUDE.md
```

Expected: 10+ links to docs/ directories

- [ ] **Step 6: Final commit**

```bash
git add .
git commit -m "docs: complete documentation restructuring with verification

- All files under 200 lines
- CLAUDE.md lean (~150 lines)
- Hierarchical structure with lazy loading
- Bidirectional navigation
- Cross-references updated"
```

---

## Completion Criteria

- [ ] All markdown files ≤ 200 lines
- [ ] CLAUDE.md ≤ 150 lines (hard limit: 180)
- [ ] 21 new documentation files created
- [ ] 3 old files archived
- [ ] Directory structure matches spec
- [ ] All internal links functional
- [ ] Navigation footers added to detailed docs
- [ ] strategies/README.md consolidated
- [ ] Git history shows 14 focused commits
- [ ] No broken links (basic verification passed)

---

## Notes

**Content Extraction Strategy:**
- Use text editor or scripting to extract sections from original files
- Preserve all code examples, tables, and formatting
- Add context headers and navigation footers to each new file
- Verify line counts after each split

**Line Count Flexibility:**
- Target line counts are guidelines
- Accept ±10 lines variance (e.g., ~150 lines = 140-160 acceptable)
- Hard limit: 200 lines (no exceptions)
- CLAUDE.md hard limit: 180 lines (target: 150)

**Navigation Footer Template:**
```markdown
---
**Navigation:**
[← Previous](previous.md) | [README](README.md) | [Next →](next.md)

**Related:** [Quick Start](../quick_start/xxx.md) | [Topic](../dir/topic.md)
```

**Commit Message Format:**
- Use conventional commits: `docs: <description>`
- Keep messages concise and descriptive
- One logical change per commit (e.g., all phase files in one commit)

---

## APPENDIX: Content Extraction Guidance

### Source File Line Ranges

**From STRATEGY_DEVELOPMENT.md (579 lines) → docs/strategy_development/:**
- Lines 1-50: Overview → README.md
- Lines 51-150: Phase 1 → research_selection.md
- Lines 151-250: Phase 2 → parameter_design.md
- Lines 251-350: Phase 3 → implementation.md
- Lines 351-420: Phase 4 → backtesting.md
- Lines 421-500: Phase 5 → optimization.md
- Lines 501-579: Phase 6 → validation.md

**From INDIAN_MARKET_GUIDE.md (451 lines) → docs/indian_markets/:**
- Lines 1-40: Market Hours → trading_hours.md
- Lines 41-88: Liquidity → liquidity.md
- Lines 89-148: Circuit Breakers → circuit_breakers.md
- Lines 149-197: Volatility → volatility.md
- Lines 198-247: Events → events.md
- Lines 248-390: Risk + Sector → risk_management.md

**From CLAUDE.md (314 lines):**
- Lines 1-50: Overview → New CLAUDE.md (condensed)
- Lines 201-314: Backtesting → docs/backtesting/README.md

### Extraction Commands

Use `sed` to extract line ranges:
```bash
# Example: Extract Phase 1 from STRATEGY_DEVELOPMENT.md
sed -n '51,150p' STRATEGY_DEVELOPMENT.md > temp_phase1.txt
```

### File Structure Template

Every extracted file should follow this structure:

```markdown
# [Title]

> Part of [Parent Guide](README.md) - [Context]

## Overview
[1-2 paragraphs]

[Original content with subsections]

---
**Navigation:**
[← Previous](prev.md) | [README](README.md) | [Next →](next.md)

**Related:** [Quick Start](../quick_start/xxx.md)
```

### README Template (Tasks 5, 7, 9)

```markdown
# [Topic] Guide

[Overview paragraph]

## [Section 1]
[2-3 sentence summary]
[Full guide →](file1.md)

## [Section 2]
[2-3 sentence summary]
[Full guide →](file2.md)

[Repeat for all sections]

---
**Navigation:**
[CLAUDE.md](../../CLAUDE.md) | [Related](../other/README.md)
```

### Task 10: New CLAUDE.md Structure

Target: ~150 lines with these sections:

1. Header (3 lines)
2. Project Overview (3 paragraphs, ~10 lines)
3. Quick Links (bullet list, ~10 lines)
4. Project Structure (directory tree, ~15 lines)
5. Core Concepts (4-5 paragraphs with links, ~20 lines)
6. Development Setup (commands, ~10 lines)
7. Configuration (.env example, ~8 lines)
8. Key Dependencies (bullet list, ~10 lines)
9. Documentation Index (organized list, ~25 lines)

Extract content from current CLAUDE.md lines 1-150, condensing verbose sections and adding links to new detailed docs.

---

## APPENDIX: Implementation Guidance for Content Extraction Tasks

### Overview

Tasks 5-10 involve extracting and reorganizing content from existing markdown files. This appendix provides specific line ranges from source files and content structure templates to ensure consistent implementation.

### Source File Line Ranges (from Spec)

**From STRATEGY_DEVELOPMENT.md (579 lines):**
- Lines 1-50: Overview → `docs/strategy_development/README.md`
- Lines 51-150: Phase 1 → `docs/strategy_development/research_selection.md`
- Lines 151-250: Phase 2 → `docs/strategy_development/parameter_design.md`
- Lines 251-350: Phase 3 → `docs/strategy_development/implementation.md`
- Lines 351-420: Phase 4 → `docs/strategy_development/backtesting.md`
- Lines 421-500: Phase 5 → `docs/strategy_development/optimization.md`
- Lines 501-579: Phase 6 → `docs/strategy_development/validation.md`

**From INDIAN_MARKET_GUIDE.md (451 lines):**
- Lines 1-40: Market Hours → `docs/indian_markets/trading_hours.md`
- Lines 41-88: Liquidity → `docs/indian_markets/liquidity.md`
- Lines 89-148: Circuit Breakers → `docs/indian_markets/circuit_breakers.md`
- Lines 149-197: Volatility → `docs/indian_markets/volatility.md`
- Lines 198-247: Events → `docs/indian_markets/events.md`
- Lines 248-390: Risk Management + Sector → `docs/indian_markets/risk_management.md`
- Lines 391-451: Checklist → `docs/indian_markets/README.md` (references section)

**From CLAUDE.md (314 lines):**
- Lines 1-50: Project Overview → New `CLAUDE.md` (condensed)
- Lines 51-150: Structure → New `CLAUDE.md`
- Lines 151-200: Commands → `docs/quick_start/common_commands.md` (already created in Task 4)
- Lines 201-314: Backtesting → `docs/backtesting/README.md`

### Content Structure Template (Apply to All New Files)

**Header Pattern:**
```markdown
# [Title]

> Part of [Parent Guide](README.md) - [Context if applicable]

## Overview
[1-2 paragraphs introducing this topic]
```

**Body Pattern:**
- Organize into clear subsections (##, ###)
- Preserve all code examples from source
- Preserve all tables and lists
- Add context where needed for standalone readability

**Footer Pattern:**
```markdown
---
**Navigation:**
[← Previous](previous.md) | [README](README.md) | [Next →](next.md)

**Related:** [Quick Start](../quick_start/xxx.md) | [Related Topic](../dir/related.md)
```

### README File Template

```markdown
# [Topic] Guide

[1-2 paragraph overview]

## [Section 1]
[2-3 sentence summary]
[Full guide →](filename1.md)

## [Section 2]
[2-3 sentence summary]
[Full guide →](filename2.md)

[Repeat for all subsections]

## Quick Reference
[Key numbers, critical rules, or quick facts table]

---
**Navigation:**
[CLAUDE.md](../../CLAUDE.md) | [Related Guide](../other/README.md)
```

### New CLAUDE.md Template (Task 10)

```markdown
# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

SimpleTrader is a Python-based algorithmic trading bot for Indian equity markets (NSE/BSE). 
Supports Nubra and Upstox broker APIs with a complete backtesting framework based on Backtrader.

## Quick Links

- **Getting Started**: [Development Workflow](docs/quick_start/development_workflow.md)
- **Strategy Development**: [Strategy Development Guide](docs/strategy_development/README.md)
- **Indian Markets**: [Market Essentials](docs/quick_start/market_essentials.md) | [Full Guide](docs/indian_markets/README.md)
- **Backtesting**: [System Architecture](docs/backtesting/README.md)
- **Commands**: [Common Commands](docs/quick_start/common_commands.md)

## Project Structure

```
SimpleTrader/
├── main.py                    # Entry point
├── apis/                      # Broker API handlers (Nubra, Upstox)
├── strategies/                # Strategy templates and implementations
├── backtesting/              # Data scraper, backtest runner
├── dashboard/                # Streamlit UI
├── docs/                     # Documentation (see Quick Links)
└── data/                     # Historical OHLCV data (CSV)
```

## Core Concepts

**Broker APIs**: Nubra (production) and Upstox for market data and order placement

**Backtesting System**: Backtrader-based framework
- Strategies inherit from `bt.Strategy`
- BacktestRunner orchestrates execution
- Performance metrics: Sharpe, drawdown, win rate, P&L
- [Full details →](docs/backtesting/README.md)

**Indian Market Specifics**:
- Trading hours: 9:30 AM - 3:30 PM IST
- Min liquidity: 5 lakh daily volume
- Risk limits: Max 3% per trade, -5% daily loss
- [Full guide →](docs/indian_markets/README.md)

## Development Setup

```bash
# Activate virtual environment
source venv/Scripts/activate  # Git Bash

# Install dependencies
pip install -r requirements.txt

# Launch dashboard (recommended)
streamlit run dashboard/streamlit_app.py
```

## Configuration

Create `.env` file with broker credentials:
```
NUBRA_CLIENT_ID="your_client_id"
NUBRA_MPIN="your_mpin"
UPSTOX_ACCESS_TOKEN="your_token"
```

## Key Dependencies

- **backtrader**: Strategy backtesting framework
- **streamlit**: Web dashboard UI
- **nubra-sdk**: Nubra broker API
- **upstox-python-sdk**: Upstox broker API
- **pandas**: Data manipulation

## Documentation Index

**Quick Start (5-minute orientation):**
- [Development Workflow](docs/quick_start/development_workflow.md)
- [Market Essentials](docs/quick_start/market_essentials.md)
- [Common Commands](docs/quick_start/common_commands.md)

**Detailed Guides:**
- [Strategy Development Process](docs/strategy_development/README.md)
- [Indian Market Trading Guide](docs/indian_markets/README.md)
- [Backtesting System](docs/backtesting/README.md)
- [Creating Strategies](docs/backtesting/creating_strategies.md)
- [Strategy Templates](strategies/README.md)
```

### Extraction Process (For Tasks 5-10)

**Step-by-step approach:**

1. **Read source file section** (use line ranges above)
   ```bash
   sed -n '51,150p' STRATEGY_DEVELOPMENT.md
   ```

2. **Copy content to new file**
   - Preserve all formatting, code blocks, tables
   - Add header with title and context note
   - Organize into clear subsections if not already
   - Add footer navigation

3. **Verify standalone readability**
   - Does it make sense without the parent file?
   - Are all code examples complete?
   - Are references updated?

4. **Check line count**
   ```bash
   wc -l docs/path/to/file.md
   ```
   Should be under 200 lines

5. **Commit**

### Critical Files to Prioritize

1. **New CLAUDE.md** (Task 10) - Most important, loads first
2. **README files** (Tasks 5, 7, 9) - Navigation hubs
3. **Quick Start files** (Tasks 2-4) - Already complete with heredocs
4. **Detailed content files** (Tasks 6, 8) - Follow structure template

### Note on Manual Extraction

Tasks 5-10 require manual content extraction because:
- Source files are large (579, 451, 314 lines)
- Content needs reorganization, not just splitting
- Context headers and navigation footers must be added
- Line count constraints require editorial decisions
- Complete heredocs for all 18 files would make plan >3000 lines

The line ranges, structure templates, and extraction process above provide sufficient guidance for consistent implementation.

