"""Tests for fundamental_rules.py and the parsing helpers in fundamental_screen.py"""
from bs4 import BeautifulSoup
from scripts.fundamental_rules import evaluate
from scripts.fundamental_screen import to_num, parse_table, parse_company_page

YEARS = [f"Mar {y}" for y in range(2015, 2027)] + ["TTM"]
QTRS = [f"Q{i}" for i in range(13)]


def table(periods, **rows):
    return {"periods": periods, "rows": rows}


def good_company(**over):
    n = 12
    sales = [100 * 1.15 ** i for i in range(n)]
    d = {
        "top": {"market_cap": 20000.0, "pe": 25.0, "roe": 20.0},
        "sector": {"broad": "Industrials", "industry": "Machinery"},
        "peers_median_pe": 28.0,
        "growth": {
            "Compounded Sales Growth": {"3 Years": 15.0, "5 Years": 15.0, "TTM": 15.0},
            "Compounded Profit Growth": {"3 Years": 18.0, "5 Years": 18.0, "TTM": 18.0},
            "Return on Equity": {"Last Year": 20.0},
        },
        "tables": {
            "profit-loss": table(YEARS,
                Sales=sales + [sales[-1] * 1.15],
                **{"Operating Profit": [s * 0.2 for s in sales] + [sales[-1] * 0.23], "OPM %": [20.0] * 12 + [20.0],
                   "Other Income": [2.0] * 13, "Interest": [1.0] * 13, "Profit before tax": [s * 0.15 for s in sales] + [30.0],
                   "Net Profit": [s * 0.11 for s in sales] + [30.0], "Dividend Payout %": [30.0] * 12 + [None]}),
            "balance-sheet": table(YEARS[:-1],
                **{"Equity Capital": [10.0] * 12, "Reserves": [100.0 + 40 * i for i in range(12)], "Borrowings": [20.0] * 12,
                   "Other Liabilities": [50.0 + 5 * i for i in range(12)], "Fixed Assets": [100.0 + 10 * i for i in range(12)],
                   "CWIP": [5.0] * 12, "Investments": [60.0] * 12}),
            "cash-flow": table(YEARS[:-1],
                **{"Cash from Operating Activity": [20.0 + 3 * i for i in range(12)], "Cash from Investing Activity": [-10.0] * 12,
                   "Free Cash Flow": [10.0] * 12}),
            "ratios": table(YEARS[:-1], **{"ROCE %": [22.0] * 12, "Cash Conversion Cycle": [60.0] * 12,
                                          "Debtor Days": [40.0] * 12, "Inventory Days": [70.0] * 12}),
            "quarters": table(QTRS, Sales=[100 + 3 * i for i in range(13)], **{"Net Profit": [10 + i for i in range(13)]}),
            "shareholding": table(QTRS[:12], Promoters=[60.0] * 12, FIIs=[10.0 + 0.2 * i for i in range(12)],
                                  DIIs=[8.0 + 0.2 * i for i in range(12)], **{"No. of Shareholders": [1000.0] * 12}),
        },
    }
    d.update(over)
    return d


def level(res, rid):
    return next(r["level"] for r in res["results"] if r["id"] == rid)


def test_to_num():
    assert to_num("1,188") == 1188.0 and to_num("52.63%") == 52.63 and to_num("") is None and to_num("-60") == -60.0


def test_good_company_passes():
    res = evaluate(good_company())
    assert res["verdict"] == "PASS" and not res["hard_fails"] and res["score"] >= 70


def test_high_debt_is_hard_reject():
    d = good_company()
    d["tables"]["balance-sheet"]["rows"]["Borrowings"] = [20.0] * 11 + [900.0]
    res = evaluate(d)
    assert level(res, "1.1") == "fail" and res["verdict"] == "REJECT"
    assert any(f.startswith("1.1") for f in res["hard_fails"])


def test_rising_debt_warns_but_tiny_debt_ignored():
    d = good_company()
    d["tables"]["balance-sheet"]["rows"]["Borrowings"] = [20.0] * 8 + [30.0, 60.0, 120.0, 250.0]
    assert level(evaluate(d), "1.3") == "warn"
    d["tables"]["balance-sheet"]["rows"]["Borrowings"] = [1.0, 2.0, 3.0, 4.0] + [4.0] * 8
    assert level(evaluate(d), "1.3") == "pass"


def test_low_roce_fails():
    d = good_company()
    d["tables"]["ratios"]["rows"]["ROCE %"] = [8.0] * 12
    res = evaluate(d)
    assert level(res, "2.1") == "fail" and res["verdict"] == "REJECT"


def strong(mcap):
    """A healthy company (cash flow >= operating profit) at the given market cap."""
    d = good_company()
    d["top"]["market_cap"] = float(mcap)
    d["tables"]["cash-flow"]["rows"]["Cash from Operating Activity"] = list(d["tables"]["profit-loss"]["rows"]["Operating Profit"][:12])
    return d


