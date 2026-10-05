"""
Where every pipeline file lives (all under simple-trader-api/data/). Single source of truth.

    daily_scans/   ONLY the consolidated Excel per session: {date}_final_watchlist.xlsx (stocks + fundamentals + news/policy)
    state/         persistent state and run bookkeeping: symbol_state.json, manual_exclusions.json, _rejection_cache.json,
                   run_status.json, .run.lock, backups/ (state snapshots), logs/ (run logs)
    work/{stamp}/  per-run intermediates (candidates, check list, verdicts, Gate 7 inputs/outputs); pruned after a few days
    fundamentals/  parsed screener.in pages, cached per session date; pruned after a few days
    archive/       files moved out of daily_scans/ that are not the consolidated Excel (nothing is deleted automatically)

migrate_legacy_layout() upgrades the old flat layout (everything inside daily_scans/) by MOVING files; it is idempotent and
runs when this module is imported, so no script can ever read an empty state file because the layout changed.
"""
import os
import re
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
SCANS_DIR = os.path.join(DATA, "daily_scans")
STATE_DIR = os.path.join(DATA, "state")
WORK_DIR = os.path.join(DATA, "work")
FUND_CACHE_DIR = os.path.join(DATA, "fundamentals")
ARCHIVE_DIR = os.path.join(DATA, "archive")

STATE_PATH = os.path.join(STATE_DIR, "symbol_state.json")
EXCLUSIONS_PATH = os.path.join(STATE_DIR, "manual_exclusions.json")
REJECTION_CACHE_PATH = os.path.join(STATE_DIR, "_rejection_cache.json")
STATUS_PATH = os.path.join(STATE_DIR, "run_status.json")
LOCK_PATH = os.path.join(STATE_DIR, ".run.lock")
BACKUPS_DIR = os.path.join(STATE_DIR, "backups")
LOGS_DIR = os.path.join(STATE_DIR, "logs")

KEEP_WORK_DAYS = 3
KEEP_FUND_CACHE_DAYS = 3
KEEP_LOG_DAYS = 30

WATCHLIST_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_final_watchlist\.xlsx$")
DATED_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_(.+)$")
STATE_FILES = ("symbol_state.json", "manual_exclusions.json", "_rejection_cache.json", "run_status.json", ".run.lock")


def work_dir(stamp, create=True):
    d = os.path.join(WORK_DIR, stamp)
    if create:
        os.makedirs(d, exist_ok=True)
    return d


def _move(src, dst):
    """Move src -> dst without ever overwriting: if dst exists the source is left where it is."""
    if os.path.exists(dst):
        return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    return True


def migrate_legacy_layout(scans=SCANS_DIR, state=STATE_DIR, work=WORK_DIR, archive=ARCHIVE_DIR):
    """Move legacy files out of daily_scans/. Returns a list of 'src -> dst' strings (empty when nothing to do)."""
    moved = []
    if not os.path.isdir(scans):
        return moved
    for name in sorted(os.listdir(scans)):
        src = os.path.join(scans, name)
        if name.startswith(".~lock") or WATCHLIST_RE.match(name):
            continue  # an open-file lock from the spreadsheet app, or the consolidated Excel itself
        if os.path.isdir(src):
            if name in ("backups", "logs"):
                for sub in sorted(os.listdir(src)):
                    if _move(os.path.join(src, sub), os.path.join(state, name, sub)):
                        moved.append(f"{name}/{sub} -> state/{name}/")
                if not os.listdir(src):
                    os.rmdir(src)
            continue
        if name in STATE_FILES:
            dst = os.path.join(state, name)
        elif name.lower().endswith(".xlsx"):
            dst = os.path.join(archive, name)  # a spreadsheet that is not the consolidated watchlist
        else:
            m = DATED_RE.match(name)
            dst = os.path.join(work, m.group(1), m.group(2)) if m else os.path.join(work, "undated", name)
        if _move(src, dst):
            moved.append(f"{name} -> {os.path.relpath(dst, os.path.dirname(scans))}")
    return moved


def prune_old(stamp, work=WORK_DIR, cache=FUND_CACHE_DIR, logs=LOGS_DIR, keep_work=KEEP_WORK_DAYS,
              keep_cache=KEEP_FUND_CACHE_DAYS, keep_logs=KEEP_LOG_DAYS):
    """Delete per-run intermediates older than the keep windows (relative to the session `stamp`). Returns what was removed."""
    from datetime import date, timedelta
    ref = date.fromisoformat(stamp)
    removed = []
    for root, keep in ((work, keep_work), (cache, keep_cache)):
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            path = os.path.join(root, name)
            try:
                d = date.fromisoformat(name)
            except ValueError:
                continue  # not a dated folder - leave it alone
            if os.path.isdir(path) and d < ref - timedelta(days=keep):
                shutil.rmtree(path)
                removed.append(os.path.relpath(path, os.path.dirname(root)))
    if os.path.isdir(logs):
        import time
        cutoff = time.time() - keep_logs * 86400
        for name in os.listdir(logs):
            path = os.path.join(logs, name)
            if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                os.remove(path)
                removed.append(f"logs/{name}")
    return removed


migrate_legacy_layout()
