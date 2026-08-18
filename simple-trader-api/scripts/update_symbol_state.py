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
