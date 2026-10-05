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


def test_small_cap_and_loss_are_rejected():
    d = good_company()
    d["top"]["market_cap"] = 2000.0
    assert evaluate(d)["verdict"] == "REJECT"
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
