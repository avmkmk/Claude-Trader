# Daily ATH Scan Re-check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the staleness gap in the daily ATH scan routine — already-tracked Reclaimed/Approaching symbols currently never get re-validated against the live TradingView chart — and package the full routine as a `/daily-ath-scan` skill.

**Architecture:** A new Step A2 script (`build_check_list.py`) diffs today's Chartink candidates against `symbol_state.json` and unions in every symbol currently `reclaimed` or `approaching`, producing the actual list Step C checks each run. `update_symbol_state.py` gets a cap-tier fallback fix so a re-checked symbol (not freshly scraped today) doesn't get its market-cap tier silently reset to unknown. The existing Step A+B (`scan_candidates.py`), Step C (`scan_step_c.mjs`), and Step D (`build_final_watchlist.py`) scripts are otherwise unchanged; a new skill file glues the full sequence together.

**Tech Stack:** Python 3 + pytest (existing project convention, see `simple-trader-api/tests/test_update_metadata_db.py`), Node.js (`scan_step_c.mjs`, unchanged), openpyxl (unchanged).

**Spec:** `docs/superpowers/specs/2026-08-11-daily-ath-scan-routine-design.md` (see the "Revision (2026-08-18)" section this plan implements)

## Global Constraints

- `symbol_state.json` stays at `simple-trader-api/data/daily_scans/symbol_state.json` — no schema changes.
- `scan_step_c.mjs`'s only requirement of its input candidates list is a `symbol` key per entry — do not change its interface.
- `update_symbol_state.py`'s CLI signature stays `<new_verdicts_details.json> <candidates.json> <scan_date>` — unchanged, only internal cap-lookup logic changes.
- `build_final_watchlist.py` is not modified — it already reads the entire state file every run.
- Tests run via `python -m pytest tests/ -v` from `simple-trader-api/` (confirmed working: `scripts/` and `lib/` are importable as namespace packages from that cwd, no `__init__.py` needed, matching the existing `test_update_metadata_db.py` convention).

---

### Task 1: `build_check_list.py` — Step A2 diff/union script

**Files:**
- Create: `simple-trader-api/scripts/build_check_list.py`
- Test: `simple-trader-api/tests/test_build_check_list.py`

