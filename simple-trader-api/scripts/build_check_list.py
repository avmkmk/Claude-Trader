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

# Must stay in sync with TRANSIENT_SKIP_REASONS in
# tradingview-mcp-jackson/scan_step_c.mjs (~line 56) - these are read
# glitches, not real analysis outcomes, so a symbol stuck on one of these
# reasons must keep getting re-checked rather than being treated like a
# genuine (non-transient) skip such as "outside_band" or "not_primed".
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


def build_check_list(candidates, state):
    candidates_by_symbol = {c["symbol"]: c for c in candidates}
    state_symbols = set(state.keys())

    genuinely_new = list(dict.fromkeys(
        c["symbol"] for c in candidates if c["symbol"] not in state_symbols
    ))
    already_tracked = [
        symbol for symbol, r in state.items()
        if r.get("verdict") in RECHECK_VERDICTS
        or (r.get("verdict") == "skip" and r.get("reason") in TRANSIENT_SKIP_REASONS)
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
