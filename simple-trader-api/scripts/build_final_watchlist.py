"""
Builds the dated watchlist Excel from the persistent symbol-state file:
Reclaimed first, then Approaching, each group sorted by closeness to the
entry price (smallest |distance| first).

Reclaimed stocks are filtered/sorted by distance from their ACTUAL entry
price (the RECLAIM bar's close), not the current ATH - the ATH keeps
ratcheting up while a position is held, so "close to ATH" does not mean
"close to entry" (e.g. WELCORP entered at 1005.5 in April, current price
1881 is +87% past entry despite sitting right at the current ATH).
Approaching stocks have no entry yet, so distance-from-ATH is the right
"how close to triggering" measure for them.

Each row also gets fundamental columns (verdict, score, block scores, hard fails,
warnings) from scripts/fundamental_screen.py - see docs/FUNDAMENTAL_RULES.md. That step
fetches screener.in pages (cached per day, ~2-4 min for a fresh list). If it fails, the
technical watchlist is still written with blank fundamental columns.

Usage:
    python scripts/build_final_watchlist.py <scan_date> <output_path> [--no-fundamentals] [--refresh-fundamentals]
"""
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

STATE_PATH = "data/daily_scans/symbol_state.json"
EXCLUSIONS_PATH = "data/daily_scans/manual_exclusions.json"

FUNDAMENTAL_HEADERS = [
    "Fundamental Verdict", "Fundamental Score", "Quality /30", "Growth /25", "Safety /20",
    "Valuation /15", "Ownership /10", "Industry", "Key Note",
]
VERDICT_FILLS = {"PASS": "C6EFCE", "WATCH": "FFEB9C", "REJECT": "FFC7CE", "FINANCIAL": "DDEBF7", "NO DATA": "D9D9D9"}

ENTRY_BAND_PCT = 5.0
CAP_LABELS = {"large": "Large Cap", "mid": "Mid Cap", "small": "Small Cap", "unknown": "Unknown"}


def load(path):
    with open(path) as f:
        return json.load(f)


def load_exclusions():
    try:
        return load(EXCLUSIONS_PATH)
    except FileNotFoundError:
        return {}


def compute_combined_rank(rows):
    eligible = [r for r in rows if r.get("ranking_eligible")]

    def dense_rank_by(key):
        # Ties share a rank (distinct sorted values, not list position) so
        # two symbols with identical metrics get an identical combined_rank.
        distinct_values = sorted({r[key] for r in eligible}, reverse=True)
        return {v: i for i, v in enumerate(distinct_values)}

    wr_rank = dense_rank_by("win_rate_pct")
    pf_rank = dense_rank_by("profit_factor")
    for r in rows:
        if r.get("ranking_eligible"):
            r["combined_rank"] = (wr_rank[r["win_rate_pct"]] + pf_rank[r["profit_factor"]]) / 2
        else:
            r["combined_rank"] = None


def key_note(summary):
    """One short line for page 1: the first hard fail, else the first warning (full detail is on the symbol's sheet)."""
    if summary["verdict"] == "FINANCIAL":
        return "Bank / NBFC / insurer - not scored"
    for text in list(summary.get("hard_fails") or []) + list(summary.get("flags") or []):
        text = text.split(": ", 1)[1] if ": " in text else text
        return text if len(text) <= 90 else text[:87] + "..."
    return ""


