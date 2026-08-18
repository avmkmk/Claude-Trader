"""
One-off: merge the several partial Step C runs from this session into a
single final watchlist, taking the most-corrected verdict available for
each symbol, tagged with market cap from candidates.json.

Priority (highest wins per symbol):
  1. skipped_38 rerun       - has the isHeld-unconditional-reclaim fix
  2. user_watchlist + retry2 - has the isHeld-unconditional-reclaim fix
  3. full 293 verdicts_details.json - label-based ground truth, but still
     had the old band cap on held positions (pre isHeld fix)

Usage:
    python scripts/merge_watchlist.py
"""
import json

CANDIDATES_PATH = "data/daily_scans/2026-08-12_candidates.json"
FULL_293_PATH = "data/daily_scans/2026-08-12_verdicts_details.json"
TEMP_DIR = r"C:\Users\User\AppData\Local\Temp"
SKIPPED_38_PATH = TEMP_DIR + r"\skipped_38_verdicts_details.json"
USER_WATCHLIST_PATH = TEMP_DIR + r"\user_watchlist_verdicts_details.json"
RETRY2_PATH = TEMP_DIR + r"\retry2_verdicts_details.json"

OUTPUT_PATH = "data/daily_scans/2026-08-12_merged_verdicts_details.json"


def load(path):
    with open(path) as f:
        return json.load(f)


def main():
    candidates = load(CANDIDATES_PATH)
    cap_by_symbol = {c["symbol"]: c for c in candidates}

    merged = {}

    # Lowest priority first, so later loads overwrite with better data.
    for d in load(FULL_293_PATH):
        merged[d["symbol"]] = d
    for d in load(USER_WATCHLIST_PATH):
        merged[d["symbol"]] = d
    for d in load(RETRY2_PATH):
        merged[d["symbol"]] = d
    for d in load(SKIPPED_38_PATH):
        merged[d["symbol"]] = d

    out = list(merged.values())
    for row in out:
        cap = cap_by_symbol.get(row["symbol"], {})
        row["cap_size"] = cap.get("cap_size", "unknown")
        row["market_cap_cr"] = cap.get("market_cap_cr")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(out, f, indent=2)

    counts = {}
    for row in out:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    print(f"Merged {len(out)} symbols: {counts}")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