**Interfaces:**
- Produces: `build_check_list(candidates: list[dict], state: dict) -> tuple[list[dict], dict]` — pure function, no I/O. `candidates` entries are dicts with at least a `"symbol"` key (today's `scan_candidates.py` output). `state` is the parsed `symbol_state.json` dict (keyed by symbol). Returns `(to_check, summary)` where `to_check` is a deduplicated list of candidate-shaped dicts and `summary` is `{"new": int, "re_checked": int, "total": int}`.
- Produces: `run(candidates_path: str, output_path: str, state_path: str = STATE_PATH) -> dict` — does the file I/O, calls `build_check_list`, writes `output_path`, prints the summary line, returns the summary dict.
- Produces: `main()` — CLI entrypoint, `python build_check_list.py <candidates.json> <output.json>`, uses the real `STATE_PATH`.

- [ ] **Step 1: Write the failing tests for `build_check_list()`**

Create `simple-trader-api/tests/test_build_check_list.py`:

```python
"""Tests for build_check_list.py"""
from scripts.build_check_list import build_check_list


def test_new_candidate_not_in_state_is_included():
    candidates = [{"symbol": "FRESHCO", "cap_size": "large"}]
    state = {}
    to_check, summary = build_check_list(candidates, state)
    assert to_check == [{"symbol": "FRESHCO", "cap_size": "large"}]
    assert summary == {"new": 1, "re_checked": 0, "total": 1}


def test_tracked_reclaimed_symbol_included_even_if_not_in_todays_candidates():
    candidates = []
    state = {"OLDCO": {"verdict": "reclaimed", "entry_price": 100}}
    to_check, summary = build_check_list(candidates, state)
    assert to_check == [{"symbol": "OLDCO"}]
    assert summary == {"new": 0, "re_checked": 1, "total": 1}


def test_tracked_approaching_symbol_included():
    candidates = []
    state = {"OLDCO": {"verdict": "approaching"}}
    to_check, summary = build_check_list(candidates, state)
    assert summary == {"new": 0, "re_checked": 1, "total": 1}


def test_tracked_skip_symbol_excluded():
    candidates = []
    state = {"OLDCO": {"verdict": "skip", "reason": "outside_band"}}
    to_check, summary = build_check_list(candidates, state)
    assert to_check == []
    assert summary == {"new": 0, "re_checked": 0, "total": 0}


def test_symbol_both_new_and_tracked_not_double_counted():
    # HELDCO is already tracked as reclaimed AND happens to reappear in
    # today's fresh Chartink scrape - must only be checked once, using
    # today's fresh data (not the bare {"symbol": ...} fallback).
    candidates = [{"symbol": "HELDCO", "cap_size": "mid"}]
    state = {"HELDCO": {"verdict": "reclaimed"}}
    to_check, summary = build_check_list(candidates, state)
    assert to_check == [{"symbol": "HELDCO", "cap_size": "mid"}]
    assert summary == {"new": 0, "re_checked": 1, "total": 1}


def test_empty_state_treats_everything_as_new():
    candidates = [{"symbol": "A"}, {"symbol": "B"}]
    state = {}
    to_check, summary = build_check_list(candidates, state)
    assert summary == {"new": 2, "re_checked": 0, "total": 2}
```

- [ ] **Step 2: Run the tests to verify they fail**

From `simple-trader-api/`:
```bash
python -m pytest tests/test_build_check_list.py -v
```
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'scripts.build_check_list'` (the file doesn't exist yet).

- [ ] **Step 3: Write `build_check_list.py`**

Create `simple-trader-api/scripts/build_check_list.py`:

```python
"""
Daily ATH scan routine - Step A2 (diff/union).

Determines which symbols need a live TradingView check today: symbols
Chartink surfaced today for the first time (per scan_candidates.py's
output), plus any symbol already tracked in symbol_state.json as
"reclaimed" or "approaching". Without this, a stop-out or a fresh
RECLAIM #N re-entry on an already-tracked symbol is never re-checked and
silently goes stale - see docs/superpowers/specs/
2026-08-11-daily-ath-scan-routine-design.md, Revision (2026-08-18).

Usage:
    python scripts/build_check_list.py <candidates.json> <output.json>
"""
import json
import os
import sys

STATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "daily_scans", "symbol_state.json",
)

RECHECK_VERDICTS = {"reclaimed", "approaching"}


def load(path):
    with open(path) as f:
        return json.load(f)


def load_state(path):
    try:
        return load(path)
    except FileNotFoundError:
        return {}


def build_check_list(candidates, state):
    candidates_by_symbol = {c["symbol"]: c for c in candidates}
    state_symbols = set(state.keys())

    genuinely_new = [c["symbol"] for c in candidates if c["symbol"] not in state_symbols]
    already_tracked = [
        symbol for symbol, r in state.items()
        if r.get("verdict") in RECHECK_VERDICTS
    ]

    to_check_symbols = list(dict.fromkeys(genuinely_new + already_tracked))
    to_check = [candidates_by_symbol.get(symbol, {"symbol": symbol}) for symbol in to_check_symbols]

    summary = {
        "new": len(genuinely_new),
        "re_checked": len(already_tracked),
        "total": len(to_check_symbols),
    }
    return to_check, summary


def run(candidates_path, output_path, state_path=STATE_PATH):
    candidates = load(candidates_path)
    state = load_state(state_path)

    to_check, summary = build_check_list(candidates, state)

    with open(output_path, "w") as f:
        json.dump(to_check, f, indent=2)

    print(f"new={summary['new']} re-checked={summary['re_checked']} total={summary['total']}")
    print(f"Wrote {output_path}")
    return summary


