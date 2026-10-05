# SimpleTrader — Project History

Compiled 2026-10-03 from git history (`origin/main` + 48 local commits), the specs/plans in `docs/superpowers/`, and every README/CLAUDE.md found in the repo. Remote: `https://github.com/avmkmk/Claude-Trader.git` (renamed from `SmartTrader-NSE-BSE`; the old URL redirects, and the original name appears in the archived README).

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

## Final state at time of writing
- Remote `main` is 48 commits behind local `main` (nothing from April 13 onward is on GitHub).
- One uncommitted change: `simple-trader-api/scripts/build_final_watchlist.py` removes the ranking sort (`combined_rank` first) and sorts by `abs(distance_pct)` only. This reverts the behaviour of commit `fdd2289`; confirm it is intentional before committing.

## Where the original markdown lives
Every markdown file existing before cleanup is preserved in `docs/superpowers/` (specs/plans, unchanged) and `docs/archive/` (copies of the data-pipeline README and the vendored `tradingview-mcp-jackson` docs, skills and agents).
