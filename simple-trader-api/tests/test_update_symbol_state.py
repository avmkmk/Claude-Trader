"""Tests for update_symbol_state.py"""
from scripts.update_symbol_state import resolve_cap_info, merge_new_results, load_state


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


def test_transient_skip_on_tracked_reclaimed_does_not_clobber_entry():
    # Critical fix: scan_step_c.mjs's TRANSIENT_SKIP_REASONS (ohlcv_error,
    # error, strategy_not_found, missing_live_ath, insufficient_history,
    # stale_data_after_retries) are read glitches, not real analysis
    # outcomes. A transient skip on a tracked reclaimed symbol must not
    # overwrite entry_price/entry_date with a bare "skip" - that would make
    # the symbol permanently unreachable, since build_check_list.py only
    # re-checks stored reclaimed/approaching verdicts (plus stored transient
    # skips - but only if it's still recorded as one).
    state = {
        "HELDCO": {
            "verdict": "reclaimed", "cap_size": "mid", "market_cap_cr": 8000,
            "entry_price": 250.0, "entry_date": "2026-01-15",
            "distance_from_entry_pct": 3.2, "last_checked": "2026-08-18",
        }
    }
    new_details = [{"symbol": "HELDCO", "verdict": "skip", "reason": "error"}]
    candidates = []

    merged = merge_new_results(state, new_details, candidates, "2026-08-19")

    assert merged["HELDCO"]["verdict"] == "reclaimed"
    assert merged["HELDCO"]["entry_price"] == 250.0
    assert merged["HELDCO"]["entry_date"] == "2026-01-15"
    assert merged["HELDCO"]["distance_from_entry_pct"] == 3.2
    assert merged["HELDCO"]["last_checked"] == "2026-08-19"


def test_entry_price_preserved_on_recheck_with_same_entry_date():
    # Important fix: scan_step_c.mjs re-derives entry_price from a capped
    # 500-bar OHLCV window on every re-check - a bad bar-match could
    # silently drift a held position's true (historical) entry price. If
    # the incoming result is the same trade (same entry_date) as what's
    # already stored, the OLD entry_price wins, and distance_from_entry_pct
    # is recomputed from it and the new close - not trusted from the
    # incoming (potentially wrong) result.
    state = {
        "HELDCO": {
            "verdict": "reclaimed", "cap_size": "mid", "market_cap_cr": 8000,
            "entry_price": 100.0, "entry_date": "2026-01-15",
            "distance_from_entry_pct": 5.0, "last_checked": "2026-08-18",
        }
    }
    new_details = [{
        "symbol": "HELDCO", "verdict": "reclaimed",
        "entry_date": "2026-01-15", "entry_price": 137.5,  # wrongly re-derived
        "distance_from_entry_pct": 20.0,  # would-be-wrong value from bad entry_price
        "close": 110.0,
    }]
    candidates = []

    merged = merge_new_results(state, new_details, candidates, "2026-08-19")

    assert merged["HELDCO"]["entry_price"] == 100.0
    assert merged["HELDCO"]["distance_from_entry_pct"] == round(((110.0 - 100.0) / 100.0) * 100, 2)
    assert merged["HELDCO"]["last_checked"] == "2026-08-19"


def test_entry_price_not_preserved_when_entry_date_differs():
    # A different entry_date means a genuinely new trade (e.g. stopped out
    # and re-entered) - the fresh entry_price must be used, not the old one.
    state = {
        "HELDCO": {
            "verdict": "reclaimed", "cap_size": "mid", "market_cap_cr": 8000,
            "entry_price": 100.0, "entry_date": "2026-01-15",
        }
    }
    new_details = [{
        "symbol": "HELDCO", "verdict": "reclaimed",
        "entry_date": "2026-02-01", "entry_price": 120.0,
        "distance_from_entry_pct": 1.0, "close": 121.2,
    }]
    candidates = []

    merged = merge_new_results(state, new_details, candidates, "2026-08-19")

    assert merged["HELDCO"]["entry_price"] == 120.0
    assert merged["HELDCO"]["entry_date"] == "2026-02-01"
    assert merged["HELDCO"]["distance_from_entry_pct"] == 1.0


def test_load_state_returns_empty_dict_on_missing_file(tmp_path):
    missing_path = tmp_path / "does_not_exist.json"
    assert load_state(str(missing_path)) == {}
