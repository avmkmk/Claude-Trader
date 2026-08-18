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

Usage:
    python scripts/build_final_watchlist.py <scan_date> <output_path>
"""
import json
import sys

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

STATE_PATH = "data/daily_scans/symbol_state.json"
EXCLUSIONS_PATH = "data/daily_scans/manual_exclusions.json"

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


def main():
    if len(sys.argv) != 3:
        print("Usage: python build_final_watchlist.py <scan_date> <output_path>")
        sys.exit(1)
    scan_date, output_path = sys.argv[1], sys.argv[2]

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
                "entry_date": r.get("entry_date"), "last_checked": r.get("last_checked"),
            })
        elif r.get("verdict") == "approaching":
            approaching_rows.append({
                "symbol": symbol, "status": "Approaching", "cap_size": cap_size,
                "market_cap_cr": market_cap_cr, "distance_pct": r.get("distance_pct"),
                "close": r.get("close"), "reference_price": r.get("absolute_ath"),
                "reference_label": "ATH (entry trigger)", "ema200": r.get("ema200"),
                "entry_date": None, "last_checked": r.get("last_checked"),
            })

    reclaimed_rows.sort(key=lambda r: abs(r["distance_pct"]))
    approaching_rows.sort(key=lambda r: abs(r["distance_pct"]))

    wb = Workbook()
    ws = wb.active
    ws.title = "Watchlist"

    headers = [
        "Symbol", "Status", "Cap Tier", "Market Cap (cr)", "Distance from Entry %",
        "Current Price", "Reference Price", "Reference", "EMA 200", "Entry Date",
        "Last Checked", "TradingView Link",
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
            ws.cell(row=row_idx, column=1, value=r["symbol"])
            ws.cell(row=row_idx, column=2, value=r["status"])
            ws.cell(row=row_idx, column=3, value=CAP_LABELS.get(r["cap_size"], "Unknown"))
            ws.cell(row=row_idx, column=4, value=r["market_cap_cr"])
            ws.cell(row=row_idx, column=5, value=r["distance_pct"])
            ws.cell(row=row_idx, column=6, value=r["close"])
            ws.cell(row=row_idx, column=7, value=r["reference_price"])
            ws.cell(row=row_idx, column=8, value=r["reference_label"])
            ws.cell(row=row_idx, column=9, value=r["ema200"])
            ws.cell(row=row_idx, column=10, value=r["entry_date"] or "")
            ws.cell(row=row_idx, column=11, value=r["last_checked"] or "")
            ws.cell(row=row_idx, column=12, value=f"https://in.tradingview.com/chart/?symbol=NSE:{r['symbol']}")
            row_idx += 1

    for col_idx, header in enumerate(headers, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = max(14, len(header) + 2)

    wb.save(output_path)
    print(f"Reclaimed near entry: {len(reclaimed_rows)}")
    print(f"Approaching: {len(approaching_rows)}")
    print(f"Wrote {len(reclaimed_rows) + len(approaching_rows)} stocks to {output_path}")


if __name__ == "__main__":
    main()
