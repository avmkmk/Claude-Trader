---
name: daily-ath-scan
description: Run the daily ATH Reclaim routine end to end - the pure-script scan (Chartink union -> live TradingView Pine read -> fundamentals -> Excel watchlist with a sheet per stock) PLUS Gate 7 (AI web search on company news and government/industry stance) and send the Excel. Use when the user asks to run the daily ATH scan, refresh the watchlist, check today's candidates, or add the news/policy check to the latest watchlist.
---

# Daily ATH Scan (Claude command)

Two ways to run the same routine:
- **Pure script** (no Claude, scheduled by Windows Task Scheduler): `python scripts/run_daily.py` in `simple-trader-api/`. Produces the watchlist Excel with technical + fundamental columns.
- **This command**: runs that same script, then adds **Gate 7** - web research that only an AI session can do - and rebuilds the Excel with it.

Design: `docs/superpowers/specs/2026-08-11-daily-ath-scan-routine-design.md`, rules: `docs/FUNDAMENTAL_RULES.md`, setup/scheduling: `docs/SETUP.md`.

## Key idea: the watchlist stamp
Files are stamped with the **last completed NSE session date** (not the calendar date): a run after the close and a run the next morning before the open are the same watchlist. `{stamp}` below is that date. Holidays come from `simple-trader-api/config/nse_holidays.json`.

## Steps (all commands run from `simple-trader-api/`)

1. **Is a run needed?**
   ```bash
   python scripts/run_daily.py --check-only
   ```
   Prints `CURRENT` (exit 0) or `RUN NEEDED` (exit 10), the newest watchlist date, the expected session, and whether Gate 7 is done. If the market is open the signals are provisional (today's bar is still forming) - say so.
   - `CURRENT` and the user did not ask for a refresh: skip to step 3 using the newest watchlist's date as `{stamp}`.
   - Otherwise (or if the user asks to refresh), go to step 2.

2. **Run the scan** (long - run it in the background and poll `data/state/run_status.json` and the newest file in `data/state/logs/`):
   ```bash
   python scripts/run_daily.py            # add --force to refresh a current watchlist
   ```
   It performs, in order: prerequisites check; Chartink scrape (**union** of both screeners, so nothing is missed) + enrichment; build the check list (new candidates + every tracked Reclaimed/Approaching symbol); relaunch TradingView with remote debugging if CDP is not up (the script closes any open TradingView window - that is accepted); read the live Pine strategy per symbol (slowest step, seconds per symbol); back up and merge `symbol_state.json`; build `{stamp}_final_watchlist.xlsx` with fundamentals. Report the counts it prints (`new=N re-checked=M`, Reclaimed/Approaching, fundamental tally). If it fails, the status file names the step: fix the cause and resume with `--from-step N`.

3. **Gate 7 - news and government stance (this is the part that needs you).** Read `data/work/{stamp}/gate7_targets.json` (the PASS/WATCH survivors: symbol, name, industry, verdict, score). For each target:
   - **Company news** - WebSearch `"<name> NSE <symbol> news"` (look at roughly the last 30 days): earnings and guidance, order wins/losses, capex/M&A, management or auditor changes, promoter stake/pledge actions, credit-rating actions, litigation or regulatory action.
   - **Government / industry stance** - WebSearch the target's `industry` in India (e.g. `"<industry> India government policy duty subsidy PLI regulation <month year>"` and `"<industry> India demand outlook"`): budget and policy moves, tariffs/duties, PLI/subsidies, regulation, RBI/SEBI actions, commodity or demand trends. Targets in the same industry share one industry search.
   - Classify each as **Bullish** (clear net positive developments / policy tailwind), **Neutral** (mixed, or nothing material found) or **Bearish** (net negative). No evidence means Neutral - say "No material news found". Never invent headlines, dates or URLs; use only what the searches returned.
   - Write `data/work/{stamp}/gate7.json`:
     ```json
     {"SYMBOL": {"news_sentiment": "Bullish|Neutral|Bearish",
                 "policy_sentiment": "Bullish|Neutral|Bearish",
                 "summary": "2-3 plain sentences: what is happening and why it matters, with dates.",
                 "headlines": [{"title": "...", "source": "...", "date": "YYYY-MM-DD", "url": "https://..."}],
                 "checked_on": "YYYY-MM-DD"}}
     ```
   Gate 7 is advisory: it never changes the numeric verdict. Call out conflicts (a PASS with Bearish news, a WATCH with a clear policy tailwind).

4. **Rebuild the Excel with Gate 7** (fast: fundamentals are cached for the stamp):
   ```bash
   python scripts/build_final_watchlist.py {stamp} data/daily_scans/{stamp}_final_watchlist.xlsx
   ```
   Adds News Sentiment / Policy Stance / News & Policy Note columns on the Watchlist sheet and a "News and policy" section on each symbol's sheet.

5. **Report and send.** Summarize: candidates scraped, new vs re-checked, Reclaimed/Approaching counts, fundamental tally, the PASS names with their news and policy tags, any conflicts. Send `data/daily_scans/{stamp}_final_watchlist.xlsx` to the user.

## Workbook (for reference)
- **Watchlist** sheet: one clean table, filter/sort dropdowns on every column (the user does all sorting; default order is Reclaimed then Approaching by distance). Clicking a symbol jumps to its sheet.
- **One sheet per symbol**: verdict banner, key figures, a 3-4 line summary, Gate 7 section, and every rule as a filterable Check / Value / Result / Gate table, with a link back.

## Notes
- First-ever run: a missing `symbol_state.json` is treated as empty; every candidate is `new`.
- Symbols you want excluded permanently live in `data/state/manual_exclusions.json`.
- If the live Pine read fails partway, its rejection cache (`data/state/_rejection_cache.json`) means already-processed `skip` verdicts are not re-driven for 3 days; just resume.
- `symbol_state.json` is backed up before every merge to `data/state/backups/` (newest 14 kept). `data/daily_scans/` holds only the consolidated Excel files; intermediates live in `data/work/{stamp}/` and are pruned after 3 days.
- Telegram delivery is planned but not built; the file is delivered by this command / opened by the scheduled run.
