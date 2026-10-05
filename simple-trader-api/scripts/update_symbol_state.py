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

Two additional invariants are enforced in merge_new_results() before any
of the above:

1. Transient chart-read glitches must never permanently evict a tracked
   reclaimed/approaching symbol. scan_step_c.mjs's TRANSIENT_SKIP_REASONS
   (see that file, ~line 56) documents these as "not a real analysis
   outcome" - always meant to be retried fresh, never cached as a real
   skip. If we let a transient skip clobber a tracked entry here, it
   would become permanently unreachable: build_check_list.py only
   re-checks symbols whose stored verdict is reclaimed/approaching (plus
   stored transient skips, see that file), so overwriting a
   reclaimed/approaching entry with a plain "skip" would take it out of
   that set for good.
2. A held position's entry_price is re-derived by scan_step_c.mjs from a
   capped 500-bar OHLCV window on every re-check (see the design spec,
   "Explicitly out of scope for this revision" - confirmed unreliable for
   trades older than that window). If this re-check is the same trade
   (same entry_date) as what's already stored, the previously recorded
   entry_price is preferred over the freshly re-derived one - the true
   entry price is historical and cannot legitimately change - and
   distance_from_entry_pct is recomputed to stay consistent with it.

Usage:
    python scripts/update_symbol_state.py <new_verdicts_details.json> <candidates.json> <scan_date>
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.paths import STATE_PATH  # noqa: E402

RECHECK_VERDICTS = {"reclaimed", "approaching"}

# Must stay in sync with TRANSIENT_SKIP_REASONS in
# tradingview-mcp-jackson/scan_step_c.mjs (~line 56) - these are read
# glitches, not real analysis outcomes.
TRANSIENT_SKIP_REASONS = {
    "strategy_not_found", "missing_live_ath", "insufficient_history",
    "stale_data_after_retries", "ohlcv_error", "error",
}


def load(path):
    with open(path) as f:
        return json.load(f)


def load_state(path):
    try:
        return load(path)
    except FileNotFoundError:
        return {}


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
        symbol = r["symbol"]
        existing = state.get(symbol)

        # Invariant 1: a transient-reason skip on a tracked reclaimed/
        # approaching symbol is a read glitch, not a real state change.
        # Just bump last_checked on the existing entry and move on -
        # don't overwrite it, so tomorrow's build_check_list.py naturally
        # retries it (its verdict is still reclaimed/approaching).
        if (
            r.get("verdict") == "skip"
            and r.get("reason") in TRANSIENT_SKIP_REASONS
            and existing is not None
            and existing.get("verdict") in RECHECK_VERDICTS
        ):
            existing["last_checked"] = scan_date
            continue

        # Invariant 2: re-checking the same held trade (same entry_date)
        # must not let a freshly re-derived entry_price silently drift
        # the stored one. Override entry_price/distance_from_entry_pct on
        # the result before it goes through the normal write path below -
        # this case still writes (unlike invariant 1), just with the
        # corrected price/distance.
        if (
            r.get("verdict") == "reclaimed"
            and existing is not None
            and existing.get("verdict") == "reclaimed"
            and existing.get("entry_price") is not None
            and r.get("entry_date") is not None
            and existing.get("entry_date") == r.get("entry_date")
        ):
            entry_price = existing["entry_price"]
            r = dict(r)
            r["entry_price"] = entry_price
            close = r.get("close")
            if close is not None:
                r["distance_from_entry_pct"] = round(((close - entry_price) / entry_price) * 100, 2)

        cap_size, market_cap_cr = resolve_cap_info(symbol, cap_by_symbol, state)
        state[symbol] = {
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

    state = load_state(STATE_PATH)
    candidates = load(candidates_path)
    new_details = load(new_details_path)

    state = merge_new_results(state, new_details, candidates, scan_date)

    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

    print(f"State file now has {len(state)} symbols")


if __name__ == "__main__":
    main()
