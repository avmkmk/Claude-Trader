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


def test_tracked_symbol_reappearing_in_candidates_uses_fresh_data():
    # HELDCO is already tracked as reclaimed AND happens to reappear in
    # today's fresh Chartink scrape - must only be checked once, using
    # today's fresh data (not the bare {"symbol": ...} fallback).
    candidates = [{"symbol": "HELDCO", "cap_size": "mid"}]
    state = {"HELDCO": {"verdict": "reclaimed"}}
    to_check, summary = build_check_list(candidates, state)
    assert to_check == [{"symbol": "HELDCO", "cap_size": "mid"}]
    assert summary == {"new": 0, "re_checked": 1, "total": 1}


def test_tracked_skip_with_transient_reason_is_rechecked():
    # A transient-reason skip (see TRANSIENT_SKIP_REASONS - matches
    # scan_step_c.mjs's set of the same name) is a read glitch, not a real
    # analysis outcome, so it must keep being re-checked just like
    # reclaimed/approaching symbols, unlike a genuine skip.
    candidates = []
    state = {"GLITCHCO": {"verdict": "skip", "reason": "error"}}
    to_check, summary = build_check_list(candidates, state)
    assert to_check == [{"symbol": "GLITCHCO"}]
    assert summary == {"new": 0, "re_checked": 1, "total": 1}


def test_tracked_skip_with_non_transient_reason_still_excluded():
    # This part of the existing design is intentional and must not change:
    # a genuine (non-transient) skip reason like outside_band stays excluded.
    candidates = []
    state = {"OLDCO": {"verdict": "skip", "reason": "outside_band"}}
    to_check, summary = build_check_list(candidates, state)
    assert to_check == []
    assert summary == {"new": 0, "re_checked": 0, "total": 0}


def test_duplicate_candidate_symbols_deduplicated_before_counting():
    # If candidates.json ever contains a duplicate symbol, the "new" count
    # must reflect unique symbols, not raw candidate entries.
    candidates = [
        {"symbol": "DUPCO", "cap_size": "large"},
        {"symbol": "DUPCO", "cap_size": "large"},
        {"symbol": "OTHERCO", "cap_size": "mid"},
    ]
    state = {}
    to_check, summary = build_check_list(candidates, state)
    assert {c["symbol"] for c in to_check} == {"DUPCO", "OTHERCO"}
    assert len(to_check) == 2
    assert summary == {"new": 2, "re_checked": 0, "total": 2}


def test_empty_state_treats_everything_as_new():
    candidates = [{"symbol": "A"}, {"symbol": "B"}]
    state = {}
    to_check, summary = build_check_list(candidates, state)
    assert summary == {"new": 2, "re_checked": 0, "total": 2}


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
