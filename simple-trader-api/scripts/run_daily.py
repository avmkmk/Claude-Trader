"""
Daily ATH scan runner - the pure-script routine (no Claude needed).

    python scripts/run_daily.py                 # run only if the newest watchlist is older than the last completed session
    python scripts/run_daily.py --force         # run regardless
    python scripts/run_daily.py --check-only    # print staleness, exit 10 if a run is needed, 0 if current
    python scripts/run_daily.py --dry-run       # show what would run
    python scripts/run_daily.py --from-step 4   # resume after a failure (steps listed in STEPS)
    flags: --open (open the Excel when done), --no-fundamentals, --stamp YYYY-MM-DD

The watchlist is stamped with the last COMPLETED NSE session (see trading_calendar.py), so running after the close
or the next morning before the open is the same thing. Designed to be started by Windows Task Scheduler at a fixed
morning time AND at logon: whichever fires first does the work, the other finds a current watchlist and exits.

Exit codes: 0 ok / already current, 1 a step failed, 2 another run is in progress, 10 (--check-only) run needed.
Gate 7 (news + government stance, needs web search) is deliberately NOT here - it is done by the /daily-ath-scan
Claude command on top of the watchlist this script produces.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.trading_calendar import is_stale, load_holidays, market_is_open, now_ist  # noqa: E402

API = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(API)
TV = os.path.join(ROOT, "tradingview-mcp-jackson")
# Layout (see scripts/paths.py): SCANS holds ONLY the consolidated Excel files; state/bookkeeping live in data/state/,
# per-run intermediates in data/work/{stamp}/.
from scripts.paths import (BACKUPS_DIR as BACKUPS, LOCK_PATH as LOCK, LOGS_DIR as LOGS, REJECTION_CACHE_PATH,  # noqa: E402
                           SCANS_DIR as SCANS, STATE_PATH as STATE, STATUS_PATH as STATUS, WORK_DIR as WORK, prune_old)
LOCK_MAX_AGE_S = 4 * 3600
CDP_URL = "http://localhost:9222/json/version"

STEPS = [
    (1, "Preflight (prerequisites)"),
    (2, "Scrape Chartink (union of both screeners) + enrich"),
    (3, "Build today's check list"),
    (4, "Ensure TradingView is running with CDP"),
    (5, "Read live Pine strategy state per symbol"),
    (6, "Merge verdicts into symbol_state.json (backed up first)"),
    (7, "Build watchlist Excel with fundamentals"),
]


class StepFailed(Exception):
    pass


def paths(stamp):
    d = lambda name: os.path.join(WORK, stamp, name)  # noqa: E731
    return {"candidates": d("candidates.json"), "to_check": d("to_check.json"), "verdicts": d("verdicts.json"),
            "details": d("verdicts_details.json"), "gate7": d("gate7.json"),
            "watchlist": os.path.join(SCANS, f"{stamp}_final_watchlist.xlsx")}


def write_status(**fields):
    os.makedirs(os.path.dirname(STATUS), exist_ok=True)
    try:
        cur = json.load(open(STATUS, encoding="utf-8"))
    except (OSError, ValueError):
        cur = {}
    cur.update(fields)
    with open(STATUS, "w", encoding="utf-8") as f:
        json.dump(cur, f, indent=2)


def acquire_lock():
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    if os.path.exists(LOCK) and time.time() - os.path.getmtime(LOCK) < LOCK_MAX_AGE_S:
        return False
    with open(LOCK, "w") as f:
        f.write(json.dumps({"pid": os.getpid(), "started": datetime.now().isoformat(timespec="seconds")}))
    return True


def release_lock():
    try:
        os.remove(LOCK)
    except OSError:
        pass


class Logger:
    def __init__(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.f = open(path, "a", encoding="utf-8")

    def __call__(self, msg=""):
        line = f"[{datetime.now():%H:%M:%S}] {msg}"
        print(line, flush=True)
        self.f.write(line + "\n")
        self.f.flush()


def run(cmd, cwd, log, timeout):
    """Run a subprocess, streaming its output to the log. Raises StepFailed on a non-zero exit."""
    log(f"$ {' '.join(cmd)}   (cwd={os.path.relpath(cwd, ROOT)})")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                            errors="replace", env=env)
    start = time.time()
    for line in proc.stdout:
        log("    " + line.rstrip())
        if time.time() - start > timeout:
            proc.kill()
            raise StepFailed(f"timed out after {timeout // 60} min")
    if proc.wait() != 0:
        raise StepFailed(f"exit code {proc.returncode}")


def cdp_up():
    try:
        urllib.request.urlopen(CDP_URL, timeout=3).read()
        return True
    except Exception:
        return False


def backup_state(stamp, log):
    if not os.path.exists(STATE):
        return
    os.makedirs(BACKUPS, exist_ok=True)
    dest = os.path.join(BACKUPS, f"symbol_state_{stamp}_{datetime.now():%H%M%S}.json")
    shutil.copy2(STATE, dest)
    try:
        shown = os.path.relpath(dest, ROOT)
    except ValueError:  # different drive
        shown = dest
    log(f"Backed up symbol_state.json -> {shown}")
    for old in sorted(glob.glob(os.path.join(BACKUPS, "symbol_state_*.json")))[:-14]:  # keep the newest 14
        os.remove(old)


MAX_ERROR_RATIO = 0.25


def check_verdicts(details_path):
    """Refuse to merge a live read that is mostly errors (e.g. TradingView chart was not ready)."""
    with open(details_path, encoding="utf-8") as f:
        details = json.load(f)
    live = [d for d in details if not d.get("cached_from")]
    errors = [d for d in live if d.get("reason") == "error"]
    if len(errors) >= 5 and len(errors) / max(1, len(live)) > MAX_ERROR_RATIO:
        sample = (errors[0].get("error") or "").splitlines()[0][:120]
        raise StepFailed(f"{len(errors)} of {len(live)} live reads errored (first: {sample}) - not merging into symbol_state.json")


def execute(stamp, args, log):
    p = paths(stamp)
    os.makedirs(os.path.dirname(p["candidates"]), exist_ok=True)
    os.makedirs(SCANS, exist_ok=True)
    rel = lambda path: os.path.relpath(path, API)  # noqa: E731
    py = sys.executable
    for n, title in STEPS:
        if n < args.from_step:
            continue
        log(f"=== Step {n}/{len(STEPS)}: {title}")
        write_status(step=n, step_title=title)
        if n == 1:
            out = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                                  os.path.join(ROOT, "scripts", "preflight.ps1")], capture_output=True, text=True)
            for line in out.stdout.splitlines():
                log("    " + line)
            missing = [ln for ln in out.stdout.splitlines() if ln.startswith("[MISSING]")]
            if missing:
                raise StepFailed("missing prerequisites - see log (docs/SETUP.md)")
        elif n == 2:
            run([py, "scripts/scan_candidates.py", stamp], API, log, 1800)
        elif n == 3:
            run([py, "scripts/build_check_list.py", rel(p["candidates"]), rel(p["to_check"])], API, log, 600)
        elif n == 4:
            if cdp_up():
                log("TradingView already running with CDP on :9222 - not relaunching")
            else:
                run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                     os.path.join(TV, "scripts", "launch_tv_debug.ps1")], ROOT, log, 300)
        elif n == 5:
            run(["node", "scan_step_c.mjs", p["to_check"], p["verdicts"], REJECTION_CACHE_PATH], TV, log, 4 * 3600)
        elif n == 6:
            check_verdicts(p["details"])
            backup_state(stamp, log)
            run([py, "scripts/update_symbol_state.py", rel(p["details"]), rel(p["candidates"]), stamp], API, log, 600)
        elif n == 7:
            cmd = [py, "scripts/build_final_watchlist.py", stamp, rel(p["watchlist"])]
            if args.no_fundamentals:
                cmd.append("--no-fundamentals")
            run(cmd, API, log, 3600)
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--from-step", type=int, default=1)
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--no-fundamentals", action="store_true")
    ap.add_argument("--stamp", help="override the session date (YYYY-MM-DD)")
    args = ap.parse_args()

    holidays = load_holidays()
    now = now_ist()
    stale, latest, expected = is_stale(SCANS, now, holidays)
    stamp = args.stamp or expected.isoformat()
    state_txt = (f"newest watchlist: {latest or 'none'}; expected session: {expected} "
                 f"(now {now:%Y-%m-%d %H:%M} IST{', market open' if market_is_open(now, holidays) else ''})")

    if args.check_only:
        g7 = ""
        if latest is not None:
            g7 = "; Gate 7 (news/policy) " + ("done" if os.path.exists(paths(latest.isoformat())["gate7"]) else "pending")
        print(("RUN NEEDED - " if stale else "CURRENT - ") + state_txt + g7)
        sys.exit(10 if stale else 0)
    if not stale and not args.force and not args.dry_run:
        print("Watchlist already current - nothing to do. " + state_txt)
        write_status(last_check=now.isoformat(timespec="seconds"), note="current")
        sys.exit(0)
    if args.dry_run:
        print(state_txt)
        print(f"Would run {'(stale)' if stale else '(forced)'} with session stamp {stamp}:")
        for n, title in STEPS:
            if n >= args.from_step:
                print(f"  {n}. {title}")
        print("Output:", paths(stamp)["watchlist"])
        sys.exit(0)

    if not acquire_lock():
        print("Another run is in progress (lock file is less than 4h old) - exiting.")
        sys.exit(2)
    log = Logger(os.path.join(LOGS, f"{stamp}_{datetime.now():%H%M%S}.log"))
    log(state_txt)
    if market_is_open(now, holidays):
        log("NOTE: market is open - today's daily bar is still forming, so signals are provisional.")
    started = datetime.now().isoformat(timespec="seconds")
    write_status(stamp=stamp, status="running", started=started, finished=None, error=None, log=log.f.name)
    try:
        p = execute(stamp, args, log)
    except StepFailed as e:
        log(f"FAILED: {e}")
        write_status(status="failed", finished=datetime.now().isoformat(timespec="seconds"), error=str(e))
        release_lock()
        sys.exit(1)
    except Exception as e:  # unexpected - still leave a clear status behind
        log(f"FAILED (unexpected {type(e).__name__}): {e}")
        write_status(status="failed", finished=datetime.now().isoformat(timespec="seconds"), error=f"{type(e).__name__}: {e}")
        release_lock()
        sys.exit(1)
    release_lock()
    write_status(status="success", finished=datetime.now().isoformat(timespec="seconds"), watchlist=p["watchlist"],
                 gate7_done=os.path.exists(p["gate7"]))
    removed = prune_old(stamp)
    if removed:
        log(f"Pruned old intermediates: {', '.join(removed)}")
    log(f"DONE. Watchlist: {p['watchlist']}")
    if not os.path.exists(p["gate7"]):
        log("Gate 7 (news + government stance) not done yet - run /daily-ath-scan in Claude Code to add it.")
    if args.open and os.name == "nt":
        os.startfile(p["watchlist"])  # noqa: S606


if __name__ == "__main__":
    main()