def test_below_250_cr_is_hard_rejected_even_if_healthy():
    res = evaluate(strong(200))
    assert res["tier"] == "micro" and res["verdict"] == "REJECT"
    assert any(f.startswith("0.2") for f in res["hard_fails"]) and res["score"] >= 70


def test_250_to_1000_cr_is_capped_at_watch():
    res = evaluate(strong(800))
    assert res["tier"] == "small_low" and not res["hard_fails"]
    assert res["score"] >= 70 and res["verdict"] == "WATCH" and res["capped"]
    assert level(res, "0.2") == "warn"


def test_small_cap_is_not_rejected_for_size_alone():
    res = evaluate(strong(2000))
    assert res["tier"] == "small" and not res["hard_fails"] and res["verdict"] == "PASS" and not res["capped"]
    assert level(res, "0.2") == "ok"
    assert evaluate(strong(5000))["tier"] == "standard" and evaluate(strong(250))["tier"] == "small_low"


def test_small_caps_face_stricter_thresholds():
    # ROCE 16%: passes the standard 15% bar, only warns under the small-cap 18% bar
    big, small = strong(20000), strong(2000)
    for d in (big, small):
        d["tables"]["ratios"]["rows"]["ROCE %"] = [16.0] * 12
        d["growth"]["Return on Equity"]["Last Year"] = 16.0
    assert level(evaluate(big), "2.1") == "pass" and level(evaluate(small), "2.1") == "warn"
    # cash conversion ~65%: standard warns, small caps fail (hard)
    big, small = strong(20000), strong(2000)
    for d in (big, small):
        d["tables"]["cash-flow"]["rows"]["Cash from Operating Activity"] = [x * 0.65 for x in d["tables"]["profit-loss"]["rows"]["Operating Profit"][:12]]
    assert level(evaluate(big), "1.4") == "warn" and level(evaluate(small), "1.4") == "fail"
    # debt/equity 0.6: standard warns, small caps warn; 0.9: standard warns, small caps fail
    for mc, expect in ((20000, "warn"), (2000, "fail")):
        d = strong(mc)
        d["tables"]["balance-sheet"]["rows"]["Borrowings"] = [20.0] * 11 + [0.9 * (10 + 100 + 40 * 11)]
        assert level(evaluate(d), "1.1") == expect


def test_short_history_warns_for_small_caps_but_fails_standard():
    for mc, expect in ((2000, "warn"), (20000, "fail")):
        d = strong(mc)
        d["tables"]["profit-loss"]["rows"]["Sales"] = [None] * 8 + d["tables"]["profit-loss"]["rows"]["Sales"][8:]
        assert level(evaluate(d), "0.1") == expect
    d = strong(2000)
    d["tables"]["profit-loss"]["rows"]["Sales"] = [None] * 10 + d["tables"]["profit-loss"]["rows"]["Sales"][10:]
    assert level(evaluate(d), "0.1") == "fail"


def test_loss_making_is_rejected():
    d = good_company()
    d["tables"]["profit-loss"]["rows"]["Net Profit"][-1] = -5.0
    assert level(evaluate(d), "0.4") == "fail"


def test_financials_are_routed_out():
    res = evaluate(good_company(sector={"broad": "Financials", "industry": "Private Sector Bank"}))
    assert res["verdict"] == "FINANCIAL" and res["score"] is None


def test_peg_not_applicable_when_profit_shrinks():
    d = good_company()
    d["growth"]["Compounded Profit Growth"]["3 Years"] = -4.0
    assert level(evaluate(d), "4.2") == "fail"


def test_promoter_selling_fails_ownership():
    d = good_company()
    d["tables"]["shareholding"]["rows"]["Promoters"] = [60.0] * 4 + [50.0] * 8
    assert level(evaluate(d), "5.1") == "fail"


def test_parse_table_strips_plus_and_numbers():
    html = ('<section id="x"><table><tr><th></th><th>Mar 2025</th><th>TTM</th></tr>'
            '<tr><td class="text">Sales&nbsp;+</td><td>1,200</td><td>1,300</td></tr>'
            '<tr><td>OPM %</td><td>19%</td><td></td></tr></table></section>')
    t = parse_table(BeautifulSoup(html, "html.parser").find("section"))
    assert t["periods"] == ["Mar 2025", "TTM"]
    assert t["rows"]["Sales"] == [1200.0, 1300.0] and t["rows"]["OPM %"] == [19.0, None]


def test_parse_company_page_top_ratios_and_growth():
    html = ('<ul id="top-ratios"><li><span class="name">Stock P/E</span><span class="value"><span class="number">46.3</span></span></li></ul>'
            '<section id="profit-loss"><table class="ranges-table"><tr><th>Compounded Sales Growth</th></tr>'
            '<tr><td>3 Years:</td><td>1%</td></tr></table></section>')
    d = parse_company_page(html)
    assert d["top"]["pe"] == 46.3
    assert d["growth"]["Compounded Sales Growth"]["3 Years"] == 1.0
