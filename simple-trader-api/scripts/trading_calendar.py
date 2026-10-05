"""
NSE trading calendar helpers for the daily ATH routine.

A watchlist is stamped with the last COMPLETED trading session, so a run after the close and a run the
next morning before the open produce the same stamp (the data is identical). Everything is computed in
IST (UTC+5:30, no DST) regardless of the machine's timezone.
"""
import glob
import json
import os
import re
from datetime import date, datetime, time, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
MARKET_OPEN = time(9, 15)
# Close is 15:30; allow time for end-of-day data (Chartink / TradingView daily bar) to settle.
SESSION_COMPLETE = time(16, 0)

HOLIDAYS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "nse_holidays.json")
WATCHLIST_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_final_watchlist\.xlsx$")


def now_ist():
    return datetime.now(timezone.utc).astimezone(IST)


def load_holidays(path=HOLIDAYS_PATH):
    try:
        with open(path, encoding="utf-8") as f:
            return {date.fromisoformat(d) for d in json.load(f).get("holidays", [])}
    except FileNotFoundError:
        return set()


def is_trading_day(d, holidays):
    return d.weekday() < 5 and d not in holidays


def previous_trading_day(d, holidays):
    """Latest trading day strictly before d."""
    d -= timedelta(days=1)
    while not is_trading_day(d, holidays):
        d -= timedelta(days=1)
    return d


def expected_session_date(now, holidays):
    """The session date a fresh watchlist should carry at time `now` (an aware or IST-naive datetime).

    After 16:00 IST on a trading day: that day. Otherwise (before 16:00, weekend or holiday): the latest
    earlier trading day. Between 09:15 and 16:00 the day's bar is still forming, so it is not used.
    """
    d = now.date()
    if is_trading_day(d, holidays) and now.time() >= SESSION_COMPLETE:
        return d
    return previous_trading_day(d, holidays)


def market_is_open(now, holidays):
    return is_trading_day(now.date(), holidays) and MARKET_OPEN <= now.time() < SESSION_COMPLETE


def latest_watchlist_date(scans_dir):
    """Newest YYYY-MM-DD among *_final_watchlist.xlsx files, or None."""
    dates = []
    for path in glob.glob(os.path.join(scans_dir, "*_final_watchlist.xlsx")):
        m = WATCHLIST_RE.match(os.path.basename(path))
        if m:
            dates.append(date.fromisoformat(m.group(1)))
    return max(dates) if dates else None


def is_stale(scans_dir, now=None, holidays=None):
    """(stale?, latest_date, expected_date). Stale when the newest watchlist predates the expected session."""
    holidays = load_holidays() if holidays is None else holidays
    now = now or now_ist()
    expected = expected_session_date(now, holidays)
    latest = latest_watchlist_date(scans_dir)
    return (latest is None or latest < expected), latest, expected