def main():
    if len(sys.argv) != 3:
        print("Usage: python build_check_list.py <candidates.json> <output.json>")
        sys.exit(1)
    run(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python -m pytest tests/test_build_check_list.py -v
```
Expected: 6 passed.

- [ ] **Step 5: Write the failing tests for `run()`'s file I/O (missing state file, mixed new/re-checked output)**

Append to `simple-trader-api/tests/test_build_check_list.py`:

```python
import json as json_module

from scripts.build_check_list import run


def test_run_treats_missing_state_file_as_empty(tmp_path):
    candidates_path = tmp_path / "candidates.json"
    candidates_path.write_text(json_module.dumps([{"symbol": "A"}, {"symbol": "B"}]))
    output_path = tmp_path / "to_check.json"
    missing_state_path = tmp_path / "does_not_exist.json"

    summary = run(str(candidates_path), str(output_path), state_path=str(missing_state_path))

    assert summary == {"new": 2, "re_checked": 0, "total": 2}
    written = json_module.loads(output_path.read_text())
    assert written == [{"symbol": "A"}, {"symbol": "B"}]


def test_run_writes_union_of_new_and_tracked(tmp_path):
    candidates_path = tmp_path / "candidates.json"
    candidates_path.write_text(json_module.dumps([{"symbol": "NEWCO", "cap_size": "large"}]))
    state_path = tmp_path / "symbol_state.json"
    state_path.write_text(json_module.dumps({"HELDCO": {"verdict": "reclaimed"}}))
    output_path = tmp_path / "to_check.json"

    summary = run(str(candidates_path), str(output_path), state_path=str(state_path))

    written = json_module.loads(output_path.read_text())
    symbols = {c["symbol"] for c in written}
    assert symbols == {"NEWCO", "HELDCO"}
    assert summary == {"new": 1, "re_checked": 1, "total": 2}
```

- [ ] **Step 6: Run the tests to verify they pass**

```bash
python -m pytest tests/test_build_check_list.py -v
```
Expected: 8 passed.

- [ ] **Step 7: Commit**

```bash
git add simple-trader-api/scripts/build_check_list.py simple-trader-api/tests/test_build_check_list.py
git commit -m "feat: add build_check_list.py to re-check tracked Reclaimed/Approaching symbols"
```

---

### Task 2: Fix `update_symbol_state.py` cap-tier fallback bug

**Files:**
- Modify: `simple-trader-api/scripts/update_symbol_state.py` (full file, currently 47 lines)
- Test: `simple-trader-api/tests/test_update_symbol_state.py`

**Interfaces:**
- Consumes: nothing from Task 1 (independent fix; both tasks touch different files).
- Produces: `resolve_cap_info(symbol: str, cap_by_symbol: dict, existing_state: dict) -> tuple[str, float | None]` — returns `(cap_size, market_cap_cr)`.
- Produces: `merge_new_results(state: dict, new_details: list[dict], candidates: list[dict], scan_date: str) -> dict` — mutates and returns `state`.

- [ ] **Step 1: Write the failing tests**

Create `simple-trader-api/tests/test_update_symbol_state.py`:

```python
"""Tests for update_symbol_state.py"""
from scripts.update_symbol_state import resolve_cap_info, merge_new_results


def test_uses_todays_candidate_cap_info_when_present():
    cap_by_symbol = {"FRESHCO": {"symbol": "FRESHCO", "cap_size": "large", "market_cap_cr": 50000}}
    existing_state = {}
    cap_size, market_cap_cr = resolve_cap_info("FRESHCO", cap_by_symbol, existing_state)
    assert cap_size == "large"
    assert market_cap_cr == 50000


def test_falls_back_to_existing_state_when_not_in_todays_candidates():
    # The bug fix: a symbol re-checked today (build_check_list.py) but not
    # freshly scraped by Chartink today must keep its previously known cap
    # tier, not silently reset to unknown/null.
    cap_by_symbol = {}
    existing_state = {"OLDCO": {"cap_size": "mid", "market_cap_cr": 8000, "verdict": "reclaimed"}}
    cap_size, market_cap_cr = resolve_cap_info("OLDCO", cap_by_symbol, existing_state)
    assert cap_size == "mid"
    assert market_cap_cr == 8000


def test_defaults_to_unknown_when_absent_from_both():
    cap_size, market_cap_cr = resolve_cap_info("NEWCO", {}, {})
    assert cap_size == "unknown"
    assert market_cap_cr is None


def test_merge_new_results_preserves_cap_for_recheck_symbol():
    state = {
        "OLDCO": {
            "cap_size": "small", "market_cap_cr": 2000, "verdict": "reclaimed",
            "entry_price": 100, "entry_date": "2026-01-01",
        }
    }
    new_details = [{"symbol": "OLDCO", "verdict": "skip", "reason": "outside_band"}]
    candidates = []  # OLDCO was not freshly scraped today

    merged = merge_new_results(state, new_details, candidates, "2026-08-19")

    assert merged["OLDCO"]["verdict"] == "skip"
    assert merged["OLDCO"]["cap_size"] == "small"
    assert merged["OLDCO"]["market_cap_cr"] == 2000
    assert merged["OLDCO"]["last_checked"] == "2026-08-19"


def test_merge_new_results_uses_fresh_cap_for_new_symbol():
    state = {}
    new_details = [{"symbol": "NEWCO", "verdict": "approaching"}]
    candidates = [{"symbol": "NEWCO", "cap_size": "large", "market_cap_cr": 90000}]

    merged = merge_new_results(state, new_details, candidates, "2026-08-19")

    assert merged["NEWCO"]["cap_size"] == "large"
    assert merged["NEWCO"]["market_cap_cr"] == 90000
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
python -m pytest tests/test_update_symbol_state.py -v
```
Expected: FAIL/ERROR — `ImportError: cannot import name 'resolve_cap_info'` (functions don't exist yet in the current file).

- [ ] **Step 3: Rewrite `update_symbol_state.py`**

Replace the full contents of `simple-trader-api/scripts/update_symbol_state.py`:

```python
"""
Merges today's fresh Step C results into the persistent symbol-state
file, tagging each with market cap and today's date.

Results cover two kinds of symbols (see build_check_list.py): those
Chartink surfaced today for the first time, and any symbol already
tracked as "reclaimed" or "approaching" that got re-checked today. The
second group is NOT present in today's candidates.json (they weren't
freshly scraped), so their cap tier is carried forward from the existing
state entry rather than reset to unknown - see
docs/superpowers/specs/2026-08-11-daily-ath-scan-routine-design.md,
Revision (2026-08-18).

Usage:
    python scripts/update_symbol_state.py <new_verdicts_details.json> <candidates.json> <scan_date>
"""
import json
import sys

STATE_PATH = "data/daily_scans/symbol_state.json"


def load(path):
    with open(path) as f:
        return json.load(f)


def resolve_cap_info(symbol, cap_by_symbol, existing_state):
    if symbol in cap_by_symbol:
        cap = cap_by_symbol[symbol]
        return cap.get("cap_size", "unknown"), cap.get("market_cap_cr")
    existing = existing_state.get(symbol)
    if existing:
        return existing.get("cap_size", "unknown"), existing.get("market_cap_cr")
    return "unknown", None


def merge_new_results(state, new_details, candidates, scan_date):
    cap_by_symbol = {c["symbol"]: c for c in candidates}
    for r in new_details:
        cap_size, market_cap_cr = resolve_cap_info(r["symbol"], cap_by_symbol, state)
        state[r["symbol"]] = {
            **r,
            "cap_size": cap_size,
            "market_cap_cr": market_cap_cr,
            "last_checked": scan_date,
        }
    return state


def main():
    if len(sys.argv) != 4:
        print("Usage: python update_symbol_state.py <new_verdicts_details.json> <candidates.json> <scan_date>")
        sys.exit(1)
    new_details_path, candidates_path, scan_date = sys.argv[1], sys.argv[2], sys.argv[3]

    state = load(STATE_PATH)
    candidates = load(candidates_path)
    new_details = load(new_details_path)

    state = merge_new_results(state, new_details, candidates, scan_date)

    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

    print(f"State file now has {len(state)} symbols")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python -m pytest tests/test_update_symbol_state.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Run the full test suite to confirm no regressions**

```bash
python -m pytest tests/ -v
```
Expected: all tests pass (existing `test_data_fetcher.py`, `test_update_metadata_db.py` unaffected; plus the two new test files).

- [ ] **Step 6: Commit**

```bash
git add simple-trader-api/scripts/update_symbol_state.py simple-trader-api/tests/test_update_symbol_state.py
git commit -m "fix: preserve cap tier for re-checked symbols not in today's candidates"
```

---

### Task 3: Package the routine as the `/daily-ath-scan` skill

**Files:**
- Create: `.claude/skills/daily-ath-scan/SKILL.md`

**Interfaces:**
- Consumes: `build_check_list.py`'s CLI (`python build_check_list.py <candidates.json> <output.json>`, from Task 1) and the fixed `update_symbol_state.py` CLI (unchanged signature, from Task 2). Also consumes the existing, unmodified CLIs of `scan_candidates.py`, `scan_step_c.mjs`, and `build_final_watchlist.py`.
- Produces: nothing consumed by other tasks — this is the terminal integration point.

**Note:** `.claude/` is blanket-gitignored in this repo's root `.gitignore` (line 204). Before Step 4's `git add` can work, `.claude/skills/` needs a negation exception added to `.gitignore` (mirroring the existing `!simple-trader-api/lib/` pattern at line 30) — add `!.claude/skills/` right after the `.claude/` line. Do this as part of Step 2, in the same commit as the skill file itself.

- [ ] **Step 1: Verify the exact CLI usage strings this skill will document**

From `simple-trader-api/`, confirm each script's usage line matches what the skill will tell the user to run. **Do not include `scan_candidates.py` here** — unlike the other three, its `main()` has no argv-count guard, so running it with no arguments doesn't print a usage line, it immediately starts a real Selenium scrape against Chartink:
```bash
python scripts/build_check_list.py 2>&1 | head -1
python scripts/update_symbol_state.py 2>&1 | head -1
python scripts/build_final_watchlist.py 2>&1 | head -1
```
Expected: each prints its `Usage: ...` line (called with no args) matching the commands used in Step 2 below. `build_check_list.py`'s usage line comes from Task 1; the other two are pre-existing and were confirmed while writing this plan's Task 2 code — re-run here only to catch drift if that task changed anything unexpectedly. For `scan_candidates.py`, just visually confirm its module docstring's `Usage: python scripts/scan_candidates.py` (no arguments) matches Step 1 of the skill below — don't execute it.

- [ ] **Step 2: Fix `.gitignore` and write the skill file**

In `.gitignore`, immediately after the `.claude/` line (currently line 204, under the "# Claude Code specific" comment), add:
```
!.claude/skills/
```

Create `.claude/skills/daily-ath-scan/SKILL.md`:

```markdown
---
name: daily-ath-scan
description: Run the daily ATH Reclaim scan routine - scrapes Chartink screeners, re-checks already-tracked Reclaimed/Approaching symbols against the live TradingView chart, and rebuilds the dated watchlist Excel. Use when the user asks to run the daily ATH scan, refresh the ATH reclaim watchlist, or check today's chartink candidates.
---

# Daily ATH Scan Routine

Full design: `docs/superpowers/specs/2026-08-11-daily-ath-scan-routine-design.md` — read this first if anything below is unclear, especially the "Revision (2026-08-18)" section this skill packages.

Runs Steps A/B/A2/C/D end to end: scrape Chartink → enrich with market cap/price → build today's live-check list (new candidates + already-tracked Reclaimed/Approaching symbols) → read live Pine strategy state off the TradingView desktop chart → rebuild the dated watchlist Excel.

## Steps

`{today}` is today's date as `YYYY-MM-DD`.

1. **Scrape + enrich (Step A+B)** — from `simple-trader-api/`:
   ```bash
   python scripts/scan_candidates.py
   ```
   Produces `data/daily_scans/{today}_candidates.json`.

2. **Build today's check list (Step A2)** — from `simple-trader-api/`:
   ```bash
   python scripts/build_check_list.py data/daily_scans/{today}_candidates.json data/daily_scans/{today}_to_check.json
   ```
   Prints `new=N re-checked=M total=T`. `re-checked` is every symbol currently `reclaimed` or `approaching` in `symbol_state.json` — report this count to the user before the live step, since it drives how long Step 4 takes.

3. **Ensure TradingView Desktop is running with CDP.** Check first:
   ```bash
   curl -s http://localhost:9222/json/version
   ```
   If that fails, launch it (from the repo root):
   ```bash
   powershell -ExecutionPolicy Bypass -File "tradingview-mcp-jackson/scripts/launch_tv_debug.ps1"
   ```
   Wait for the script to report `CDP ready`.

4. **Live Pine state read (Step C)** — from `tradingview-mcp-jackson/`, using **absolute paths** into `simple-trader-api/data/daily_scans/` since this runs from a different directory:
   ```bash
   node scan_step_c.mjs "<repo-root>/simple-trader-api/data/daily_scans/{today}_to_check.json" "<repo-root>/simple-trader-api/data/daily_scans/{today}_verdicts.json"
   ```
   Drives the TradingView chart via CDP for every symbol in the check list — no computer-use, no screenshots, it reads Pine's own study values and labels directly. Produces `{today}_verdicts.json` and `{today}_verdicts_details.json`. This is the slow step — expect roughly a few seconds per symbol.

5. **Merge into persistent state** — from `simple-trader-api/`:
   ```bash
   python scripts/update_symbol_state.py data/daily_scans/{today}_verdicts_details.json data/daily_scans/{today}_candidates.json {today}
   ```
   Updates `data/daily_scans/symbol_state.json` in place. Prints the new total symbol count.

6. **Build the watchlist Excel** — from `simple-trader-api/`:
   ```bash
   python scripts/build_final_watchlist.py {today} data/daily_scans/{today}_final_watchlist.xlsx
   ```
   Reads the *entire* `symbol_state.json` (not just today's touched symbols), so anything that flipped to `skip` during today's re-check (e.g. a stop-out) is automatically excluded. Prints Reclaimed/Approaching counts.

7. **Report and send.** Summarize: candidates scraped, new vs re-checked counts, final Reclaimed/Approaching counts. Send the Excel file at `simple-trader-api/data/daily_scans/{today}_final_watchlist.xlsx` to the user.

## Notes

- If Step 2 reports `re-checked=0` and this is the very first run (`symbol_state.json` doesn't exist yet), `build_check_list.py` treats a missing state file as empty — every candidate is `new`. This is expected, not an error.
- Symbols manually excluded from the watchlist live in `simple-trader-api/data/daily_scans/manual_exclusions.json` — unaffected by this routine.
- If Step 4 fails partway through, its rejection cache (`_rejection_cache.json`, written next to the verdicts output) means already-processed `skip` verdicts won't be re-driven against the live chart again for 3 days on a re-run — safe to just re-run Step 4 with the same input file.
```

- [ ] **Step 3: Verify the file is well-formed and not gitignored**

```bash
git check-ignore -v .claude/skills/daily-ath-scan/SKILL.md
```
Expected: no output and a non-zero exit code (meaning it is NOT ignored — confirms the `.gitignore` fix from Step 2 worked). If this instead prints a match, the negation pattern didn't take effect; double check it was placed after (not before) the `.claude/` line it's meant to override.

```bash
python -c "import yaml, re; content = open('.claude/skills/daily-ath-scan/SKILL.md').read(); fm = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL).group(1); data = yaml.safe_load(fm); assert 'name' in data and 'description' in data; print('frontmatter OK:', data['name'])"
```
Expected: `frontmatter OK: daily-ath-scan`. (If `yaml` isn't installed in the active venv, `pip install pyyaml` first, or just visually confirm the frontmatter block has `name:` and `description:` keys between the `---` markers.)

- [ ] **Step 4: Commit**

```bash
git add .gitignore .claude/skills/daily-ath-scan/SKILL.md
git commit -m "feat: package daily ATH scan routine as /daily-ath-scan skill"
```

---

## Final Verification

Not independently unit-testable end-to-end (live TradingView desktop + live Chartink dependency, same limitation the spec already documents for Step C). After all three tasks are committed:

1. Run the full test suite once more from `simple-trader-api/`: `python -m pytest tests/ -v` — confirm all tests pass (no regressions from either script change).
2. On a real morning run, invoke `/daily-ath-scan` and confirm: Step 2's `re-checked` count roughly matches the current count of `reclaimed`+`approaching` entries in `symbol_state.json`; the final Excel's Reclaimed section reflects any real stop-out that happened since the last run (a symbol that should have flipped to `skip` is actually gone from the sheet).
