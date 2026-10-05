"""
Fundamental rules engine (see docs/FUNDAMENTAL_RULES.md).

Pure functions: takes the parsed screener.in data dict (see fundamental_screen.parse_company_page)
and returns a verdict, 0-100 score, per-block scores and one result per rule. No I/O.
"""
from statistics import median, pstdev

POINTS = {"pass": 1.0, "bonus": 1.0, "ok": 0.6, "warn": 0.3, "fail": 0.0}

GATE_NAMES = {0: "Gate 0 - Eligibility", 1: "Gate 1 - Survival and red flags", 2: "Gate 2 - Business quality",
              3: "Gate 3 - Growth", 4: "Gate 4 - Valuation", 5: "Gate 5 - Ownership", 6: "Gate 6 - Balance-sheet strength"}
RULE_NAMES = {
    "0.1": "Enough history", "0.2": "Market cap size", "0.3": "Not a financial company", "0.4": "Profitable (last FY and TTM)",
    "1.1": "Debt to equity", "1.2": "Interest cover", "1.3": "Rising debt", "1.4": "Cash backs profit (CFO/OP)",
    "1.5": "Free cash flow (5 yrs)", "1.6": "Other income share of profit", "1.7": "Liabilities vs sales growth",
    "1.8": "Equity dilution", "1.9": "Promoter pledging", "1.10": "Credit rating",
    "2.1": "ROCE level", "2.2": "ROCE consistency", "2.3": "ROCE trend", "2.4": "ROE", "2.5": "ROE vs ROCE (debt-inflated?)",
    "2.6": "Operating margin vs history", "2.7": "Margin stability", "2.8": "Cash conversion cycle", "2.9": "Debtor and inventory days",
    "3.1": "Sales growth (3y / 5y)", "3.2": "Profit growth (3y / 5y)", "3.3": "TTM growth", "3.4": "Latest quarter (YoY)",
    "3.5": "Profit growth streak", "3.6": "Operating leverage", "3.7": "Earnings shocks (5 yrs)",
    "4.1": "P/E vs peers", "4.2": "PEG", "4.4": "Dividend payout",
    "5.1": "Promoter holding", "5.2": "FII + DII holding", "5.3": "Shareholder count",
    "6.1": "Reserves growth", "6.2": "Self-funded growth", "6.3": "Capex with ROCE holding", "6.4": "Investments vs borrowings",
}
BLOCK_MAX = {"quality": 30, "growth": 25, "safety": 20, "valuation": 15, "ownership": 10}
HARD_GATES = (0, 1, 2)


# ---------- data accessors ----------

def _norm(name):
    return name.replace("+", "").strip().lower()


def _table(d, table):
    return d.get("tables", {}).get(table) or {"periods": [], "rows": {}}


def series(d, table, name, with_ttm=False):
    """Values for a row, annual/quarterly columns only (the 'TTM' column is dropped unless asked)."""
    t = _table(d, table)
    row = next((v for k, v in t["rows"].items() if _norm(k) == _norm(name)), None)
    if row is None:
        return []
    out = []
    for period, v in zip(t["periods"], row):
        if period.strip().upper() == "TTM" and not with_ttm:
            continue
        out.append(v)
    return out


def ttm_value(d, table, name):
    t = _table(d, table)
    if not t["periods"] or t["periods"][-1].strip().upper() != "TTM":
        return None
    row = next((v for k, v in t["rows"].items() if _norm(k) == _norm(name)), None)
    return row[-1] if row else None


def tail(lst, k):
    """Last k values, or None if fewer than k or any is missing."""
    if len(lst) < k:
        return None
    t = lst[-k:]
    return None if any(v is None for v in t) else t


def pct_change(new, old):
    if new is None or old is None or old == 0:
        return None
    return (new - old) / abs(old) * 100.0


def growth(d, block, label):
    return d.get("growth", {}).get(block, {}).get(label)


# ---------- engine ----------

