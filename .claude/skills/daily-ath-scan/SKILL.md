---
name: daily-ath-scan
description: Run the daily ATH Reclaim scan routine - scrapes Chartink screeners, re-checks already-tracked Reclaimed/Approaching symbols against the live TradingView chart, and rebuilds the dated watchlist Excel. Use when the user asks to run the daily ATH scan, refresh the ATH reclaim watchlist, or check today's chartink candidates.
---

# Daily ATH Scan Routine

Full design: `docs/superpowers/specs/2026-08-11-daily-ath-scan-routine-design.md` — read this first if anything below is unclear, especially the "Revision (2026-08-18)" section this skill packages.

Runs Steps A/B/A2/C/D end to end: scrape Chartink → enrich with market cap/price → build today's live-check list (new candidates + already-tracked Reclaimed/Approaching symbols) → read live Pine strategy state off the TradingView desktop chart → rebuild the dated watchlist Excel.

## Steps

`{today}` is today's date as `YYYY-MM-DD`.

1. **Scrape + enrich (Step A+B)** — from `simple-trader-api/`:
   ```bash
   python scripts/scan_candidates.py
   ```
   Produces `data/daily_scans/{today}_candidates.json`.

2. **Build today's check list (Step A2)** — from `simple-trader-api/`:
   ```bash
   python scripts/build_check_list.py data/daily_scans/{today}_candidates.json data/daily_scans/{today}_to_check.json
   ```
   Prints `new=N re-checked=M total=T`. `re-checked` is every symbol currently `reclaimed` or `approaching` in `symbol_state.json` — report this count to the user before the live step, since it drives how long Step 4 takes.

3. **Ensure TradingView Desktop is running with CDP.** Check first:
   ```bash
   curl -s http://localhost:9222/json/version
   ```
   If that fails, launch it (from the repo root):
   ```bash
   powershell -ExecutionPolicy Bypass -File "tradingview-mcp-jackson/scripts/launch_tv_debug.ps1"
   ```
   Wait for the script to report `CDP ready`.

4. **Live Pine state read (Step C)** — from `tradingview-mcp-jackson/`, using **absolute paths** into `simple-trader-api/data/daily_scans/` since this runs from a different directory:
   ```bash
   node scan_step_c.mjs "<repo-root>/simple-trader-api/data/daily_scans/{today}_to_check.json" "<repo-root>/simple-trader-api/data/daily_scans/{today}_verdicts.json"
   ```
   Drives the TradingView chart via CDP for every symbol in the check list — no computer-use, no screenshots, it reads Pine's own study values and labels directly. Produces `{today}_verdicts.json` and `{today}_verdicts_details.json`. This is the slow step — expect roughly a few seconds per symbol.

5. **Merge into persistent state** — from `simple-trader-api/`:
   ```bash
   python scripts/update_symbol_state.py data/daily_scans/{today}_verdicts_details.json data/daily_scans/{today}_candidates.json {today}
   ```
   Updates `data/daily_scans/symbol_state.json` in place. Prints the new total symbol count.

6. **Build the watchlist Excel** — from `simple-trader-api/`:
   ```bash
   python scripts/build_final_watchlist.py {today} data/daily_scans/{today}_final_watchlist.xlsx
   ```
   Reads the *entire* `symbol_state.json` (not just today's touched symbols), so anything that flipped to `skip` during today's re-check (e.g. a stop-out) is automatically excluded. Prints Reclaimed/Approaching counts.

   It also runs the **fundamental screen** (`scripts/fundamental_screen.py`, rules in `docs/FUNDAMENTAL_RULES.md`) on every row: fetches each symbol's screener.in page (cached per day; allow ~3-5 min on a fresh list) and adds Fundamental Verdict (PASS / WATCH / REJECT / FINANCIAL / NO DATA), score, block scores, industry and a one-line Key Note to page 1. Every stock also gets its **own sheet named after the symbol** (verdict banner, key figures, a 3-4 line summary, and every rule as Check / Value / Result); clicking a symbol on the Watchlist sheet jumps to it, and each sheet has a link back. Pass `--no-fundamentals` to skip it, `--refresh-fundamentals` to ignore today's cache. If the fundamental step fails, the technical watchlist is still written with blank fundamental columns.

7. **Report and send.** Summarize: candidates scraped, new vs re-checked counts, final Reclaimed/Approaching counts, and the fundamental verdict tally (PASS/WATCH/REJECT) with the PASS names. Send the Excel file at `simple-trader-api/data/daily_scans/{today}_final_watchlist.xlsx` to the user.

## Notes

- If Step 2 reports `re-checked=0` and this is the very first run (`symbol_state.json` doesn't exist yet), `build_check_list.py` treats a missing state file as empty — every candidate is `new`. This is expected, not an error.
- Symbols manually excluded from the watchlist live in `simple-trader-api/data/daily_scans/manual_exclusions.json` — unaffected by this routine.
- If Step 4 fails partway through, its rejection cache (`_rejection_cache.json`, written next to the verdicts output) means already-processed `skip` verdicts won't be re-driven against the live chart again for 3 days on a re-run — safe to just re-run Step 4 with the same input file.
