# Fundamental Screening Rules (screener.in)

Automatable rules applied to a stock's screener.in page (consolidated figures) after the technical ATH scan has shortlisted it. Thresholds are **starting points to tune**, not proven numbers. Implemented in `simple-trader-api/scripts/fundamental_rules.py` (pure rules engine) and `simple-trader-api/scripts/fundamental_screen.py` (fetch, parse, Excel report); tests in `tests/test_fundamental_rules.py`.

## How it works
Each stock passes through the gates in order. A **FAIL** in Gates 0-2 makes it **REJECT**. Everything else feeds a 0-100 score: **PASS** >= 70, **WATCH** 50-69, **REJECT** < 50 or any hard fail. The output lists every flag so the reason is visible. A REJECT only flags the row; it is never silently removed from the watchlist.

Banks, NBFCs and insurers need different metrics (NIM, NPA, capital adequacy). They are routed out at Gate 0 and marked `FINANCIAL - not scored` until a financials ruleset exists.

## Gate 0: Eligibility
| # | Rule | Source | Result |
|---|---|---|---|
| 0.1 | At least 5 years of annual data | P&L columns | Fail if fewer |
| 0.2 | Market cap >= Rs 5,000 Cr | Top box | Fail if smaller |
| 0.3 | Sector is not Bank / NBFC / Insurance | Sector line under Peer comparison | Route to financials |
| 0.4 | Net profit positive, TTM and last FY | P&L | Fail if either negative |

## Gate 1: Survival and red flags
| # | Rule | Formula | Pass / Warn / Fail |
|---|---|---|---|
| 1.1 | Debt to equity | Borrowings / (Equity Capital + Reserves) | <=0.5 pass; 0.5-1 warn; >1 fail |
| 1.2 | Interest cover | Operating Profit / Interest | >=5 pass; 3-5 warn; <3 fail |
| 1.3 | Rising debt | Borrowings up each of last 3 years, or up >50% in one year (increase must exceed 5% of net worth, to ignore noise on tiny debt) | Warn |
| 1.4 | Cash backs profit | Sum of last 3 yrs Cash from Operations / sum of Operating Profit | >=80% pass; 60-80 warn; <60 fail |
| 1.5 | Free cash flow | Sum of last 5 years FCF | Negative warns |
| 1.6 | Profit quality | Other Income / Profit before tax (last FY) | <20% pass; 20-40 warn; >40 fail |
| 1.7 | Liabilities outrunning sales | Total 3-yr % growth of Other Liabilities minus total 3-yr % growth of sales | > +10 points warns |
| 1.8 | Equity dilution | Equity Capital growth over 3 years | >10% warns |
| 1.9 | Promoter pledging | Pledged % of promoter holding | <10 pass; 10-25 warn; >25 fail (needs expanded Promoters row; skipped if unavailable) |
| 1.10 | Credit rating | Latest rating action | Downgrade fails (needs manual/LLM read; not automated in v1) |

## Gate 2: Business quality
| # | Rule | Formula | Pass / Warn / Fail |
|---|---|---|---|
| 2.1 | ROCE level | Latest ROCE % | >=20 strong; 15-20 pass; 10-15 warn; <10 fail |
| 2.2 | ROCE consistency | Median ROCE 5 yrs; years below 10% | Median >=15 and zero bad years passes |
| 2.3 | ROCE trend | Latest minus 5-yr average | Drop >5 pts warns; >10 fails |
| 2.4 | ROE | Last Year ROE and 3-yr ROE | >=15 pass; <10 fail |
| 2.5 | ROE honesty | ROE far above ROCE with D/E > 0.5 | Warn |
| 2.6 | Operating margin | TTM OPM vs its 5-yr median | Within 3 pts passes; 3-5 below is neutral; >5 below warns |
| 2.7 | Margin stability | Std-dev of annual OPM, 5 yrs | <4 pts passes; 4-6 neutral; >6 warns |
| 2.8 | Working capital | Cash Conversion Cycle vs 3 yrs ago | Up >25% warns |
| 2.9 | Receivables / inventory | Debtor Days, Inventory Days vs 3 yrs ago | Either up >30% warns |

## Gate 3: Growth
| # | Rule | Formula | Pass / Warn / Fail |
|---|---|---|---|
| 3.1 | Sales growth | Compounded sales growth, 3 yr and 5 yr | Both >=10 pass; either <5 warns |
| 3.2 | Profit growth | Compounded profit growth, 3 yr and 5 yr | Both >=10 pass; either <5 warns |
| 3.3 | Momentum | TTM sales and profit growth | Both >=10 pass |
| 3.4 | Latest quarter | YoY sales and profit growth | Sales >=10 and profit >0 passes |
| 3.5 | Streak | Consecutive quarters of positive YoY profit growth | >=3 bonus |
| 3.6 | Operating leverage | 3-yr profit growth >= sales growth | Bonus |
| 3.7 | Earnings shocks | Any year in last 5 with profit down >25% | Warn |

