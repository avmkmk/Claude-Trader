# SimpleTrader — Project History

Compiled 2026-10-03 (Phase 6 added 2026-10-05) from git history, the specs/plans in `docs/superpowers/`, and every README/CLAUDE.md found in the repo. Remote: `https://github.com/avmkmk/Claude-Trader.git` (renamed from `SmartTrader-NSE-BSE`; the old URL redirects, and the original name appears in the archived README).

## Timeline

### Phase 1 — Multi-strategy trading framework (2026-03-27 → 2026-03-29)
- `4ae138f` Initial commit: algorithmic trading framework for NSE/BSE (Backtrader strategies, Nubra and Upstox broker handlers in `apis/`).
- `f969071` Added a React web app (`simple-trader-web`), a FastAPI backend (`simple-trader-api`), a Gemini AI chat, news feeds and extensive docs.
- `bac8d1d` Removed `node_modules` and results from tracking.

### Phase 2 — ATH Reclaim backtesting (2026-04-03 → 2026-04-04)
- Added a Nifty 300 stock list and data validator, a `CapitalManager` (monthly capital injection, position sizing), the `ath_reclaim_daily_v1` Backtrader strategy (state machine, entry/exit), batch and portfolio backtest runners.
- `041d0e0` / `b497a86` "Ruthless" repository cleanup: unused strategies and scripts removed, leaving `ath_reclaim_daily_v1`, `sma_crossover`, `rsi_mean_reversion_india`, `ema_crossover`.
- `3f8e282` (2026-04-04) is the **last commit on the GitHub remote**.

### Phase 3 — ATH monitoring web workflow (2026-04-13 → 2026-04-17, local only)
- Spec `2026-04-13-ath-monitoring-design.md`: manual Chartink scraping (Selenium) → candidates → watchlist → `ATHAnalyzer` phase labels ("Phase 3 (Entry)", "Approaching Phase 3", …).
- Spec/plan `2026-04-14-daily-data-pipeline-*`: parallel EOD data updater for NIFTY 750 via the Nubra API (gap detection, SQLite metadata, retry with backoff, file locking). Built as `simple-trader-api/lib/*` and `update_daily_data.py`, with a data-pipeline doc (`README_DATA_PIPELINE.md`). Merged via `feature/daily-data-pipeline`.
- Nubra TOTP authenticator login, unified watchlist with data-freshness and source tracking, `Array.isArray` crash fixes on the frontend pages.

### Phase 4 — Daily ATH scan routine (2026-08-11 → 2026-08-18)
- Design `2026-08-11-daily-ath-scan-routine-design.md`: a Claude-driven daily routine. It scrapes two Chartink screeners (`within-2-of-52-week-highs-chartitude`, `stage-2-trend-template`) and intersects them. It then segregates by market-cap tier, drives the **live TradingView Desktop chart** over CDP to read the `ath-reclaim-pinecone.txt` Pine strategy's state, and writes a dated Excel watchlist. Deliberately does not use local EOD CSVs, which go stale.
- Revision 2026-08-18 + plan `2026-08-18-daily-ath-scan-recheck.md`: `build_check_list.py` re-checks every tracked Reclaimed/Approaching symbol each day. Fixes to `update_symbol_state.py` (cap-tier preservation, no clobbering tracked entries). Packaged as the `/daily-ath-scan` skill.

### Phase 5 — Pivot to a single-strategy signal pipeline (2026-08-18)
- Spec/plan `2026-08-18-signal-pipeline-selection-*`: stop being a multi-broker web app. Target pipeline: technical scan → ranked selection → Telegram delivery → fundamentals. Only scan and ranking are built; **Telegram delivery and fundamentals are not**.
- `66e6f2c` deleted the scrapped web UI (`simple-trader-web`) and the dead routers. `628993b` vendored `tradingview-mcp-jackson` (TradingView CDP/MCP bridge) into the repo.
- `4c12b80` fixed strategy detection (`isTVScriptStrategy`), `04a8c4a` added `ranking.js`, `fc3831b` made `scan_step_c.mjs` pull win-rate / profit-factor / held-entry price, `fdd2289` ranks the Excel watchlist, `cd26a6e` tracks `tradingview_cli.py`, the Pine source and `.mcp.json`.

