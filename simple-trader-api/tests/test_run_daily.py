"""Tests for run_daily.py's lock, backup and path helpers (all patched to a temp dir - never touches real run files)."""
import os
import time

import scripts.run_daily as rd


def patch_dirs(monkeypatch, tmp_path):
    scans = tmp_path / "daily_scans"
    scans.mkdir()
    monkeypatch.setattr(rd, "SCANS", str(scans))
    monkeypatch.setattr(rd, "LOCK", str(scans / ".run.lock"))
    monkeypatch.setattr(rd, "STATUS", str(scans / "run_status.json"))
    monkeypatch.setattr(rd, "STATE", str(scans / "symbol_state.json"))
    monkeypatch.setattr(rd, "BACKUPS", str(scans / "backups"))
    return scans


def test_paths_use_the_stamp():
    p = rd.paths("2026-10-01")
    assert p["watchlist"].endswith("2026-10-01_final_watchlist.xlsx")
    assert os.path.basename(os.path.dirname(p["gate7"])) == "2026-10-01" and p["gate7"].endswith("gate7.json")  # intermediates live in work/{stamp}/
    assert os.path.dirname(p["watchlist"]) == rd.SCANS and os.path.dirname(os.path.dirname(p["candidates"])) == rd.WORK


def test_lock_blocks_a_second_run_but_not_a_stale_lock(monkeypatch, tmp_path):
    patch_dirs(monkeypatch, tmp_path)
    assert rd.acquire_lock() is True
    assert rd.acquire_lock() is False            # another run in progress
    old = time.time() - (rd.LOCK_MAX_AGE_S + 60)
    os.utime(rd.LOCK, (old, old))
    assert rd.acquire_lock() is True             # abandoned lock is taken over
    rd.release_lock()
    assert not os.path.exists(rd.LOCK)
    rd.release_lock()                            # releasing twice is harmless


def test_backup_state_copies_and_keeps_newest_14(monkeypatch, tmp_path):
    scans = patch_dirs(monkeypatch, tmp_path)
    (scans / "symbol_state.json").write_text('{"A": 1}')
    os.makedirs(rd.BACKUPS)
    for i in range(20):
        (open(os.path.join(rd.BACKUPS, f"symbol_state_2026-09-{i + 1:02d}_000000.json"), "w")).write("{}")
    rd.backup_state("2026-10-01", lambda *_: None)
    names = sorted(os.listdir(rd.BACKUPS))
    assert len(names) == 14 and any("2026-10-01" in n for n in names)
    assert "symbol_state_2026-09-01_000000.json" not in names


def test_write_status_merges_fields(monkeypatch, tmp_path):
    patch_dirs(monkeypatch, tmp_path)
    rd.write_status(stamp="2026-10-01", status="running")
    rd.write_status(status="failed", error="boom")
    import json
    assert json.load(open(rd.STATUS)) == {"stamp": "2026-10-01", "status": "failed", "error": "boom"}


def test_check_verdicts_blocks_a_mostly_errored_read(tmp_path):
    import json
    import pytest
    err = {"verdict": "skip", "reason": "error", "error": "JS evaluation error: TypeError: Cannot read properties of undefined"}
    ok = {"verdict": "skip", "reason": "outside_band"}
    f = tmp_path / "d.json"
    f.write_text(json.dumps([err] * 30 + [ok] * 10))
    with pytest.raises(rd.StepFailed):
        rd.check_verdicts(str(f))
    f.write_text(json.dumps([err] * 3 + [ok] * 40))                      # a few glitches are normal
    rd.check_verdicts(str(f))
    f.write_text(json.dumps([err] * 30 + [{**ok, "cached_from": "2026-10-01"}] * 200))  # cached skips are not live reads
    with pytest.raises(rd.StepFailed):
        rd.check_verdicts(str(f))
