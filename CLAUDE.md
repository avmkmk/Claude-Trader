# CLAUDE.md

Guidance for Claude Code in this repository.

## Project Overview

SimpleTrader is now a single-purpose pipeline: the **Daily ATH Scan** for Indian equities (NSE/BSE). It scrapes Chartink, enriches candidates, reads the live "ATH Reclaim - Final Verified" Pine strategy off the TradingView Desktop chart over CDP, ranks them, and writes a dated Excel watchlist. Run it with the `/daily-ath-scan` skill.

History of how it got here: `docs/PROJECT_HISTORY.md`. Install and run instructions: `docs/SETUP.md`.

## Structure

```
.claude/skills/daily-ath-scan/   # the skill that runs the whole routine
ath-reclaim-pinecone.txt         # Pine strategy source (paste into TradingView)
simple-trader-api/
  scripts/                       # scan_candidates, build_check_list, update_symbol_state, build_final_watchlist
  app/services/                  # chartink_scraper.py, tradingview_cli.py
  tests/                         # pytest (run from simple-trader-api/)
  data/daily_scans/              # gitignored: daily outputs, symbol_state.json, manual_exclusions.json
tradingview-mcp-jackson/         # vendored TradingView CDP bridge; scan_step_c.mjs is the live-scan step
docs/                            # PROJECT_HISTORY.md, SETUP.md, superpowers/ specs+plans, archive/
.mcp.json                        # tradingview-desktop MCP server (edit the absolute path per machine)
```

## Commands

```bash
cd simple-trader-api && python -m pytest tests -v
cd tradingview-mcp-jackson && node --test tests/ranking.test.js
```

## Notes

- Design: `docs/superpowers/specs/2026-08-11-daily-ath-scan-routine-design.md` and `2026-08-18-signal-pipeline-selection-design.md`.
- Planned but not built: Telegram delivery of the top 5 picks, and fundamentals enrichment.
- `symbol_state.json` is gitignored persistent state; back it up.
- Removed in the 2026 cleanup (still in git history): backtesting engine, broker APIs, FastAPI app, React frontend, data-update pipeline.
