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

## Daily run
1. Open Claude Code in the repo and type `/daily-ath-scan`. The skill is `.claude/skills/daily-ath-scan/SKILL.md`.
2. It runs, in order: `scan_candidates.py` (Chartink + enrich), `build_check_list.py`, TradingView launch via `launch_tv_debug.ps1` (CDP on port 9222, see above), `scan_step_c.mjs` (live Pine read), `update_symbol_state.py`, `build_final_watchlist.py`.
3. Output: `simple-trader-api/data/daily_scans/{date}_final_watchlist.xlsx`. Persistent state is `symbol_state.json` in the same folder (gitignored, so back it up yourself); `manual_exclusions.json` lists symbols to always skip.

## Optional: TradingView MCP tools in Claude
`.mcp.json` registers the `tradingview-desktop` MCP server (`tradingview-mcp-jackson/src/server.js`). Edit the absolute path in it to match your clone location.

## Tests
```bash
cd simple-trader-api && python -m pytest tests/ -v
cd ../tradingview-mcp-jackson && node --test tests/ranking.test.js
```
