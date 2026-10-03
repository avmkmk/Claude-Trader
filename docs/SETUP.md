# Setup — running the Daily ATH Scan from scratch

Everything a new machine needs to run the `/daily-ath-scan` routine in Claude Code (desktop app or CLI): Chartink scrape, live TradingView read, and the dated Excel watchlist. See `docs/PROJECT_HISTORY.md` for why it is built this way.

## Prerequisites
- Windows 10/11, Git, Python 3.11+, Node.js 18+, Google Chrome (Selenium scrapes Chartink with it).
- TradingView Desktop (Microsoft Store build) signed in to an account that can show the Pine strategy.
- Claude Code (desktop app or CLI) opened on this repo folder.

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

## One-time TradingView setup
1. Open TradingView Desktop, create a new Pine strategy, paste the contents of `ath-reclaim-pinecone.txt`, and save it. The saved name must be exactly `ATH Reclaim - Final Verified`.
2. Add it to the default chart template so it loads on every symbol (the routine reads its study values and labels directly).

## Daily run
1. Open Claude Code in the repo and type `/daily-ath-scan`. The skill is `.claude/skills/daily-ath-scan/SKILL.md`.
2. It runs, in order: `scan_candidates.py` (Chartink + enrich), `build_check_list.py`, TradingView launch via `tradingview-mcp-jackson/scripts/launch_tv_debug.ps1` (CDP on port 9222), `scan_step_c.mjs` (live Pine read), `update_symbol_state.py`, `build_final_watchlist.py`.
3. Output: `simple-trader-api/data/daily_scans/{date}_final_watchlist.xlsx`. Persistent state is `symbol_state.json` in the same folder (gitignored, so back it up yourself); `manual_exclusions.json` lists symbols to always skip.

## Optional: TradingView MCP tools in Claude
`.mcp.json` registers the `tradingview-desktop` MCP server (`tradingview-mcp-jackson/src/server.js`). Edit the absolute path in it to match your clone location.

## Tests
```bash
cd simple-trader-api && python -m pytest tests/ -v
cd ../tradingview-mcp-jackson && node --test tests/ranking.test.js
```
