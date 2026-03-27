# Documentation Restructuring Design

**Date:** 2026-03-26
**Status:** Approved
**Goal:** Restructure SimpleTrader documentation into hierarchical, lazy-loading system with no file exceeding 200 lines

---

## Problem Statement

Current documentation state:
- **STRATEGY_DEVELOPMENT.md**: 579 lines
- **INDIAN_MARKET_GUIDE.md**: 451 lines
- **strategies/README.md**: 293 lines
- **CLAUDE.md**: 314 lines
- **Total**: 1,637 lines in monolithic files

**Issues:**
1. Claude Code loads 1600+ lines on every session start
2. Difficult to navigate and find specific information
3. All files exceed 200-line target for focused documentation
4. No lazy-loading - everything is eager-loaded

**Requirements:**
- No MD file exceeds 200 lines
- Hierarchical structure with lazy loading
- Brief summaries in parent files with links to child documents
- CLAUDE.md stays lean (<150 lines) as entry point

---

## Solution Overview

**Approach:** Quick Start + Deep Dive hybrid structure

- **CLAUDE.md**: Lean guidance (~150 lines) with navigation links
- **docs/quick_start/**: Condensed actionable guides (3 files, ~400 lines total)
- **docs/strategy_development/**: Detailed workflow (7 files, ~970 lines total)
- **docs/indian_markets/**: Market reference (8 files, ~790 lines total)
- **docs/backtesting/**: System documentation (3 files, ~450 lines total)
- **strategies/README.md**: Consolidated template guide (~180 lines)

**Benefits:**
- Initial context load: ~150 lines (CLAUDE.md only) vs 1600+ lines
- On-demand loading of relevant docs
- Easy navigation via TOC structure
- Scalable for future additions

---

## Directory Structure

```
SimpleTrader/
├── CLAUDE.md (~150 lines)
│
├── docs/
│   ├── quick_start/
│   │   ├── development_workflow.md (~150 lines)
│   │   ├── market_essentials.md (~150 lines)
│   │   └── common_commands.md (~100 lines)
│   │
│   ├── strategy_development/
│   │   ├── README.md (~150 lines)
│   │   ├── research_selection.md (~180 lines)
│   │   ├── parameter_design.md (~150 lines)
│   │   ├── implementation.md (~120 lines)
│   │   ├── backtesting.md (~100 lines)
│   │   ├── optimization.md (~150 lines)
│   │   └── validation.md (~120 lines)
│   │
│   ├── indian_markets/
│   │   ├── README.md (~100 lines)
│   │   ├── trading_hours.md (~120 lines)
│   │   ├── liquidity.md (~100 lines)
│   │   ├── circuit_breakers.md (~120 lines)
│   │   ├── volatility.md (~120 lines)
│   │   ├── risk_management.md (~150 lines)
│   │   └── events.md (~80 lines)
│   │
│   ├── backtesting/
│   │   ├── README.md (~150 lines)
│   │   ├── architecture.md (~120 lines)
│   │   └── creating_strategies.md (~180 lines)
│   │
│   └── superpowers/
│       └── specs/
│           └── 2026-03-26-doc-restructure-design.md (this file)
│
└── strategies/
    ├── README.md (~180 lines)
    └── templates/ (unchanged)
```

---

## CLAUDE.md Restructuring

### New Structure (~150 lines)

**Sections:**
1. **Project Overview** (2-3 paragraphs)
   - What is SimpleTrader
   - Broker APIs supported (Nubra, Upstox)
   - Core capabilities

2. **Quick Links** (bullet list)
   - Development Workflow
   - Strategy Development Guide
   - Market Essentials
   - Backtesting System
   - Common Commands

3. **Project Structure** (directory tree with brief descriptions)

4. **Core Concepts** (4-5 paragraphs)
   - Broker abstraction
   - Backtesting system
   - Indian market specifics
   - Each links to detailed docs

5. **Development Setup** (commands only)
   - Venv activation
   - Dependency installation
   - Dashboard launch

6. **Configuration** (.env example)

7. **Key Dependencies** (bullet list with one-line descriptions)

8. **Documentation Index** (organized list of all doc links)

### Content Moved Out
- Detailed backtesting architecture → `docs/backtesting/README.md`
- Strategy development workflow → `docs/strategy_development/README.md`
- Indian market specifics → `docs/indian_markets/README.md`
- Detailed commands → `docs/quick_start/common_commands.md`

### Design Principle
CLAUDE.md is a "control panel" - quick orientation + navigation pointers. Future Claude instances load this fast (~150 lines) and navigate to specific topics as needed (lazy loading).

---

## Quick Start Documentation

**Purpose:** Condensed actionable guides for fast comprehension (5-minute read)

### development_workflow.md (~150 lines)

**Content:**
- Setup section (environment, deps, config)
- Strategy Development phases (2-3 bullets each + link to full guide)
  - Research & Selection
  - Parameter Design
  - Implementation (code snippet)
  - Backtesting (command + metrics)
  - Optimization (checklist)
  - Validation checklist
- Common Commands (top 5-7 only)
- Links to detailed guides

### market_essentials.md (~150 lines)

**Content:**
- Trading Hours (main session + avoid times + best windows table)
- Liquidity Requirements (min volume, position limits, stock selection)
- Circuit Breakers (critical info: levels, impact, strategy adaptation)
- Risk Management Rules (max per trade, position, daily limits)
- High-Impact Events (RBI, Budget, Elections)
- Quick Reference Table (condensed metrics)
- Links to detailed guides

### common_commands.md (~100 lines)

**Content:**
- Dashboard commands
- Testing strategies (quick backtest command + via dashboard)
- Data scraping (single equity + batch)
- Authentication testing
- Development commands (venv, deps)
- Troubleshooting section

**Design Principle:**
- Actionable: Commands you can run immediately
- Condensed: 2-3 bullets per topic
- Linked: Every section links to full guide
- Time-optimized: Read all 3 in ~5 minutes

---

## Detailed Documentation Structure

### docs/strategy_development/ (~970 lines total, 7 files)

**README.md (~150 lines)**
- Overview: 6-phase workflow description
- Process Phases: Brief summary (2-3 sentences) + link per phase
- Success Criteria: Checklist (Sharpe, drawdown, win rate, etc.)
- Quick Start link

**Phase Files (~120-180 lines each):**
- `research_selection.md`: Market regimes, strategy types, indicator selection, timeframe guidance
- `parameter_design.md`: Entry/exit conditions, position sizing, risk management, filters (time/volume/volatility)
- `implementation.md`: Strategy class structure, indicator initialization, trading logic patterns, code examples
- `backtesting.md`: Data selection (1+ year), running backtests, interpreting metrics, dashboard usage
- `optimization.md`: Parameter sensitivity testing, walk-forward validation, overfitting prevention, stress testing
- `validation.md`: Performance checklist, robustness criteria, deployment readiness, final verification

**Content Organization Per Phase File:**
- Brief intro (context within workflow)
- Main content organized into subsections
- Code examples where applicable
- Footer navigation: Previous Phase | README | Next Phase
- Related links: Quick Start, Indian Markets, Backtesting

### docs/indian_markets/ (~790 lines total, 8 files)

**README.md (~100 lines)**
- Market overview (NSE/BSE context)
- Topics list with brief description + link per topic
- Key numbers summary
- Quick Start link

**Topic Files (~80-150 lines each):**
- `trading_hours.md`: Pre-market, main session, closing; best windows table; session characteristics; time filters for strategies
- `liquidity.md`: Stock selection criteria (large/mid/small cap), position limits formula, volume filters, examples
- `circuit_breakers.md`: Stock-level circuits (±5/10/20%), index-level circuits (-10/-15/-20%), halt mechanics, strategy impact, detection code
- `volatility.md`: Intraday ranges by cap size, weekly patterns table, seasonal volatility, ATR reference values, strategy adaptation
- `risk_management.md`: Position sizing formulas, stop loss rules (ATR-based), account limits, daily/weekly/monthly review process, sector correlations
- `events.md`: Scheduled events (RBI, Budget, Elections, Earnings, Rebalancing), unscheduled events (global shocks), detection methods, impact levels

**Content Organization Per Topic File:**
- Brief intro (why this topic matters)
- Main content with subsections
- Tables for quick reference
- Code examples for strategy implementation
- Footer navigation: README | Related Topics
- Quick Start link

### docs/backtesting/ (~450 lines total, 3 files)

**README.md (~150 lines)**
- System architecture diagram (text format)
- Components overview (Strategy Framework, Backtest Runner, Data Scraper, Dashboard)
- Quick example (basic backtest code)
- Performance metrics explanation
- Links to detailed docs

**Detailed Files:**
- `architecture.md` (~120 lines): Component design, data flow, metrics calculation, BacktestRunner API, analyzer configuration
- `creating_strategies.md` (~180 lines): Strategy class structure, Backtrader concepts, indicator usage patterns, entry/exit logic examples, common mistakes, testing workflow

**Content Organization:**
- Architecture follows system design
- Creating strategies is practical/tutorial style
- Both link back to README and strategy_development/

### strategies/README.md (~180 lines)

**Content:**
- Available templates (3 templates with descriptions)
- Using templates section
- Creating custom strategies (consolidated from guides/)
- Parameter tuning guidelines
- Common mistakes
- Testing checklist
- Cross-reference to `docs/strategy_development/` and `docs/backtesting/creating_strategies.md`

**Changes:**
- Remove content that duplicates `docs/strategy_development/`
- Consolidate guides/ content into main README
- Keep focused on templates and quick usage
- Link to detailed workflow docs

---

## Content Migration Strategy

### Content Mapping

**From STRATEGY_DEVELOPMENT.md (579 lines):**
- Lines 1-50 (Overview) → `docs/strategy_development/README.md`
- Lines 51-150 (Phase 1) → `docs/strategy_development/research_selection.md`
- Lines 151-250 (Phase 2) → `docs/strategy_development/parameter_design.md`
- Lines 251-350 (Phase 3) → `docs/strategy_development/implementation.md`
- Lines 351-420 (Phase 4) → `docs/strategy_development/backtesting.md`
- Lines 421-500 (Phase 5) → `docs/strategy_development/optimization.md`
- Lines 501-579 (Phase 6) → `docs/strategy_development/validation.md`
- Key excerpts → `docs/quick_start/development_workflow.md`

**From INDIAN_MARKET_GUIDE.md (451 lines):**
- Lines 1-40 (Market Hours) → `docs/indian_markets/trading_hours.md`
- Lines 41-88 (Liquidity) → `docs/indian_markets/liquidity.md`
- Lines 89-148 (Circuit Breakers) → `docs/indian_markets/circuit_breakers.md`
- Lines 149-197 (Volatility) → `docs/indian_markets/volatility.md`
- Lines 198-247 (Events) → `docs/indian_markets/events.md`
- Lines 248-307 (Risk Management) → `docs/indian_markets/risk_management.md`
- Lines 308-390 (Sector/Tax) → `docs/indian_markets/risk_management.md` (sector section)
- Lines 391-451 (Checklist/Resources) → `docs/indian_markets/README.md`
- Critical excerpts → `docs/quick_start/market_essentials.md`

**From CLAUDE.md (314 lines):**
- Lines 1-50 (Project Overview) → New `CLAUDE.md` (condensed)
- Lines 51-150 (Project Structure) → New `CLAUDE.md`
- Lines 151-200 (Commands) → `docs/quick_start/common_commands.md`
- Lines 201-314 (Backtesting System) → `docs/backtesting/README.md`

**From strategies/README.md (293 lines):**
- Keep as consolidated file (~180 lines after removing redundancy)
- Remove content duplicating `docs/strategy_development/`
- Add cross-references to detailed docs

### Migration Workflow

**Phase 1: Create Directory Structure**
```bash
mkdir -p docs/quick_start
mkdir -p docs/strategy_development
mkdir -p docs/indian_markets
mkdir -p docs/backtesting
```

**Phase 2: Create Placeholder Files**
- Create all README.md files with TOC structure
- Ensures navigation works before content migration
- Allows testing link structure early

**Phase 3: Migrate Content by Topic**
- Split each source file into target files
- Preserve code examples, tables, formatting
- Add cross-references and navigation links
- Verify line counts stay under 200

**Phase 4: Create Quick Start Files**
- Extract key points from detailed docs
- Write condensed versions with links to full content
- Ensure actionable commands and examples

**Phase 5: Rewrite CLAUDE.md**
- Use new structure as foundation
- Add documentation index with links
- Verify ~150 line count

**Phase 6: Update Cross-References**
- Find all internal links in markdown files
- Update paths to new locations
- Add bidirectional navigation links

**Phase 7: Archive Old Files**
```bash
mkdir -p archive/
mv STRATEGY_DEVELOPMENT.md archive/
mv INDIAN_MARKET_GUIDE.md archive/
mv CLAUDE.md archive/CLAUDE.md.old
```

### Content Transformation Rules

**When splitting content:**
1. **Preserve all information** - don't lose content, just reorganize
2. **Add context headers** - each file self-contained with brief intro
3. **Include navigation** - every file links to parent README and related topics
4. **Maintain code examples** - keep working code snippets intact
5. **Update references** - change "see below" to proper file links

**Transformation Example:**
```markdown
# Before (in STRATEGY_DEVELOPMENT.md)
## Phase 1: Research & Selection
[200 lines of content]

# After (in docs/strategy_development/research_selection.md)
# Research & Selection

> Part of [Strategy Development Workflow](README.md) - Phase 1 of 6

## Overview
This phase identifies market regime and selects appropriate strategy type.

[Content organized into subsections]

## Next Steps
Continue to [Phase 2: Parameter Design](parameter_design.md)

---
**Navigation:**
[README](README.md) | [Next Phase →](parameter_design.md)

**Related:** [Quick Start](../quick_start/development_workflow.md) | [Indian Markets](../indian_markets/README.md)
```

---

## Cross-References & Navigation

### Link Patterns

**Bidirectional Navigation:**
Every detailed doc links back to:
- Parent README
- Related quick start
- Related topics

**Footer Navigation Pattern:**
```markdown
---
**Navigation:**
[← Previous](previous.md) | [README](README.md) | [Next →](next.md)

**Related:** [Quick Start](../quick_start/xxx.md) | [Topic Y](../other/related.md)
```

### Link Update Strategy

**Find all markdown links:**
```bash
grep -r "\[.*\](.*.md)" *.md docs/ strategies/
```

**Update patterns:**
- `STRATEGY_DEVELOPMENT.md` → `docs/strategy_development/README.md`
- `INDIAN_MARKET_GUIDE.md` → `docs/indian_markets/README.md`
- `strategies/README.md` → Keep same (relative paths in nested docs use `../`)

**Verify links:**
```bash
find docs/ -name "*.md" -exec grep -l "\](.*\.md)" {} \;
```

### Documentation Discovery Paths

**Path 1: Quick Start (Fastest - 5 minutes)**
```
CLAUDE.md → docs/quick_start/development_workflow.md
          → docs/quick_start/market_essentials.md
          → docs/quick_start/common_commands.md
```
Total: ~400 lines

**Path 2: Deep Dive from Quick Start**
```
docs/quick_start/development_workflow.md
  → docs/strategy_development/README.md
  → docs/strategy_development/research_selection.md
```

**Path 3: Topic-Specific**
```
CLAUDE.md → docs/indian_markets/README.md
          → docs/indian_markets/circuit_breakers.md
```

**Path 4: Implementation-Focused**
```
CLAUDE.md → docs/backtesting/README.md
          → docs/backtesting/creating_strategies.md
          → strategies/README.md
```

---

## Maintenance Guidelines

### Adding New Content

**If new doc exceeds 200 lines:**
1. Split into subtopics following same pattern
2. Create parent README with TOC
3. Add bidirectional navigation links

**Integration checklist:**
- Add link to relevant parent README TOC
- Add footer navigation to related docs
- Update quick_start if critical information
- Verify line count under 200

### Updating Existing Content

**After editing:**
1. Check line count still under 200
2. If exceeded, split into subtopics
3. Preserve navigation footer pattern
4. Update cross-references if structure changes

### Deprecating Content

**Process:**
1. Don't delete immediately - move to `archive/deprecated/`
2. Add deprecation notice in old location with link to replacement
3. Remove after one version cycle (or when no longer referenced)

---

## Verification Checklist

After migration complete:

- [ ] All new files under 200 lines
- [ ] CLAUDE.md under 150 lines
- [ ] No broken internal links
- [ ] All code examples tested and working
- [ ] Quick start files link to detailed docs
- [ ] Detailed docs link back to quick start
- [ ] README files have complete TOC
- [ ] Old files archived (not deleted)
- [ ] Git commit with descriptive message
- [ ] Documentation builds without errors
- [ ] Navigation paths tested (all links clickable)

**Testing:**
```bash
# Check line counts
find docs/ -name "*.md" -exec wc -l {} \; | awk '$1 > 200 {print $0}'
wc -l CLAUDE.md  # Should be ~150

# Check for broken links (basic)
grep -r "\](.*\.md)" docs/ | grep -v "http" | cut -d: -f2 | sed 's/.*(\(.*\.md\)).*/\1/' | sort -u