def fundamental_cells(summary):
    """Values for FUNDAMENTAL_HEADERS from a screen_symbols() summary (blank cells if None)."""
    if not summary:
        return [""] * len(FUNDAMENTAL_HEADERS)
    b = summary.get("blocks") or {}
    return [
        summary["verdict"], summary["score"], b.get("quality"), b.get("growth"), b.get("safety"),
        b.get("valuation"), b.get("ownership"), summary.get("industry") or "", key_note(summary),
    ]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if len(args) != 2 or not flags <= {"--no-fundamentals", "--refresh-fundamentals"}:
        print("Usage: python build_final_watchlist.py <scan_date> <output_path> [--no-fundamentals] [--refresh-fundamentals]")
        sys.exit(1)
    scan_date, output_path = args

    state = load(STATE_PATH)
    exclusions = load_exclusions()

    reclaimed_rows = []
    approaching_rows = []

    for symbol, r in state.items():
        if symbol in exclusions:
            continue
        cap_size = r.get("cap_size", "unknown")
        market_cap_cr = r.get("market_cap_cr")

        if r.get("verdict") == "reclaimed":
            dist = r.get("distance_from_entry_pct")
            if dist is None or abs(dist) > ENTRY_BAND_PCT:
                continue
            reclaimed_rows.append({
                "symbol": symbol, "status": "Reclaimed", "cap_size": cap_size,
                "market_cap_cr": market_cap_cr, "distance_pct": dist,
                "close": r.get("close"), "reference_price": r.get("entry_price"),
                "reference_label": "Entry Price", "ema200": r.get("ema200"),
                "win_rate_pct": r.get("win_rate_pct"), "profit_factor": r.get("profit_factor"),
                "total_trades": r.get("total_trades"), "ranking_eligible": r.get("ranking_eligible", False),
                "entry_date": r.get("entry_date"), "last_checked": r.get("last_checked"),
            })
        elif r.get("verdict") == "approaching":
            approaching_rows.append({
                "symbol": symbol, "status": "Approaching", "cap_size": cap_size,
                "market_cap_cr": market_cap_cr, "distance_pct": r.get("distance_pct"),
                "close": r.get("close"), "reference_price": r.get("absolute_ath"),
                "reference_label": "ATH (entry trigger)", "ema200": r.get("ema200"),
                "win_rate_pct": r.get("win_rate_pct"), "profit_factor": r.get("profit_factor"),
                "total_trades": r.get("total_trades"), "ranking_eligible": r.get("ranking_eligible", False),
                "entry_date": None, "last_checked": r.get("last_checked"),
            })

    compute_combined_rank(reclaimed_rows)
    compute_combined_rank(approaching_rows)

    def sort_key(r):
        return abs(r["distance_pct"])

    reclaimed_rows.sort(key=sort_key)
    approaching_rows.sort(key=sort_key)

    fundamentals = {}
    all_rows = reclaimed_rows + approaching_rows
    if "--no-fundamentals" not in flags and all_rows:
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # so `scripts.*` imports work when run as a script
            from scripts.fundamental_screen import screen_symbols
            from scripts.fundamental_sheets import add_symbol_sheet, link
            print(f"Running fundamental screen on {len(all_rows)} symbols (cached per day)...")
            fundamentals = screen_symbols([r["symbol"] for r in all_rows], refresh="--refresh-fundamentals" in flags)
        except Exception as e:  # never lose the technical watchlist over the fundamental step
            print(f"WARNING: fundamental screen failed ({type(e).__name__}: {e}); writing watchlist without fundamentals")

    sheet_names = {}
    if fundamentals:
        from scripts.fundamental_sheets import sheet_name
        used = ["Watchlist"]
        for r in all_rows:
            if r["symbol"] in fundamentals:
                sheet_names[r["symbol"]] = sheet_name(r["symbol"], used)
                used.append(sheet_names[r["symbol"]])

    wb = Workbook()
    ws = wb.active
    ws.title = "Watchlist"

    headers = [
        "Symbol", "Status", "Cap Tier", "Market Cap (cr)", "Distance from Entry %",
        "Current Price", "Reference Price", "Reference", "EMA 200",
        "Win Rate %", "Profit Factor", "Total Trades", "Combined Rank",
        *FUNDAMENTAL_HEADERS,
        "Entry Date", "Last Checked", "TradingView Link",
    ]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    row_idx = 2
    for label, group in [("Reclaimed", reclaimed_rows), ("Approaching", approaching_rows)]:
        if not group:
            continue
        header_cell = ws.cell(row=row_idx, column=1, value=label)
        header_cell.font = Font(bold=True)
        header_cell.fill = PatternFill("solid", fgColor="DDDDDD")
        row_idx += 1

        for r in group:
            fund = fundamental_cells(fundamentals.get(r["symbol"]))
            values = [
                r["symbol"], r["status"], CAP_LABELS.get(r["cap_size"], "Unknown"), r["market_cap_cr"],
                r["distance_pct"], r["close"], r["reference_price"], r["reference_label"], r["ema200"],
                r["win_rate_pct"], r["profit_factor"], r["total_trades"], r["combined_rank"],
                *fund,
                r["entry_date"] or "", r["last_checked"] or "",
                f"https://in.tradingview.com/chart/?symbol=NSE:{r['symbol']}",
            ]
            for col, v in enumerate(values, start=1):
                ws.cell(row=row_idx, column=col, value=v)
            if r["symbol"] in sheet_names:  # symbol -> its fundamental sheet
                link(ws.cell(row=row_idx, column=1), f"'{sheet_names[r['symbol']]}'!A1")
            verdict_col = headers.index("Fundamental Verdict") + 1
            if fund[0] in VERDICT_FILLS:
                ws.cell(row=row_idx, column=verdict_col).fill = PatternFill("solid", fgColor=VERDICT_FILLS[fund[0]])
            row_idx += 1

    for col_idx, header in enumerate(headers, start=1):
        wide = {"Key Note": 60, "Industry": 24}
        ws.column_dimensions[get_column_letter(col_idx)].width = wide.get(header, max(14, len(header) + 2))
    ws.freeze_panes = "B2"

    for r in all_rows:  # one sheet per symbol, in watchlist order
        if r["symbol"] in sheet_names:
            add_symbol_sheet(wb, r["symbol"], fundamentals[r["symbol"]], sheet_names[r["symbol"]], tech=r)

    wb.save(output_path)
    print(f"Reclaimed near entry: {len(reclaimed_rows)}")
    print(f"Approaching: {len(approaching_rows)}")
    if fundamentals:
        tally = {}
        for summ in fundamentals.values():
            tally[summ["verdict"]] = tally.get(summ["verdict"], 0) + 1
        print("Fundamentals: " + ", ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    print(f"Wrote {len(reclaimed_rows) + len(approaching_rows)} stocks to {output_path}")


if __name__ == "__main__":
    main()
