"""
Per-symbol fundamental sheets for the daily watchlist workbook.

Each symbol gets a sheet named after it: verdict banner, key figures, a 3-4 line summary, an optional
"News and policy" (Gate 7) section, then every rule as one filterable table (Gate | Check | Value | Result)
with dropdown sort/filter on every column. The Watchlist sheet's symbol cell links here and this sheet links back.
"""
import re

from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.hyperlink import Hyperlink

from scripts.fundamental_rules import HARD_GATES, summary_notes

VERDICT_FILLS = {"PASS": "C6EFCE", "WATCH": "FFEB9C", "REJECT": "FFC7CE", "FINANCIAL": "DDEBF7", "NO DATA": "D9D9D9"}
SENTIMENT_FILLS = {"Bullish": "C6EFCE", "Neutral": "EDEDED", "Bearish": "FFC7CE", "Unrated": "EDEDED"}
RESULT_STYLE = {  # level -> (label, fill)
    "pass": ("Pass", "C6EFCE"), "bonus": ("Bonus", "C6EFCE"), "ok": ("Neutral", "F2F2F2"),
    "warn": ("Warn", "FFEB9C"), "fail": ("Fail", "F8CBAD"), "info": ("Info", "EDEDED"), "skip": ("Not checked", "EDEDED"),
}
GATE_LABELS = {0: "0 Eligibility", 1: "1 Survival & red flags", 2: "2 Business quality", 3: "3 Growth",
               4: "4 Valuation", 5: "5 Ownership", 6: "6 Balance sheet"}
BLOCK_LABELS = [("quality", "Quality", 30), ("growth", "Growth", 25), ("safety", "Safety", 20),
                ("valuation", "Valuation", 15), ("ownership", "Ownership", 10)]
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
LAST_COL = 4  # columns A-D


def sheet_name(symbol, used=()):
    """Excel sheet names: max 31 chars, none of []:*?/\\ and unique (case-insensitive)."""
    base = re.sub(r"[\[\]:*?/\\]", "_", symbol)[:31] or "sheet"
    name, n = base, 2
    taken = {u.lower() for u in used}
    while name.lower() in taken:
        suffix = f"_{n}"
        name, n = base[:31 - len(suffix)] + suffix, n + 1
    return name


def link(cell, location, text=None):
    """Internal (same-workbook) hyperlink."""
    cell.hyperlink = Hyperlink(ref=cell.coordinate, location=location, display=text or str(cell.value))
    cell.font = Font(color="0563C1", underline="single", bold=cell.font.bold, size=cell.font.size)


def _fmt(v, spec, unit=""):
    return format(v, spec) + unit if v is not None else "n/a"


def _header_bar(ws, row, text):
    ws.cell(row=row, column=1, value=text).font = Font(bold=True, color="FFFFFF")
    for c in range(1, LAST_COL + 1):
        ws.cell(row=row, column=c).fill = PatternFill("solid", fgColor="404040")