## Gate 4: Valuation
| # | Rule | Formula | Pass / Warn / Fail |
|---|---|---|---|
| 4.1 | P/E vs peers | Stock P/E / peer-table median P/E | <=1.5x pass; 1.5-2x warn; >2x fail |
| 4.2 | PEG | P/E / 3-yr profit growth % | <1 cheap; 1-2 fair; >2 expensive; growth <=0 is N/A (treated as expensive) |
| 4.3 | Own history | P/E vs own 5-yr median | Phase 2 (needs PE chart data) |
| 4.4 | Dividend sanity | Payout % | 20-70% healthy (info) |

## Gate 5: Ownership
| # | Rule | Formula | Pass / Warn / Fail |
|---|---|---|---|
| 5.1 | Promoter stake | Latest % and change over 8 quarters | >=40 with change >= -2 passes; drop >5 pts fails |
| 5.2 | Institutions | (FII + DII) change over 4 and 8 quarters | Rising bonus; falling >5 pts warns |
| 5.3 | Retail crowding | Shareholder count trend | Info only |

## Gate 6: Balance-sheet bonus
Reserves rising every year; CFO exceeds investing outflow (self-funded growth); Fixed Assets + CWIP growing while ROCE holds; Investments > Borrowings (net cash).

## Gate 7: Judgment (not rule-based, future)
Latest news, concall summary, rating changes, government/industry stance -> bullish / neutral / bearish tag, run only on survivors.

## Scoring
Quality (Gate 2) 30, Growth (Gate 3) 25, Safety and cash (Gate 1 + Gate 6) 20, Valuation (Gate 4) 15, Ownership (Gate 5) 10. Within a block the score is the average of its rules' points x the block maximum. Points per rule: pass or bonus 1.0, neutral ("ok") 0.6, warn 0.3, fail 0. Info and skipped rules are not scored. Gate 6 rules count inside the Safety block. Gate 0-2 fails are hard rejects regardless of score.

## Caveats
- Sector norms differ; cyclicals (metals, power) need through-the-cycle averages.
- screener.in figures are machine-processed; rows can be blank (e.g. TTM tax %).
- Rate-limit requests and respect screener.in terms of use.
- Worked example (Asian Paints, 5 Oct 2026): scores **PASS 81** (quality 30/30, safety 17.7/20, ownership 10/10, growth 16.1/25, valuation 7.5/15). Flags: rising debt in FY26, weak 3-yr growth, a 33% profit drop in FY25, PEG 23. Good business, expensive and slow lately - the score reflects mostly quality.

## Running it
The daily `build_final_watchlist.py` runs this automatically and adds the columns and per-symbol sheets to the watchlist Excel (`--no-fundamentals` skips, `--refresh-fundamentals` ignores the day's cache). To run it on its own against an existing watchlist:
```bash
cd simple-trader-api
python scripts/fundamental_screen.py                 # newest *_final_watchlist.xlsx
python scripts/fundamental_screen.py path/to/list.xlsx --delay 2 --refresh
```
The standalone command only fetches and prints verdicts. The Excel output comes from `build_final_watchlist.py`: page 1 (Watchlist) gets Fundamental Verdict, Score, block scores, Industry and a Key Note, and the symbol cell is a hyperlink to that stock's own sheet. Each symbol sheet (named after the symbol, with a link back) shows the verdict banner, block scores, key figures, the technical status, a 3-4 line summary and every rule as Check / Value / Result (Pass, Bonus, Neutral, Warn, Fail, Fail - Reject, Info, Not checked), grouped by gate. Parsed pages are cached per day in `data/fundamentals/{date}/` (gitignored).

## Implementation notes (v1)
- Fetches `screener.in/company/{SYMBOL}/consolidated/`; if that has < 5 years or < 5 quarters of data (empty or recently consolidated), it also fetches standalone and keeps whichever has more history. The basis used is stored in the cached JSON.
- Peer median P/E comes from screener's peers endpoint (rule 4.1).
- Banks, NBFCs and insurers are marked FINANCIAL and not scored. Symbols not found on screener.in are marked NO DATA.
- Not automated yet: promoter pledging (1.9), credit rating (1.10), own-history P/E (4.3), and Gate 7 news/government stance.
- Known tuning questions: the Rs 5,000 Cr market-cap floor (0.2) rejects small caps on size alone; the score can still say PASS with several safety warnings.
