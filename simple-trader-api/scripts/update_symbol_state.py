"""
Merges today's fresh Step C results (only run for symbols new to the
Chartink screeners) into the persistent symbol-state file, tagging each
with market cap and today's date.

Usage:
    python scripts/update_symbol_state.py <new_verdicts_details.json> <candidates.json> <scan_date>
"""
import json
import sys

STATE_PATH = "data/daily_scans/symbol_state.json"


def load(path):
    with open(path) as f:
        return json.load(f)


def main():
    if len(sys.argv) != 4:
        print("Usage: python update_symbol_state.py <new_verdicts_details.json> <candidates.json> <scan_date>")
        sys.exit(1)
    new_details_path, candidates_path, scan_date = sys.argv[1], sys.argv[2], sys.argv[3]

    state = load(STATE_PATH)
    candidates = load(candidates_path)
    cap_by_symbol = {c["symbol"]: c for c in candidates}

    for r in load(new_details_path):
        cap = cap_by_symbol.get(r["symbol"], {})
        state[r["symbol"]] = {
            **r,
            "cap_size": cap.get("cap_size", "unknown"),
            "market_cap_cr": cap.get("market_cap_cr"),
            "last_checked": scan_date,
        }

    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

    print(f"State file now has {len(state)} symbols")


if __name__ == "__main__":
    main()
