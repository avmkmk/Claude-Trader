"""Tests for paths.py: legacy-layout migration (moves, never deletes) and pruning of old intermediates."""
import os
import time

from scripts import paths


def make_legacy(tmp_path):
    scans = tmp_path / "daily_scans"
    (scans / "backups").mkdir(parents=True)
    (scans / "logs").mkdir()
    for name in ("2026-10-01_final_watchlist.xlsx", "2026-09-29_final_watchlist.xlsx", ".~lock.2026-10-01_final_watchlist.xlsx#",
                 "symbol_state.json", "manual_exclusions.json", "_rejection_cache.json", "run_status.json",
                 "2026-10-01_candidates.json", "2026-10-01_verdicts_details.json", "2026-09-29_gate7.json",
                 "2026-09-29_final_watchlist_with_fundamentals.xlsx", "2026-08-31_fundamental_ranking.xlsx", "notes.json"):
        (scans / name).write_text(name)
    (scans / "backups" / "symbol_state_x.json").write_text("b")
    (scans / "logs" / "run.log").write_text("l")
    return scans, tmp_path / "state", tmp_path / "work", tmp_path / "archive"


def test_migration_moves_everything_and_keeps_excels(tmp_path):
    scans, state, work, archive = make_legacy(tmp_path)
    moved = paths.migrate_legacy_layout(str(scans), str(state), str(work), str(archive))
    assert moved
    assert sorted(os.listdir(scans)) == [".~lock.2026-10-01_final_watchlist.xlsx#", "2026-09-29_final_watchlist.xlsx", "2026-10-01_final_watchlist.xlsx"]
    assert {"symbol_state.json", "manual_exclusions.json", "_rejection_cache.json", "run_status.json", "backups", "logs"} <= set(os.listdir(state))
    assert os.listdir(state / "backups") == ["symbol_state_x.json"] and os.listdir(state / "logs") == ["run.log"]
    assert sorted(os.listdir(work / "2026-10-01")) == ["candidates.json", "verdicts_details.json"]
    assert os.listdir(work / "2026-09-29") == ["gate7.json"] and os.listdir(work / "undated") == ["notes.json"]
    assert sorted(os.listdir(archive)) == ["2026-08-31_fundamental_ranking.xlsx", "2026-09-29_final_watchlist_with_fundamentals.xlsx"]
    assert (state / "symbol_state.json").read_text() == "symbol_state.json"   # content preserved


def test_migration_is_idempotent_and_never_overwrites(tmp_path):
    scans, state, work, archive = make_legacy(tmp_path)
    paths.migrate_legacy_layout(str(scans), str(state), str(work), str(archive))
    assert paths.migrate_legacy_layout(str(scans), str(state), str(work), str(archive)) == []
    (scans / "symbol_state.json").write_text("OLD COPY")               # a stray older copy appears again
    (state / "symbol_state.json").write_text("CURRENT")
    paths.migrate_legacy_layout(str(scans), str(state), str(work), str(archive))
    assert (state / "symbol_state.json").read_text() == "CURRENT" and (scans / "symbol_state.json").exists()  # nothing lost


def test_migration_with_missing_folder_is_a_noop(tmp_path):
    assert paths.migrate_legacy_layout(str(tmp_path / "nope"), str(tmp_path / "s"), str(tmp_path / "w"), str(tmp_path / "a")) == []


def test_prune_removes_only_old_dated_folders_and_logs(tmp_path):
    work, cache, logs = tmp_path / "work", tmp_path / "fund", tmp_path / "logs"
    for root in (work, cache):
        for d in ("2026-09-20", "2026-09-27", "2026-09-28", "2026-10-01", "undated", "keepme"):
            (root / d).mkdir(parents=True)
            (root / d / "f.json").write_text("x")
    logs.mkdir()
    (logs / "old.log").write_text("x")
    (logs / "new.log").write_text("x")
    old = time.time() - 40 * 86400
    os.utime(logs / "old.log", (old, old))
    removed = paths.prune_old("2026-10-01", str(work), str(cache), str(logs))
    # window = 3 days before the stamp: 09-28 is kept, 09-27 and older go; non-dated folders are never touched
    assert sorted(os.listdir(work)) == ["2026-09-28", "2026-10-01", "keepme", "undated"]
    assert sorted(os.listdir(cache)) == ["2026-09-28", "2026-10-01", "keepme", "undated"]
    assert os.listdir(logs) == ["new.log"] and any("old.log" in r for r in removed)