def evaluate(d):
    results = []

    def add(rid, gate, block, level, msg):
        results.append({"id": rid, "name": RULE_NAMES.get(rid, rid), "gate": gate, "block": block, "level": level, "msg": msg})

    top = d.get("top", {})
    broad = (d.get("sector", {}).get("broad") or "")
    industry = (d.get("sector", {}).get("industry") or "")

    if "financ" in broad.lower() or "bank" in industry.lower() or "insurance" in industry.lower():
        add("0.3", 0, None, "info", f"Financial sector ({broad} / {industry}) - needs financials ruleset")
        return {"verdict": "FINANCIAL", "score": None, "blocks": {}, "results": results, "hard_fails": []}

    # ---- Gate 0: eligibility ----
    sales_a = series(d, "profit-loss", "Sales")
    np_a = series(d, "profit-loss", "Net Profit")
    n_years = len([v for v in sales_a if v is not None])
    add("0.1", 0, None, "pass" if n_years >= 5 else "fail", f"{n_years} years of annual data")
    mcap = top.get("market_cap")
    if mcap is not None:
        add("0.2", 0, None, "pass" if mcap >= 5000 else "fail", f"Market cap Rs {mcap:,.0f} Cr (min 5,000)")
    np_last, np_ttm = (np_a[-1] if np_a else None), ttm_value(d, "profit-loss", "Net Profit")
    if np_last is not None:
        ok = np_last > 0 and (np_ttm is None or np_ttm > 0)
        add("0.4", 0, None, "pass" if ok else "fail", f"Net profit last FY {np_last:,.0f}, TTM {np_ttm if np_ttm is not None else 'n/a'}")

    # ---- Gate 1: survival and red flags ----
    eq_cap, reserves, borrow = (series(d, "balance-sheet", n) for n in ("Equity Capital", "Reserves", "Borrowings"))
    networth = (eq_cap[-1] + reserves[-1]) if eq_cap and reserves and None not in (eq_cap[-1], reserves[-1]) else None
    de = None
    if networth is not None and borrow and borrow[-1] is not None:
        de = borrow[-1] / networth if networth > 0 else 99.0
        add("1.1", 1, "safety", "pass" if de <= 0.5 else "warn" if de <= 1 else "fail", f"Debt/equity {de:.2f}")

    op_a, intr_a = series(d, "profit-loss", "Operating Profit"), series(d, "profit-loss", "Interest")
    if op_a and intr_a and None not in (op_a[-1], intr_a[-1]):
        if intr_a[-1] <= 0:
            add("1.2", 1, "safety", "pass", "No interest cost")
        else:
            ic = op_a[-1] / intr_a[-1]
            add("1.2", 1, "safety", "pass" if ic >= 5 else "warn" if ic >= 3 else "fail", f"Interest cover {ic:.1f}x")

    b4 = tail(borrow, 4)
    if b4 and networth:
        material = lambda a, b: (b - a) > 0.05 * networth   # ignore noise on tiny debt
        rising3 = all(b4[i + 1] > b4[i] and material(b4[i], b4[i + 1]) for i in range(3))
        jump = b4[3] > b4[2] * 1.5 and material(b4[2], b4[3])
        msg = f"Borrowings {b4[0]:,.0f} -> {b4[1]:,.0f} -> {b4[2]:,.0f} -> {b4[3]:,.0f}"
        add("1.3", 1, "safety", "warn" if (rising3 or jump) else "pass", msg)

    cfo3, op3 = tail(series(d, "cash-flow", "Cash from Operating Activity"), 3), tail(op_a, 3)
    if cfo3 and op3:
        if sum(op3) <= 0:
            add("1.4", 1, "safety", "fail", "Operating profit sum <= 0 over 3 years")
        else:
            r = sum(cfo3) / sum(op3) * 100
            add("1.4", 1, "safety", "pass" if r >= 80 else "warn" if r >= 60 else "fail", f"3-yr CFO/OP {r:.0f}%")

    fcf5 = tail(series(d, "cash-flow", "Free Cash Flow"), 5)
    if fcf5:
        add("1.5", 1, "safety", "warn" if sum(fcf5) < 0 else "pass", f"5-yr free cash flow {sum(fcf5):,.0f} Cr")

    oi_a, pbt_a = series(d, "profit-loss", "Other Income"), series(d, "profit-loss", "Profit before tax")
    if oi_a and pbt_a and None not in (oi_a[-1], pbt_a[-1]):
        if pbt_a[-1] <= 0:
            add("1.6", 1, "safety", "fail", "Profit before tax <= 0")
        else:
            r = oi_a[-1] / pbt_a[-1] * 100
            add("1.6", 1, "safety", "pass" if r < 20 else "warn" if r <= 40 else "fail", f"Other income {r:.0f}% of PBT")

    ol4, s4 = tail(series(d, "balance-sheet", "Other Liabilities"), 4), tail(sales_a, 4)
    if ol4 and s4 and ol4[0] and s4[0]:
        diff = pct_change(ol4[-1], ol4[0]) - pct_change(s4[-1], s4[0])
        add("1.7", 1, "safety", "warn" if diff > 10 else "pass", f"Other liabilities growth minus sales growth (3y): {diff:+.0f} pts")

    ec4 = tail(eq_cap, 4)
    if ec4 and ec4[0]:
        g = pct_change(ec4[-1], ec4[0])
        add("1.8", 1, "safety", "warn" if g > 10 else "pass", f"Equity capital change over 3y {g:+.1f}%")

    add("1.9", 1, None, "skip", "Promoter pledging not available in v1")
    add("1.10", 1, None, "skip", "Credit rating needs manual/LLM read")

    # ---- Gate 2: quality ----
    roce_a = series(d, "ratios", "ROCE %")
    r5 = tail(roce_a, 5)
    if roce_a and roce_a[-1] is not None:
        r = roce_a[-1]
        add("2.1", 2, "quality", "pass" if r >= 15 else "warn" if r >= 10 else "fail", f"ROCE {r:.1f}%" + (" (strong)" if r >= 20 else ""))
    if r5:
        med, bad = median(r5), sum(1 for v in r5 if v < 10)
        lvl = "pass" if med >= 15 and bad == 0 else "fail" if med < 10 else "warn"
        add("2.2", 2, "quality", lvl, f"5-yr median ROCE {med:.1f}%, {bad} yrs below 10%")
        drop = r5[-1] - sum(r5) / 5
        add("2.3", 2, "quality", "fail" if drop < -10 else "warn" if drop < -5 else "pass", f"ROCE vs 5-yr average {drop:+.1f} pts")

    roe_last = growth(d, "Return on Equity", "Last Year")
    if roe_last is None:
        roe_last = top.get("roe")
    if roe_last is not None:
        add("2.4", 2, "quality", "pass" if roe_last >= 15 else "warn" if roe_last >= 10 else "fail", f"ROE {roe_last:.1f}%")
        if de is not None and roce_a and roce_a[-1] is not None:
            infl = roe_last - roce_a[-1] > 8 and de > 0.5
            add("2.5", 2, "quality", "warn" if infl else "pass", f"ROE {roe_last:.0f}% vs ROCE {roce_a[-1]:.0f}%, D/E {de:.2f}")

    opm_a, opm_ttm = series(d, "profit-loss", "OPM %"), ttm_value(d, "profit-loss", "OPM %")
    opm5 = tail(opm_a, 5)
    if opm5:
        cur = opm_ttm if opm_ttm is not None else opm_a[-1]
        diff = cur - median(opm5)
        add("2.6", 2, "quality", "pass" if diff >= -3 else "ok" if diff >= -5 else "warn", f"OPM {cur:.0f}% vs 5-yr median {median(opm5):.0f}%")
        sd = pstdev(opm5)
        add("2.7", 2, "quality", "pass" if sd < 4 else "ok" if sd <= 6 else "warn", f"OPM std-dev {sd:.1f} pts")

    ccc4 = tail(series(d, "ratios", "Cash Conversion Cycle"), 4)
    if ccc4 and ccc4[0] > 0:
        g = pct_change(ccc4[-1], ccc4[0])
        add("2.8", 2, "quality", "warn" if g > 25 and ccc4[-1] - ccc4[0] > 10 else "pass", f"Cash conversion cycle {ccc4[0]:.0f} -> {ccc4[-1]:.0f} days")
    dd4, inv4 = tail(series(d, "ratios", "Debtor Days"), 4), tail(series(d, "ratios", "Inventory Days"), 4)
    if dd4 and inv4:
        bad = [n for n, x in (("debtor", dd4), ("inventory", inv4)) if x[0] > 0 and pct_change(x[-1], x[0]) > 30 and x[-1] - x[0] > 10]
        add("2.9", 2, "quality", "warn" if bad else "pass", f"Debtor days {dd4[0]:.0f}->{dd4[-1]:.0f}, inventory days {inv4[0]:.0f}->{inv4[-1]:.0f}")

    # ---- Gate 3: growth ----
    sg3, sg5 = growth(d, "Compounded Sales Growth", "3 Years"), growth(d, "Compounded Sales Growth", "5 Years")
    pg3, pg5 = growth(d, "Compounded Profit Growth", "3 Years"), growth(d, "Compounded Profit Growth", "5 Years")

    def two(a, b):
        v = [x for x in (a, b) if x is not None]
        if not v:
            return None
        return "pass" if all(x >= 10 for x in v) else "warn" if any(x < 5 for x in v) else "ok"

    if two(sg3, sg5):
        add("3.1", 3, "growth", two(sg3, sg5), f"Sales CAGR 3y {sg3}%, 5y {sg5}%")
    if two(pg3, pg5):
        add("3.2", 3, "growth", two(pg3, pg5), f"Profit CAGR 3y {pg3}%, 5y {pg5}%")
    sgt, pgt = growth(d, "Compounded Sales Growth", "TTM"), growth(d, "Compounded Profit Growth", "TTM")
    if sgt is not None and pgt is not None:
        add("3.3", 3, "growth", "pass" if sgt >= 10 and pgt >= 10 else "warn" if sgt < 0 or pgt < 0 else "ok", f"TTM sales {sgt}%, profit {pgt}%")

    qs, qp = series(d, "quarters", "Sales"), series(d, "quarters", "Net Profit")

    def yoy(lst, i):
        if len(lst) < 5 - i or lst[-1 - i] is None or lst[-5 - i] is None:
            return None
        return pct_change(lst[-1 - i], lst[-5 - i]) if lst[-5 - i] > 0 else (100.0 if lst[-1 - i] > 0 else -100.0)

    sy, py = (yoy(qs, 0) if len(qs) >= 5 else None), (yoy(qp, 0) if len(qp) >= 5 else None)
    if sy is not None and py is not None:
        add("3.4", 3, "growth", "pass" if sy >= 10 and py > 0 else "warn" if py <= 0 else "ok", f"Latest quarter YoY: sales {sy:+.0f}%, profit {py:+.0f}%")
        streak = 0
        for i in range(len(qp) - 4):
            v = yoy(qp, i)
            if v is None or v <= 0:
                break
            streak += 1
        add("3.5", 3, "growth", "bonus" if streak >= 3 else "ok", f"{streak} consecutive quarters of YoY profit growth")
    if sg3 is not None and pg3 is not None:
        add("3.6", 3, "growth", "pass" if pg3 >= sg3 else "ok", f"3-yr profit {pg3}% vs sales {sg3}%")
    np6 = tail(np_a, 6)
    if np6:
        worst = min((pct_change(np6[i + 1], np6[i]) for i in range(5) if np6[i] > 0), default=0)
        add("3.7", 3, "growth", "warn" if worst < -25 else "pass", f"Worst annual profit change in 5 yrs {worst:+.0f}%")

    # ---- Gate 4: valuation ----
    pe, med_pe = top.get("pe"), d.get("peers_median_pe")
    if pe and med_pe:
        r = pe / med_pe
        add("4.1", 4, "valuation", "pass" if r <= 1.5 else "warn" if r <= 2 else "fail", f"P/E {pe:.1f} vs peer median {med_pe:.1f} ({r:.2f}x)")
    if pe and pg3 is not None:
        if pg3 <= 0:
            add("4.2", 4, "valuation", "fail", f"PEG n/a (3-yr profit growth {pg3}%)")
        else:
            peg = pe / pg3
            add("4.2", 4, "valuation", "pass" if peg < 1 else "ok" if peg <= 2 else "fail", f"PEG {peg:.1f}")
    po = series(d, "profit-loss", "Dividend Payout %")
    if po and po[-1] is not None:
        add("4.4", 4, None, "info", f"Dividend payout {po[-1]:.0f}%")

    # ---- Gate 5: ownership ----
    prom, fii, dii = (series(d, "shareholding", n) for n in ("Promoters", "FIIs", "DIIs"))
    if prom and prom[-1] is not None:
        base = prom[-9] if len(prom) >= 9 and prom[-9] is not None else prom[0]
        chg = prom[-1] - base
        lvl = "fail" if chg < -5 else "pass" if prom[-1] >= 40 and chg >= -2 else "warn" if prom[-1] < 40 else "ok"
        add("5.1", 5, "ownership", lvl, f"Promoters {prom[-1]:.1f}% (change {chg:+.1f} pts over 8 qtrs)")
    if fii and dii and fii[-1] is not None and dii[-1] is not None:
        inst = [(a + b) if a is not None and b is not None else None for a, b in zip(fii, dii)]

        def chg(k):
            return inst[-1] - inst[-1 - k] if len(inst) > k and inst[-1 - k] is not None else None

        c4, c8 = chg(4), chg(8)
        known = [c for c in (c4, c8) if c is not None]
        if known:
            lvl = "bonus" if all(c >= 0 for c in known) else "warn" if any(c < -5 for c in known) else "ok"
            add("5.2", 5, "ownership", lvl, f"FII+DII {inst[-1]:.1f}% (4q {c4 if c4 is None else format(c4, '+.1f')}, 8q {c8 if c8 is None else format(c8, '+.1f')})")
    sh = series(d, "shareholding", "No. of Shareholders")
    if sh and sh[-1] is not None and len(sh) >= 5 and sh[-5]:
        add("5.3", 5, None, "info", f"Shareholders {pct_change(sh[-1], sh[-5]):+.0f}% over 4 qtrs")

    # ---- Gate 6: balance-sheet bonus (scored inside safety) ----
    res5 = tail(reserves, 5)
    if res5:
        up = all(res5[i + 1] > res5[i] for i in range(4))
        add("6.1", 6, "safety", "bonus" if up else "ok", "Reserves rising every year" if up else "Reserves not rising every year")
    cfo_s, cfi_s = tail(series(d, "cash-flow", "Cash from Operating Activity"), 3), tail(series(d, "cash-flow", "Cash from Investing Activity"), 3)
    if cfo_s and cfi_s:
        self_funded = sum(cfo_s) + sum(cfi_s) > 0
        add("6.2", 6, "safety", "bonus" if self_funded else "ok", "Operating cash covers investing (3y)" if self_funded else "Operating cash below investing outflow (3y)")
    fa4, cw4 = tail(series(d, "balance-sheet", "Fixed Assets"), 4), tail(series(d, "balance-sheet", "CWIP"), 4)
    if fa4 and cw4 and r5:
        gro = (fa4[-1] + cw4[-1]) > (fa4[0] + cw4[0])
        held = r5[-1] - sum(r5) / 5 >= -5
        add("6.3", 6, "safety", "bonus" if gro and held else "ok", "Capex growing with ROCE holding" if gro and held else "No capex growth, or ROCE slipping")
    inv_bs = series(d, "balance-sheet", "Investments")
    if inv_bs and inv_bs[-1] is not None and borrow and borrow[-1] is not None:
        add("6.4", 6, "safety", "bonus" if inv_bs[-1] > borrow[-1] else "ok", f"Investments {inv_bs[-1]:,.0f} vs borrowings {borrow[-1]:,.0f}")

    # ---- score ----
    blocks = {}
    for b, bmax in BLOCK_MAX.items():
        pts = [POINTS[r["level"]] for r in results if r["block"] == b and r["level"] in POINTS]
        blocks[b] = round(bmax * (sum(pts) / len(pts)), 1) if pts else round(bmax * 0.5, 1)
    score = round(sum(blocks.values()), 1)
    hard_fails = [f'{r["id"]}: {r["msg"]}' for r in results if r["gate"] in HARD_GATES and r["level"] == "fail"]
    verdict = "REJECT" if hard_fails or score < 50 else "PASS" if score >= 70 else "WATCH"
    return {"verdict": verdict, "score": score, "blocks": blocks, "results": results, "hard_fails": hard_fails}


