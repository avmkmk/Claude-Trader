"""
Run the fundamental rules (docs/FUNDAMENTAL_RULES.md) over the latest daily ATH watchlist.

Usage (from simple-trader-api/):
    python scripts/fundamental_screen.py [watchlist.xlsx] [--delay 2.0] [--refresh]

Console check: reads the newest data/daily_scans/*_final_watchlist.xlsx (or the one given), fetches each
symbol's screener.in page (consolidated, falling back to standalone), caches the parsed data per day
under data/fundamentals/{date}/ and prints the verdicts. The Excel report with a sheet per symbol is
produced by build_final_watchlist.py, which calls screen_symbols() below.
"""
import argparse
import glob
import json
import os
import re
import sys
import time
from datetime import date

import requests
from bs4 import BeautifulSoup
from openpyxl import load_workbook

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.fundamental_rules import evaluate, summary_notes  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCANS_DIR = os.path.join(BASE, "data", "daily_scans")
CACHE_DIR = os.path.join(BASE, "data", "fundamentals")
HEADERS = {"User-Agent": "Mozilla/5.0 (personal research script)"}
TABLES = ["quarters", "profit-loss", "balance-sheet", "cash-flow", "ratios", "shareholding"]


def to_num(text):
    t = (text or "").replace(",", "").replace("%", "").replace("₹", "").replace("Cr.", "").strip()
    if t in ("", "-"):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def parse_table(section):
    table = section.find("table") if section else None
    if table is None:
        return None
    trs = table.find_all("tr")
    periods = [th.get_text(strip=True) for th in trs[0].find_all("th")][1:]
    rows = {}
    for tr in trs[1:]:
        cells = tr.find_all("td")
        if len(cells) < 2:
            continue
        name = re.sub(r"\s+", " ", cells[0].get_text(" ", strip=True)).replace("+", "").strip()
        rows[name] = [to_num(c.get_text(strip=True)) for c in cells[1:]]
    return {"periods": periods, "rows": rows}


def parse_peers_median_pe(html):
    soup = BeautifulSoup(html, "html.parser")
    trs = soup.find_all("tr")
    if not trs:
        return None
    heads = [c.get_text(" ", strip=True) for c in trs[0].find_all(["th", "td"])]
    if "P/E" not in heads:
        return None
    idx = heads.index("P/E")
    for tr in trs:
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
        if len(cells) > idx and cells[1:2] and cells[1].lower().startswith("median"):
            return to_num(cells[idx])
    return None


def parse_company_page(html, peers_html=None):
    """screener.in company page -> dict consumed by fundamental_rules.evaluate."""
    soup = BeautifulSoup(html, "html.parser")
    top = {}
    keymap = {"Market Cap": "market_cap", "Current Price": "price", "Stock P/E": "pe", "Book Value": "book",
              "Dividend Yield": "div_yield", "ROCE": "roce", "ROE": "roe"}
    for li in soup.select("#top-ratios li"):
        name = li.find(class_="name")
        val = li.find(class_="number")
        if name and val and name.get_text(strip=True) in keymap:
            top[keymap[name.get_text(strip=True)]] = to_num(val.get_text(strip=True))
    sector = {}
    peers = soup.find("section", id="peers")
    if peers:
        titles = {"Broad Sector": "broad", "Sector": "sector", "Broad Industry": "broad_industry", "Industry": "industry"}
        for a in peers.select("p.sub a"):
            if a.get("title") in titles:
                sector[titles[a.get("title")]] = a.get_text(strip=True)
    tables = {}
    for tid in TABLES:
        t = parse_table(soup.find("section", id=tid))
        if t:
            tables[tid] = t
    growth = {}
    for t in soup.select("table.ranges-table"):
        title = t.find("th").get_text(strip=True)
        growth[title] = {}
        for tr in t.find_all("tr")[1:]:
            if ":" in tr.get_text():
                label, val = tr.get_text(" ", strip=True).split(":", 1)
                growth[title][label.strip()] = to_num(val)
    wid = re.search(r'data-warehouse-id="(\d+)"', html)
    h1 = soup.find("h1")
    return {"name": h1.get_text(" ", strip=True) if h1 else None, "top": top, "sector": sector, "tables": tables, "growth": growth,
            "peers_median_pe": parse_peers_median_pe(peers_html) if peers_html else None,
            "warehouse_id": wid.group(1) if wid else None}


def http_get(url, extra=None, retries=3):
    for attempt in range(retries):
        r = requests.get(url, headers={**HEADERS, **(extra or {})}, timeout=30)
        if r.status_code == 429:
            time.sleep(10 * (attempt + 1))
            continue
        return r
    return r


def _usable(data):
    """(annual years, quarters) with real values - how much history a parsed page actually has."""
    pl = data["tables"].get("profit-loss", {})
    years = len([v for v in pl.get("rows", {}).get("Sales", []) if v is not None])
    qtrs = len([v for v in data["tables"].get("quarters", {}).get("rows", {}).get("Sales", []) if v is not None])
    return years, qtrs