# Verify files exist
ls -lR docs/
```

---

## Benefits Summary

### For Claude Code
- **Initial load**: ~150 lines (CLAUDE.md only) vs 1600+ lines (current)
- **Context efficiency**: 10x+ reduction in initial context consumption
- **On-demand loading**: Navigate to relevant docs only when needed
- **Better comprehension**: Focused single-topic documents easier to process
- **Faster orientation**: Quick start docs provide overview in 5 minutes

### For Human Developers
- **Fast navigation**: Find specific information via clear TOC structure
- **No scrolling**: No more 500-line files to search through
- **Progressive disclosure**: Quick start → detailed guide path
- **Easy updates**: Modify single topics without affecting others
- **Better search**: File names and directory structure aid discovery

### For Project Maintenance
- **Modular updates**: Change one topic without cascading effects
- **Clear separation**: Each file has single, well-defined purpose
- **Scalable structure**: Add new guides without bloating existing files
- **Better version control**: Git diffs show precise changes per topic
- **Reduced merge conflicts**: Changes less likely to overlap

---

## Implementation Notes

### File Size Targets
- **CLAUDE.md**: ~150 lines (hard limit: 180)
- **README.md**: ~100-150 lines
- **Quick start**: ~100-150 lines per file
- **Detailed docs**: ~100-180 lines per file
- **Maximum**: 200 lines (no exceptions)

### Navigation Overhead
- Footer navigation: ~3-5 lines per file
- Header context: ~2-3 lines per file
- Total overhead: ~5-8 lines per file
- Acceptable trade-off for improved navigation

### Content Density
- Preserve all information from original files
- Organize into logical subsections
- Use tables and lists for quick scanning
- Include code examples inline (not separate files)

### Lazy Loading Verification
After implementation:
1. Start fresh Claude Code session
2. Verify only CLAUDE.md loaded initially
3. Ask topic-specific question
4. Confirm Claude reads only relevant doc(s)
5. Check context window usage

---

## Success Criteria

**Structural:**
- ✅ All markdown files ≤ 200 lines
- ✅ CLAUDE.md ≤ 150 lines
- ✅ Clear hierarchical organization
- ✅ Bidirectional navigation links
- ✅ No broken internal references

**Functional:**
- ✅ Claude Code lazy-loads documentation
- ✅ Quick start provides 5-minute orientation
- ✅ Detailed docs accessible via clear paths
- ✅ All original content preserved
- ✅ Code examples remain functional

**Quality:**
- ✅ Each file has single, clear purpose
- ✅ Navigation intuitive (parent → child → sibling)
- ✅ Content searchable via file structure
- ✅ Maintainable for future updates
- ✅ Scalable for new content addition

---

## Conclusion

This restructuring transforms SimpleTrader documentation from monolithic files (1600+ lines) into a hierarchical, lazy-loading system optimized for both Claude Code context efficiency and human navigation. The Quick Start + Deep Dive hybrid approach balances fast orientation with comprehensive reference material, ensuring documentation serves both casual exploration and deep implementation work.

**Next Steps:** Create detailed implementation plan via writing-plans skill.
