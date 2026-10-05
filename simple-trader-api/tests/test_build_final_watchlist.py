"""Tests for build_final_watchlist.py's ranking logic."""
from scripts.build_final_watchlist import compute_combined_rank


def test_ranks_eligible_symbols_by_win_rate_and_profit_factor():
    rows = [
        {"symbol": "A", "ranking_eligible": True, "win_rate_pct": 80.0, "profit_factor": 2.0},
        {"symbol": "B", "ranking_eligible": True, "win_rate_pct": 60.0, "profit_factor": 10.0},
        {"symbol": "C", "ranking_eligible": True, "win_rate_pct": 90.0, "profit_factor": 8.0},
    ]
    compute_combined_rank(rows)
    ranks = {r["symbol"]: r["combined_rank"] for r in rows}
    # C: best win_rate (rank 0) + 2nd best profit_factor (rank 1) -> 0.5
    # A: 2nd best win_rate (rank 1) + worst profit_factor (rank 2) -> 1.5
    # B: worst win_rate (rank 2) + best profit_factor (rank 0) -> 1.0
    assert ranks["C"] < ranks["B"] < ranks["A"]


def test_ineligible_symbols_get_null_rank():
    rows = [
        {"symbol": "A", "ranking_eligible": True, "win_rate_pct": 80.0, "profit_factor": 2.0},
        {"symbol": "B", "ranking_eligible": False, "win_rate_pct": None, "profit_factor": None},
    ]
    compute_combined_rank(rows)
    assert rows[0]["combined_rank"] is not None
    assert rows[1]["combined_rank"] is None


def test_empty_list_does_not_error():
    rows = []
    compute_combined_rank(rows)
    assert rows == []


def test_all_ineligible_all_null():
    rows = [
        {"symbol": "A", "ranking_eligible": False, "win_rate_pct": None, "profit_factor": None},
        {"symbol": "B", "ranking_eligible": False, "win_rate_pct": None, "profit_factor": None},
    ]
    compute_combined_rank(rows)
    assert all(r["combined_rank"] is None for r in rows)


def test_tied_metrics_produce_equal_rank():
    rows = [
        {"symbol": "A", "ranking_eligible": True, "win_rate_pct": 70.0, "profit_factor": 3.0},
        {"symbol": "B", "ranking_eligible": True, "win_rate_pct": 70.0, "profit_factor": 3.0},
    ]
    compute_combined_rank(rows)
    assert rows[0]["combined_rank"] == rows[1]["combined_rank"]


def test_fundamental_cells_blank_when_missing():
    from scripts.build_final_watchlist import fundamental_cells, FUNDAMENTAL_HEADERS
    cells = fundamental_cells(None)
    assert len(cells) == len(FUNDAMENTAL_HEADERS) and set(cells) == {""}


def test_fundamental_cells_maps_summary():
    from scripts.build_final_watchlist import fundamental_cells, FUNDAMENTAL_HEADERS
    summary = {"verdict": "WATCH", "score": 65.4, "blocks": {"quality": 22.1, "growth": 18.6, "safety": 15.2,
               "valuation": 4.5, "ownership": 5.0}, "industry": "Paints", "hard_fails": [],
               "flags": ["1.3: Borrowings up", "3.3: weak"]}
    cells = fundamental_cells(summary)
    assert len(cells) == len(FUNDAMENTAL_HEADERS)
    assert cells[:7] == ["WATCH", 65.4, 22.1, 18.6, 15.2, 4.5, 5.0]
    assert cells[7] == "Paints" and cells[8] == "Borrowings up"


def test_key_note_prefers_hard_fail_and_truncates():
    from scripts.build_final_watchlist import key_note
    long = "0.2: " + "x" * 200
    assert key_note({"verdict": "REJECT", "hard_fails": [long], "flags": ["1.3: other"]}) == "x" * 87 + "..."
    assert key_note({"verdict": "PASS", "hard_fails": [], "flags": []}) == ""
    assert key_note({"verdict": "FINANCIAL", "hard_fails": [], "flags": []}).startswith("Bank")
