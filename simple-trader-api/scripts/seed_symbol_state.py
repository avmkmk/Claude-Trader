"""
Seeds the persistent symbol-state file from yesterday's session data. This
file (data/daily_scans/symbol_state.json) is the durable, never-auto-deleted
record of every symbol's last-known verdict/reason/date - separate from the
Node script's short-lived rejection cache, which has been wiped multiple
times during active debugging.

Priority per symbol (highest wins): the freshest, most-fixed-logic source
available from 2026-08-12's session.

Usage:
    python scripts/seed_symbol_state.py
"""
import json

MERGED_PATH = "data/daily_scans/2026-08-12_merged_verdicts_details.json"
RECLAIMED_RECHECK_PATH = r"C:\Users\User\AppData\Local\Temp\reclaimed_34_verdicts_details.json"
CANDIDATES_PATH = "data/daily_scans/2026-08-12_candidates.json"
STATE_PATH = "data/daily_scans/symbol_state.json"

SCAN_DATE = "2026-08-12"


def load(path):
    with open(path) as f:
        return json.load(f)


def main():
    candidates = load(CANDIDATES_PATH)
    cap_by_symbol = {c["symbol"]: c for c in candidates}

    state = {}
    for r in load(MERGED_PATH):
        state[r["symbol"]] = r
    for r in load(RECLAIMED_RECHECK_PATH):
        state[r["symbol"]] = r

    out = {}
    for symbol, r in state.items():
        cap = cap_by_symbol.get(symbol, {})
        out[symbol] = {
            **r,
            "cap_size": cap.get("cap_size", "unknown"),
            "market_cap_cr": cap.get("market_cap_cr"),
            "last_checked": SCAN_DATE,
        }

    with open(STATE_PATH, "w") as f:
        json.dump(out, f, indent=2)

    counts = {}
    for r in out.values():
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print(f"Seeded {len(out)} symbols into {STATE_PATH}: {counts}")


if __name__ == "__main__":
    main()
