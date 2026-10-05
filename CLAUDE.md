# CLAUDE.md

Guidance for Claude Code in this repository.

## Project Overview

SimpleTrader is now a single-purpose pipeline: the **Daily ATH Scan** for Indian equities (NSE/BSE). It scrapes Chartink, enriches candidates, reads the live "ATH Reclaim - Final Verified" Pine strategy off the TradingView Desktop chart over CDP, ranks them, and writes a dated Excel watchlist. Run it with the `/daily-ath-scan` skill.

History of how it got here: `docs/PROJECT_HISTORY.md`. Install and run instructions: `docs/SETUP.md`.

## Session start (do this first, every session)

A SessionStart hook (`.claude/settings.json` -> `scripts/preflight.ps1`) prints a prerequisite report at the top of the session. Before anything else:

1. Tell the user the result in a short list: what is installed, and what is missing with its install command (Git, Python 3.11+, Node.js 18+, Chrome, TradingView Desktop via Microsoft Store, `tradingview-cli`, Python packages, `tradingview-mcp-jackson` npm install, `.mcp.json` path).
2. If the hook output is absent, run `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/preflight.ps1` yourself.
3. If anything is missing, offer to install it (ask before running installs), then re-run the preflight until it says `all prerequisites present`.
4. TradingView must be launched with `tradingview-mcp-jackson/scripts/launch_tv_debug.ps1` (CDP port 9222), never opened normally. First-time users also need to sign in and add the Pine strategy; follow `docs/SETUP.md`.
5. The report also has a `Daily watchlist:` line (from `run_daily.py --check-only`): tell the user whether the newest watchlist is CURRENT or a run is needed, and whether Gate 7 (news/government stance) is done or pending. The watchlist is stamped with the last completed NSE session, so a post-close and a pre-open run are the same watchlist.
6. Once everything is present, offer `/daily-ath-scan` (runs the script if a run is needed, then does Gate 7 web research). Do not start the scan until prerequisites pass.

## Structure

```
.claude/skills/daily-ath-scan/   # the skill that runs the whole routine
ath-reclaim-pinecone.txt         # Pine strategy source (paste into TradingView)
simple-trader-api/
  scripts/                       # run_daily (pure-script runner), scan_candidates, build_check_list, update_symbol_state,
                                 # build_final_watchlist, fundamental_rules/_screen/_sheets, trading_calendar
  config/nse_holidays.json       # NSE holidays used to stamp watchlists with the last completed session
  app/services/                  # chartink_scraper.py, tradingview_cli.py
  tests/                         # pytest (run from simple-trader-api/)
  data/daily_scans/              # gitignored: ONLY the consolidated {date}_final_watchlist.xlsx files (stocks + fundamentals + news/policy)
  data/state/                    # symbol_state.json, manual_exclusions.json, _rejection_cache.json, run_status.json, backups/, logs/
  data/work/{stamp}/             # per-run intermediates (candidates, verdicts, gate7*.json); auto-pruned after 3 days
  data/archive/                  # spreadsheets moved out of daily_scans/ (never auto-deleted); paths are defined in scripts/paths.py
tradingview-mcp-jackson/         # vendored TradingView CDP bridge; scan_step_c.mjs is the live-scan step
docs/                            # PROJECT_HISTORY.md, SETUP.md, superpowers/ specs+plans, archive/
.mcp.json                        # tradingview-desktop MCP server (edit the absolute path per machine)
```

## Daily routine (two ways)
- Script: `cd simple-trader-api && python scripts/run_daily.py` (add `--force`, `--check-only`, `--from-step N`); scheduled with `scripts/register_daily_task.ps1`.
- Claude: `/daily-ath-scan` = the same script + Gate 7 (web search for company news and government stance), written to `data/work/{stamp}/gate7.json` and merged into the Excel.
- Excel sheets are plain filterable tables; never hard-sort or merge cells inside a table (the user sorts).

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