def fetch_symbol(symbol, delay):
    """Return (parsed data, None) or (None, reason).

    Tries consolidated first. If its history is thin (< 5 years or < 5 quarters - empty or recently
    consolidated pages), also tries standalone and keeps whichever has more annual years.
    """
    candidates, last_err = [], "no financial tables"
    for suffix in ("/consolidated/", "/"):
        r = http_get(f"https://www.screener.in/company/{symbol}{suffix}")
        time.sleep(delay)
        if r.status_code == 404:
            last_err = "not found on screener.in"
            break
        if r.status_code != 200:
            last_err = f"HTTP {r.status_code}"
            break
        if 'id="profit-loss"' not in r.text:
            continue
        data = parse_company_page(r.text)
        data["symbol"], data["basis"] = symbol, "consolidated" if "consolidated" in suffix else "standalone"
        data["_html"] = r.text
        candidates.append(data)  # keep even if empty: banks/NBFCs have no "Sales" row but are routed by sector
        years, qtrs = _usable(data)
        if suffix == "/consolidated/" and years >= 5 and qtrs >= 5:
            break
    if not candidates:
        return None, last_err
    best = max(candidates, key=lambda c: (_usable(c)[0], c["basis"] == "consolidated"))
    html = best.pop("_html")
    for c in candidates:
        c.pop("_html", None)
    if best.get("warehouse_id"):
        pr = http_get(f"https://www.screener.in/api/company/{best['warehouse_id']}/peers/", {"X-Requested-With": "XMLHttpRequest"})
        time.sleep(delay)
        if pr.status_code == 200:
            best["peers_median_pe"] = parse_peers_median_pe(pr.text)
    return best, None


def latest_watchlist():
    files = sorted(glob.glob(os.path.join(SCANS_DIR, "*_final_watchlist.xlsx")))
    if not files:
        sys.exit("No *_final_watchlist.xlsx found in data/daily_scans/")
    return files[-1]


def read_watchlist(path):
    ws = load_workbook(path, data_only=True).active
    header = [c.value for c in ws[1]]
    out = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        rec = dict(zip(header, row))
        if rec.get("Symbol") and rec.get("Status"):
            out.append(rec)
    return header, out


def screen_symbols(symbols, delay=2.0, refresh=False, log=print, cache_date=None):
    """Fetch (cached per day) and evaluate each symbol. Returns {symbol: summary}.

    summary = {verdict, score, blocks, hard_fails, flags, industry, basis, results}
    Never raises for a single bad symbol: failures become verdict "NO DATA".
    """
    cache_dir = os.path.join(CACHE_DIR, cache_date or date.today().isoformat())
    os.makedirs(cache_dir, exist_ok=True)
    out = {}
    for i, sym in enumerate(symbols, 1):
        cache = os.path.join(cache_dir, f"{sym}.json")
        data, err = None, None
        if os.path.exists(cache) and not refresh:
            with open(cache, encoding="utf-8") as f:
                data = json.load(f)
        else:
            try:
                data, err = fetch_symbol(sym, delay)
            except requests.RequestException as e:
                err = f"network error: {e}"
            if data:
                with open(cache, "w", encoding="utf-8") as f:
                    json.dump(data, f)
        if data is None:
            res = {"verdict": "NO DATA", "score": None, "blocks": {}, "results": [], "hard_fails": [err]}
        else:
            res = evaluate(data)
        flags = [f'{r["id"]}: {r["msg"]}' for r in res["results"] if r["level"] == "fail"] +                 [f'{r["id"]}: {r["msg"]}' for r in res["results"] if r["level"] == "warn"]
        out[sym] = {**res, "flags": flags, "industry": (data or {}).get("sector", {}).get("industry"),
                    "basis": (data or {}).get("basis"), "top": (data or {}).get("top", {}),
                    "name": (data or {}).get("name")}
        out[sym]["notes"] = summary_notes(out[sym], out[sym]["top"], out[sym]["basis"])
        log(f"[{i}/{len(symbols)}] {sym:12s} {res['verdict']:9s} {res['score'] if res['score'] is not None else '':>5}  {'; '.join(res['hard_fails'])[:90]}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("watchlist", nargs="?")
    ap.add_argument("--delay", type=float, default=2.0)
    ap.add_argument("--refresh", action="store_true", help="ignore today's cache")
    args = ap.parse_args()

    path = args.watchlist or latest_watchlist()
    header, rows = read_watchlist(path)
    print(f"Watchlist: {os.path.basename(path)} ({len(rows)} symbols)")
    screened = screen_symbols([r["Symbol"] for r in rows], args.delay, args.refresh)
    tally = {}
    for summ in screened.values():
        tally[summ["verdict"]] = tally.get(summ["verdict"], 0) + 1
    print("Summary:", ", ".join(f"{k}={v}" for k, v in sorted(tally.items())))


if __name__ == "__main__":
    main()
