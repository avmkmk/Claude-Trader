"""
Build and send the Telegram digest for a watchlist stamp.

    python scripts/build_telegram_digest.py 2026-10-06 --dry-run          # print only
    python scripts/build_telegram_digest.py 2026-10-06 --stage scan       # after the script run (Gate 7 pending)
    python scripts/build_telegram_digest.py 2026-10-06 --stage gate7      # after Gate 7 (news/policy tags included)
    flags: --force (send even if this stage was already sent)

Reads files the pipeline already wrote (data/work/{stamp}/gate7_targets.json, verdicts_details.json, gate7.json);
verdicts are never re-derived. Goes to TELEGRAM_CHAT_ID and, if set, TELEGRAM_CHANNEL_ID. Each (stamp, stage, target) is sent once - recorded in data/state/telegram_sent.json.
Sending never raises: a Telegram problem prints a warning and exits 0 so the scan is not affected.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.telegram_notifier import load_env, send_message  # noqa: E402
from scripts.paths import STATE_DIR, WORK_DIR  # noqa: E402
from scripts.trading_calendar import load_holidays, market_is_open, now_ist  # noqa: E402

SENT_PATH = os.path.join(STATE_DIR, "telegram_sent.json")
DISCLAIMER = "Informational scan output only, not investment advice. Do your own research."
VERDICT_RANK = {"PASS": 0, "WATCH": 1}


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _rank(targets):
    return sorted(targets, key=lambda t: (VERDICT_RANK.get(t.get("verdict"), 9), -(t.get("score") or 0)))


def _num(v):
    return "n/a" if v is None else f"{v:g}"


def _sentiment(g):
    """'Bullish by news and policy' when both agree, else each spelled out; 'pending' before Gate 7."""
    if not g:
        return "pending (news/policy check not done)"
    n, p = g.get("news_sentiment"), g.get("policy_sentiment")
    if n and n == p:
        return f"{n} by news and policy"
    return f"News {n or 'n/a'}, Policy {p or 'n/a'}"


def _block(t, details, gate7):
    d = details.get(t["symbol"], {})
    lines = [f"{t['symbol']} - {t.get('industry', '')}",
             f"Entry price: {_num(d.get('entry_price'))}",
             f"Stop Loss: {_num(d.get('ema200'))}"]
    if d.get("close") is not None:
        lines.append(f"Last close: {_num(d.get('close'))}"
                     + (f" ({d['distance_from_entry_pct']:+.1f}% from entry)" if d.get("distance_from_entry_pct") is not None else ""))
    lines.append(f"Sentiment: {_sentiment(gate7.get(t['symbol']))}")
    return "\n".join(lines)


def build_digest(stamp, stage="scan", work_dir=WORK_DIR, provisional=False):
    """Every PASS gets a full block (best score first); WATCH names follow in the same format under their own heading."""
    folder = os.path.join(work_dir, stamp)
    targets = _load(os.path.join(folder, "gate7_targets.json"), [])
    details = {d["symbol"]: d for d in _load(os.path.join(folder, "verdicts_details.json"), []) if "symbol" in d}
    gate7 = _load(os.path.join(folder, "gate7.json"), {}) if stage == "gate7" else {}
    ranked = _rank(targets)
    passed = [t for t in ranked if t.get("verdict") == "PASS"]
    watch = [t for t in ranked if t.get("verdict") == "WATCH"]

    lines = [f"ATH Reclaim scan - session {stamp}" + (" (provisional: market open)" if provisional else ""),
             f"{len(passed)} PASS, {len(watch)} WATCH after fundamentals."]
    if not ranked:
        lines.append("No PASS/WATCH names today.")
    if passed:
        lines += ["", f"=== PASS ({len(passed)}) ==="]
        for t in passed:
            lines += ["", _block(t, details, gate7)]
    if watch:
        lines += ["", f"=== WATCH ({len(watch)}) ==="]
        for t in watch:
            lines += ["", _block(t, details, gate7)]
    if stage == "gate7":
        bad = [t["symbol"] for t in passed if "Bearish" in (gate7.get(t["symbol"], {}).get("news_sentiment"),
                                                            gate7.get(t["symbol"], {}).get("policy_sentiment"))]
        if bad:
            lines += ["", "Check: PASS with Bearish news/policy - " + ", ".join(bad)]
    else:
        lines += ["", "News / policy check (Gate 7): pending."]
    lines += ["", DISCLAIMER]
    return "\n".join(lines)


def targets():
    """(label, chat_id) pairs that get the digest: your own chat and, if configured, the channel."""
    load_env()
    out = []
    for label, var in (("chat", "TELEGRAM_CHAT_ID"), ("channel", "TELEGRAM_CHANNEL_ID")):
        if os.environ.get(var):
            out.append((label, os.environ[var]))
    return out


def send_once(stamp, stage, text, force=False, sent_path=SENT_PATH, label="chat", chat_id=None):
    """Send unless (stamp, stage) was already sent to this target. Returns (sent, detail).
    The personal chat keeps the plain stage name as its marker; other targets use 'stage@label'."""
    key = stage if label == "chat" else f"{stage}@{label}"
    sent = _load(sent_path, {})
    if not force and key in sent.get(stamp, []):
        return False, f"{stage} digest for {stamp} already sent to {label} (use --force to resend)"
    ok, detail = send_message(text, chat_id=chat_id)
    if ok:
        sent.setdefault(stamp, [])
        if key not in sent[stamp]:
            sent[stamp].append(key)
        os.makedirs(os.path.dirname(sent_path), exist_ok=True)
        with open(sent_path, "w", encoding="utf-8") as f:
            json.dump(sent, f, indent=2)
    return ok, detail


def send_all(stamp, stage, text, force=False, sent_path=SENT_PATH):
    """Send to every configured target, each tracked separately. Returns {label: (ok, detail)}."""
    tg = targets()
    if not tg:
        return {"none": (False, "TELEGRAM_CHAT_ID / TELEGRAM_CHANNEL_ID not set")}
    return {label: send_once(stamp, stage, text, force, sent_path, label, cid) for label, cid in tg}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stamp")
    ap.add_argument("--stage", choices=["scan", "gate7"], default="scan")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    provisional = market_is_open(now_ist(), load_holidays())
    text = build_digest(args.stamp, args.stage, provisional=provisional)
    if args.dry_run:
        print(text)
        return 0
    results = send_all(args.stamp, args.stage, text, force=args.force)
    print("Telegram: " + "; ".join(f"{k} sent" if ok else f"{k} not sent - {d}" for k, (ok, d) in results.items()))
    return 0  # never fail the pipeline over a notification


if __name__ == "__main__":
    sys.exit(main())
