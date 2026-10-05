# Setup — running the Daily ATH Scan from scratch

Everything a new machine needs to run the `/daily-ath-scan` routine in Claude Code (desktop app or CLI): Chartink scrape, live TradingView read, and the dated Excel watchlist. See `docs/PROJECT_HISTORY.md` for why it is built this way.

## Prerequisites
- Windows 10/11, Git, Python 3.11+, Node.js 18+, Google Chrome (Selenium scrapes Chartink with it).
- TradingView Desktop (Microsoft Store build) signed in to an account that can show the Pine strategy.
- Claude Code (desktop app or CLI) opened on this repo folder.

## Automatic prerequisite check
Opening any Claude Code session in this repo runs `scripts/preflight.ps1` (via a SessionStart hook in `.claude/settings.json`). Claude then reports what is installed and what is missing, with install commands, and re-checks after fixing. You can run it by hand:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/preflight.ps1
```

## One-time install
```bash
git clone https://github.com/avmkmk/SmartTrader-NSE-BSE.git
cd SmartTrader-NSE-BSE
python -m venv venv
source venv/Scripts/activate            # Git Bash
pip install -r simple-trader-api/requirements.txt
cd tradingview-mcp-jackson && npm install && cd ..
npm install -g tradingview-mcp-server   # provides the `tradingview-cli` used for market cap / price lookups
```

## Launching TradingView so Claude can control it (required)
Claude drives TradingView Desktop through Chrome DevTools Protocol (CDP) on port 9222, which only works if the app was started with `--remote-debugging-port=9222`. **Opening TradingView normally (Start menu, taskbar, double-click) will not work**, and neither will a remote or Store-shell launch, because the flag is not forwarded. Always launch it with the script:

```powershell
powershell -ExecutionPolicy Bypass -File "tradingview-mcp-jackson/scripts/launch_tv_debug.ps1"
```

What it does:
1. Finds the Microsoft Store (MSIX) install with `Get-AppxPackage -Name "*TradingView*"` and locates `TradingView.exe`.
2. **Stops any running TradingView instance** (save your work first), so the flag takes effect.
3. Starts `TradingView.exe --remote-debugging-port=9222` and polls `http://localhost:9222/json/version` for up to ~40 s.
4. Prints `CDP ready at http://localhost:9222` on success.

Check it any time with `curl -s http://localhost:9222/json/version`. A JSON reply means Claude can connect. The `/daily-ath-scan` skill runs this check and calls the script if needed, but you can run it yourself first.

Troubleshooting:
- "TradingView package not found": install TradingView Desktop from the Microsoft Store (a plain .exe install isn't detected by this script).
- "CDP did not come up": the first cold start can be slow; wait and re-run the script.
- Use a different port with `-Port 9223`; the code in `tradingview-mcp-jackson/src/connection.js` expects 9222, so change it there too.
- The desktop session must be a normal interactive Windows login. A plain launch (including from a remote session) does not pass the debugging flag, so always use the script.

## One-time TradingView setup
1. Launch TradingView with the script above and sign in.
2. Create a new Pine strategy, paste the contents of `ath-reclaim-pinecone.txt`, and save it. The saved name must be exactly `ATH Reclaim - Final Verified`.
3. Add it to the default chart template so it loads on every symbol (the routine reads its study values and labels directly).

## Daily run: two ways, same routine
**A. Pure script (no Claude)** - from `simple-trader-api/`:
```bash
python scripts/run_daily.py              # runs only if the newest watchlist is older than the last completed session
python scripts/run_daily.py --force      # run regardless
python scripts/run_daily.py --check-only # CURRENT or RUN NEEDED (+ whether Gate 7 is done)
python scripts/run_daily.py --from-step 5  # resume after a failure
```
Steps: prerequisites -> Chartink scrape (**union** of both screeners) -> check list -> relaunch TradingView with CDP if needed -> live Pine read -> back up and merge `symbol_state.json` -> build the Excel (technical + fundamentals + a sheet per stock). Logs: `data/daily_scans/logs/`; status: `data/daily_scans/run_status.json`.

**B. Claude command** - open Claude Code in the repo and type `/daily-ath-scan`. It runs the same script, then does **Gate 7** (AI web search for company news and government/industry stance on the PASS/WATCH stocks), rebuilds the Excel with those columns and sends it. Gate 7 needs web search, so it lives in the Claude command, not in the script.

Output: `simple-trader-api/data/daily_scans/{stamp}_final_watchlist.xlsx`.

### Where files live (`simple-trader-api/data/`, all gitignored)
| Folder | What |
|---|---|
| `daily_scans/` | **Only** the consolidated Excel per session (`{date}_final_watchlist.xlsx`: stocks, fundamentals, news/policy). Nothing else is written here. |
| `state/` | Persistent state and bookkeeping: `symbol_state.json`, `manual_exclusions.json`, `_rejection_cache.json`, `run_status.json`, `backups/` (state snapshots, newest 14), `logs/` (run logs, 30 days). **Back up `state/`.** |
| `work/{stamp}/` | Per-run intermediates (candidates, check list, verdicts, Gate 7 inputs/outputs). Pruned automatically after 3 days. |
| `fundamentals/` | Parsed screener.in pages, cached per session date. Pruned after 3 days. |
| `archive/` | Any other spreadsheet found in `daily_scans/` is moved here (never deleted automatically). |

Older machines with everything inside `daily_scans/` are migrated automatically (files are moved, never deleted) the first time any script runs.

### The watchlist stamp (why running at 8 pm and at 8 am are the same)
The file date is the **last completed NSE session**, not the calendar date. After 16:00 IST on a trading day that is today; before 16:00, on weekends and on holidays it is the previous trading day. So a run after the close and a run the next morning before the open produce the same stamp, and the second one is skipped as already current. Holidays: `simple-trader-api/config/nse_holidays.json` (2026 list included; add next year's in December).

### Run it automatically (Windows Task Scheduler)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/register_daily_task.ps1            # daily 08:00 + at logon
powershell -ExecutionPolicy Bypass -File scripts/register_daily_task.ps1 -Time 07:45
powershell -ExecutionPolicy Bypass -File scripts/register_daily_task.ps1 -Status
powershell -ExecutionPolicy Bypass -File scripts/register_daily_task.ps1 -Remove
```
Three layers cover "I switched the PC on late": the 08:00 daily trigger; an **at-logon trigger** (3 min delay) that runs the moment you sign in; and **run-as-soon-as-possible-if-missed**. Each one first checks whether the newest watchlist is current and exits immediately if so, so double triggers are harmless. The job needs you logged on (TradingView is a desktop app) and relaunches TradingView with remote debugging, closing any open window. Keep the PC clock on IST. The Excel opens when the run finishes. Gate 7 is not part of the scheduled run; open Claude Code afterwards and the session-start report tells you if it is pending (`/daily-ath-scan` adds it).

### Using the Excel
Every sheet is a plain table with filter/sort dropdowns on each column; sort however you like (default order is Reclaimed then Approaching by distance from entry). Click a symbol on the Watchlist sheet to jump to its sheet; each stock sheet has a link back.

## Optional: TradingView MCP tools in Claude
`.mcp.json` registers the `tradingview-desktop` MCP server (`tradingview-mcp-jackson/src/server.js`). Edit the absolute path in it to match your clone location.

## Tests
```bash
cd simple-trader-api && python -m pytest tests/ -v
cd ../tradingview-mcp-jackson && node --test tests/ranking.test.js
```
