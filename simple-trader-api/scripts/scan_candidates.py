"""
Daily ATH scan routine - Step A + B.

Scrapes both Chartink screeners and takes the union (all stocks appearing
in either), then enriches each symbol with market cap tier and precise
price/ATH figures from tradingview-cli.

Does not touch chartink_scraper.py's existing union/dedup behavior
(scrape_both_screeners), which the existing candidates web UI relies on.
Instead calls scrape_single_screener() twice and unions here.

Usage:
    python scripts/scan_candidates.py [YYYY-MM-DD]
"""
import json
import logging
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.chartink_scraper import ChartinkScraper
from app.services.tradingview_cli import tradingview_cli
from scripts.paths import work_dir

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def scrape_all_symbols() -> list:
    scraper = ChartinkScraper()

    result_a = scraper.scrape_single_screener("within-2-52week")
    if result_a["errors"]:
        raise RuntimeError(f"Screener 'within-2-52week' failed: {result_a['errors']}")
    if getattr(scraper, "last_scrape_incomplete", False):
        raise RuntimeError("Screener 'within-2-52week' paging ended early - refusing to use a partial list")

    result_b = scraper.scrape_single_screener("stage-2-trend")
    if result_b["errors"]:
        raise RuntimeError(f"Screener 'stage-2-trend' failed: {result_b['errors']}")
    if getattr(scraper, "last_scrape_incomplete", False):
        raise RuntimeError("Screener 'stage-2-trend' paging ended early - refusing to use a partial list (new stocks would be missed)")

    symbols_a = {s["symbol"] for s in result_a["stocks"]}
    symbols_b = {s["symbol"] for s in result_b["stocks"]}
    union = sorted(symbols_a | symbols_b)

    logger.info(
        f"within-2-52week: {len(symbols_a)} stocks, "
        f"stage-2-trend: {len(symbols_b)} stocks, "
        f"common: {len(symbols_a & symbols_b)}, "
        f"union: {len(union)}"
    )
    return union


def enrich_with_market_cap(symbols: list) -> list:
    candidates = []
    for symbol in symbols:
        info = tradingview_cli.get_stock_info(symbol)
        if info is None:
            logger.warning(f"No TradingView data for {symbol}, marking cap_size=unknown")
            candidates.append({
                "symbol": symbol,
                "cap_size": "unknown",
                "market_cap_cr": None,
                "current_price": None,
                "all_time_high": None,
            })
            continue

        candidates.append({
            "symbol": symbol,
            "cap_size": info["cap_size"],
            "market_cap_cr": info["market_cap_cr"],
            "current_price": info["current_price"],
            "all_time_high": info["all_time_high"],
        })
    return candidates


def main():
    all_symbols = scrape_all_symbols()
    if not all_symbols:
        logger.warning("No candidates today - nothing to scan.")
        candidates = []
    else:
        candidates = enrich_with_market_cap(all_symbols)

    today = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()  # run_daily.py passes the session date
    output_path = os.path.join(work_dir(today), "candidates.json")
    with open(output_path, "w") as f:
        json.dump(candidates, f, indent=2)

    logger.info(f"Wrote {len(candidates)} candidates to {output_path}")
    print(output_path)
    return output_path


if __name__ == "__main__":
    main()