def _wrapped_line(ws, row, text, chars_per_line=135):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=LAST_COL)
    c = ws.cell(row=row, column=1, value=text)
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[row].height = 15 * max(1, -(-len(text) // chars_per_line))


def add_symbol_sheet(wb, symbol, summary, name, tech=None, top=None, watchlist_title="Watchlist", gate7=None, gate7_ran=False):
    """Create the sheet `name` for one symbol. `summary` is a screen_symbols() entry; `gate7` a cleaned Gate 7 entry."""
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    for col, w in zip("ABCD", (38, 78, 16, 24)):
        ws.column_dimensions[col].width = w
    top = top or summary.get("top") or {}

    link(ws.cell(row=1, column=1, value=f"<< Back to {watchlist_title}"), f"'{watchlist_title}'!A1")

    label = summary.get("name") or symbol
    title = ws.cell(row=2, column=1, value=symbol + (f"  -  {label}" if label != symbol else "")
                    + (f"  ({summary['industry']})" if summary.get("industry") else ""))
    title.font = Font(bold=True, size=16)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=LAST_COL)

    verdict = summary["verdict"]
    ws.cell(row=3, column=1, value="Fundamental verdict").font = Font(bold=True)
    v = ws.cell(row=3, column=2, value=verdict + (f"  -  {summary['score']:g} / 100" if summary.get("score") is not None else ""))
    v.font = Font(bold=True, size=12)
    v.fill = PatternFill("solid", fgColor=VERDICT_FILLS.get(verdict, "FFFFFF"))

    blocks = summary.get("blocks") or {}
    if blocks:
        ws.cell(row=4, column=1, value="Block scores").font = Font(bold=True)
        ws.cell(row=4, column=2, value="   ".join(f"{lbl} {blocks[k]:g}/{mx}" for k, lbl, mx in BLOCK_LABELS if k in blocks))

    ws.cell(row=5, column=1, value="Key figures").font = Font(bold=True)
    ws.cell(row=5, column=2, value="   ".join([
        f"Market cap Rs {_fmt(top.get('market_cap'), ',.0f')} Cr", f"Price Rs {_fmt(top.get('price'), ',.2f')}",
        f"P/E {_fmt(top.get('pe'), '.1f')}", f"ROCE {_fmt(top.get('roce'), '.1f')}%", f"ROE {_fmt(top.get('roe'), '.1f')}%",
        f"Book value Rs {_fmt(top.get('book'), ',.0f')}", f"Dividend yield {_fmt(top.get('div_yield'), '.2f')}%"]))

    if tech:
        ws.cell(row=6, column=1, value="Technical (ATH scan)").font = Font(bold=True)
        ws.cell(row=6, column=2, value="   ".join([
            str(tech.get("status", "")), f"Distance {_fmt(tech.get('distance_pct'), '+.2f', '%')}",
            f"Win rate {_fmt(tech.get('win_rate_pct'), '.0f', '%')}", f"Profit factor {_fmt(tech.get('profit_factor'), '.1f')}",
            f"Trades {tech.get('total_trades') if tech.get('total_trades') is not None else 'n/a'}"]))

    row = 8
    _header_bar(ws, row, "Summary")
    row += 1
    for line in summary.get("notes") or summary_notes(summary, top, summary.get("basis")):
        _wrapped_line(ws, row, line)
        row += 1

    # ---- Gate 7: news + government stance (written by the Claude command; blank when not run) ----
    row += 1
    _header_bar(ws, row, "News and policy (Gate 7)")
    row += 1
    if gate7:
        for lbl, key in (("Company news sentiment", "news_sentiment"), ("Government / industry stance", "policy_sentiment")):
            ws.cell(row=row, column=1, value=lbl).font = Font(bold=True)
            c = ws.cell(row=row, column=2, value=gate7[key])
            c.fill = PatternFill("solid", fgColor=SENTIMENT_FILLS.get(gate7[key], "EDEDED"))
            c.font = Font(bold=True)
            row += 1
        if gate7.get("summary"):
            _wrapped_line(ws, row, gate7["summary"])
            row += 1
        for h in gate7.get("headlines", []):
            cell = ws.cell(row=row, column=1, value=" - ".join(x for x in (h.get("date"), h.get("source"), h["title"]) if x))
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=LAST_COL)
            if str(h.get("url", "")).startswith("http"):
                cell.hyperlink = h["url"]
                cell.font = Font(color="0563C1", underline="single")
            row += 1
        if gate7.get("checked_on"):
            ws.cell(row=row, column=1, value=f"Searched on {gate7['checked_on']} (AI web search; verify before acting)").font = Font(italic=True, color="7F7F7F")
            row += 1
    else:
        msg = ("Gate 7 only covers PASS / WATCH stocks." if summary["verdict"] not in ("PASS", "WATCH") else
               "Not covered in the Gate 7 run." if gate7_ran else
               "Pending - run /daily-ath-scan in Claude Code to add the news and government-stance check.")
        _wrapped_line(ws, row, msg)
        row += 1

    # ---- rules table: one clean block (single header row, no sub-headers) so every column can be sorted/filtered ----
    row += 1
    header_row = row
    for c, text in enumerate(("Check", "Value", "Result", "Gate"), start=1):
        cell = ws.cell(row=row, column=c, value=text)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="404040")
        cell.border = BORDER
    row += 1
    for r in sorted(summary.get("results", []), key=lambda r: [int(p) for p in r["id"].split(".")]):
        lvl_label, fill = RESULT_STYLE[r["level"]]
        if r["level"] == "fail" and r["gate"] in HARD_GATES:
            lvl_label = "Fail - Reject"
        ws.cell(row=row, column=1, value=f"{r['name']} ({r['id']})")
        ws.cell(row=row, column=2, value=r["msg"]).alignment = Alignment(wrap_text=True, vertical="top")
        res = ws.cell(row=row, column=3, value=lvl_label)
        res.fill = PatternFill("solid", fgColor=fill)
        res.font = Font(bold=r["level"] in ("warn", "fail"))
        ws.cell(row=row, column=4, value=GATE_LABELS.get(r["gate"], f"{r['gate']}"))
        for c in range(1, LAST_COL + 1):
            ws.cell(row=row, column=c).border = BORDER
        row += 1
    if row > header_row + 1:
        from openpyxl.utils import get_column_letter
        ws.auto_filter.ref = f"A{header_row}:{get_column_letter(LAST_COL)}{row - 1}"
    ws.freeze_panes = "A3"
    return ws
