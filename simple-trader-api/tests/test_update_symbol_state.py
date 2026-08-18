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