# ---------- plain-English summary ----------

_STRENGTH_PRIORITY = ["2.1", "2.2", "1.1", "1.2", "1.4", "3.4", "3.3", "3.1", "3.2", "4.1", "5.1", "5.2", "6.1", "6.2"]


def summary_notes(summary, top=None, basis=None):
    """3-4 short lines describing the stock, built only from the rule results."""
    top = top or {}
    verdict, score = summary["verdict"], summary.get("score")
    results = summary.get("results", [])
    mcap = top.get("market_cap")
    cap_txt = f"Market cap Rs {mcap:,.0f} Cr" if mcap else "Market cap n/a"

    if verdict == "FINANCIAL":
        return ["Bank / NBFC / insurer: the non-financial rule set does not apply, so it is not scored.",
                "Judge it on ROE, price-to-book, net interest margin, asset quality (NPA) and capital adequacy instead.",
                cap_txt + ". A financials ruleset is a planned follow-up."]
    if verdict == "NO DATA":
        reason = "; ".join(summary.get("hard_fails") or []) or "no data returned"
        return [f"No fundamental data could be fetched ({reason}).", "Check the symbol on screener.in manually."]

    blocks = summary.get("blocks", {})
    frac = {b: blocks[b] / BLOCK_MAX[b] for b in blocks if b in BLOCK_MAX}
    best, worst = max(frac, key=frac.get), min(frac, key=frac.get)
    lines = []
    if summary.get("hard_fails"):
        lines.append(f"{verdict} ({score:.0f}/100) - hard fail: " + "; ".join(f.split(": ", 1)[1] for f in summary["hard_fails"][:2]) + ".")
    else:
        lines.append(f"{verdict} ({score:.0f}/100). Strongest area: {best.capitalize()} ({blocks[best]:g}/{BLOCK_MAX[best]}); weakest: {worst.capitalize()} ({blocks[worst]:g}/{BLOCK_MAX[worst]}).")

    by_id = {r["id"]: r for r in results}
    strengths = [by_id[i]["msg"] for i in _STRENGTH_PRIORITY if i in by_id and by_id[i]["level"] in ("pass", "bonus")][:3]
    lines.append("Strengths: " + ("; ".join(strengths) if strengths else "none standing out on these rules") + ".")

    concerns = sorted((r for r in results if r["level"] in ("fail", "warn")), key=lambda r: (r["gate"] not in HARD_GATES, r["level"] != "fail"))
    lines.append("Concerns: " + ("; ".join(r["msg"] for r in concerns[:3]) if concerns else "no warnings raised") + ".")

    ctx = cap_txt + (" (small cap - thinner liquidity, higher volatility)" if mcap and mcap < 5000 else "")
    lines.append(ctx + (f"; {basis} statements" if basis else "") + ". Promoter pledging and credit rating are not checked yet.")
    return lines