### Phase 6 — Cleanup, fundamentals, and a fully automated daily routine (2026-10-03 → 2026-10-05)
**Cleanup and onboarding (10-03)**
- `6c71597` removed everything the daily ATH scan does not use (backtesting, broker APIs, strategies, the FastAPI app, the data-update pipeline, vendored MCP docs/CLI): about 184 tracked files down to about 84. All markdown was preserved first (`b86b78d`: `docs/PROJECT_HISTORY.md`, `docs/SETUP.md`, `docs/archive/`).
- `506305f` added a SessionStart **preflight** (`scripts/preflight.ps1`): every new Claude session checks Git, Python 3.11+, Node 18+, Chrome, TradingView Desktop, `tradingview-cli`, the Python/npm packages and the `.mcp.json` path, and reports install commands for anything missing. `cb60e29` documented that TradingView must be launched with `launch_tv_debug.ps1` (remote-debugging port 9222) so Claude can control it. `4e955b4` gitignored all scan data.

**Fundamental analysis (10-05)**
- `docs/FUNDAMENTAL_RULES.md` defines automatable gates over a stock's screener.in page: eligibility, survival/red flags (debt, interest cover, cash conversion, other income), quality (ROCE, ROE, margins, working capital), growth, valuation (peer P/E, PEG), ownership, and balance-sheet strength; plus a Gate 7 for news and government stance. `b6418d4` implemented the rules engine and screener.in runner; banks, NBFCs and insurers are routed out as FINANCIAL.
- `16e06d0` made the rules **tier-aware**: below Rs 250 Cr is a hard reject; Rs 250-1,000 Cr uses stricter small-cap thresholds and a PASS is capped at WATCH; Rs 1,000-5,000 Cr uses the small-cap profile; Rs 5,000 Cr and above is standard.
- `ecb87b5` and `4a7601f` put the results in the daily Excel: verdict/score/block-score columns on page 1 and **one sheet per stock** (verdict banner, key figures, a 3-4 line summary, every rule as Check / Value / Result), with the symbol on page 1 hyperlinked to its sheet and a link back.

**Automation (10-05)**
- `7d20275` added `run_daily.py` (the pure-script runner: stale check, lock, log, status, `symbol_state.json` backup, resume with `--from-step`), `trading_calendar.py` plus `config/nse_holidays.json`, and `register_daily_task.ps1`. Watchlists are stamped with the **last completed NSE session**, so a post-close run and a pre-open run are the same watchlist. The Windows scheduled task `SimpleTrader-DailyATH` runs daily at 08:00, again at logon (so a late start still runs), and runs as soon as possible if missed.
- **Gate 7** (company news and government/industry stance via AI web search, tagged Bullish/Neutral/Bearish) lives in the `/daily-ath-scan` Claude command, not the script, and is merged into the Excel.
- The Excel became one clean, user-sortable table (no separator rows, real dates, filter dropdowns on every sheet). The Chartink screens are combined as a **union** so no stock is missed.
- First live runs exposed two reliability bugs, fixed in `105081f` and `e33e677`: the live TradingView read started before the chart had loaded (every symbol errored; it now waits for the chart and aborts without merging if most reads fail), and the Chartink scraper treated a stale element after a page change as the last page and silently returned about 40 of about 300 stocks (the button search now retries and any abnormal end of paging fails the run).
- `e33e677` also cleaned the data layout: `daily_scans/` holds only the consolidated `{date}_final_watchlist.xlsx` files; state, backups and logs live in `data/state/`, per-run intermediates in `data/work/{stamp}/` (pruned after 3 days), and `scripts/paths.py` is the single source of truth. Legacy layouts migrate themselves by moving files.
- The repository was renamed to `Claude-Trader` (`origin` updated; docs updated in `93080d2`).

## Final state at time of writing (2026-10-05)
- `origin/main` (`https://github.com/avmkmk/Claude-Trader.git`) is in sync with local `main`.
- 71 Python tests and 8 Node tests pass. The scheduled task is registered; its first fully unattended run is due 2026-10-06 08:00 (stamped with the 2026-10-05 session). It was test-run once via the task on 2026-10-05 and completed successfully.
- Not built yet: Telegram delivery, promoter-pledging and liquidity checks, a financials ruleset for banks/NBFCs, and own-history P/E. Headless scheduling of the Claude command (`register_daily_task.ps1 -Mode Claude`) is untested. Gate 7 is not part of the scheduled script run, so each unattended watchlist shows Gate 7 as pending until `/daily-ath-scan` is run.
- The 2026 NSE holiday list was compiled from published summaries and should be verified against nseindia.com.

## Where the original markdown lives
Every markdown file existing before cleanup is preserved in `docs/superpowers/` (specs/plans, unchanged) and `docs/archive/` (copies of the data-pipeline README and the vendored `tradingview-mcp-jackson` docs, skills and agents).
