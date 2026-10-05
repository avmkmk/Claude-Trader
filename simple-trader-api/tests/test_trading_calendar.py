"""Tests for trading_calendar.py: which session date a watchlist should carry."""
from datetime import date, datetime

from scripts.trading_calendar import (IST, expected_session_date, is_stale, is_trading_day, latest_watchlist_date,
                                      load_holidays, market_is_open, previous_trading_day)

H = {date(2026, 10, 2), date(2026, 10, 20)}


def at(y, m, d, hh, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=IST)


def test_morning_before_open_uses_previous_session():
    # Mon 5 Oct 08:00; Fri 2 Oct is a holiday -> Thu 1 Oct
    assert expected_session_date(at(2026, 10, 5, 8), H) == date(2026, 10, 1)
    assert expected_session_date(at(2026, 10, 6, 8), H) == date(2026, 10, 5)


def test_after_close_and_next_morning_give_the_same_stamp():
    assert expected_session_date(at(2026, 10, 5, 17), H) == date(2026, 10, 5)
    assert expected_session_date(at(2026, 10, 6, 7, 30), H) == date(2026, 10, 5)


def test_market_hours_do_not_use_todays_unfinished_bar():
    assert expected_session_date(at(2026, 10, 5, 11), H) == date(2026, 10, 1)
    assert expected_session_date(at(2026, 10, 5, 15, 45), H) == date(2026, 10, 1)
    assert market_is_open(at(2026, 10, 5, 11), H) and not market_is_open(at(2026, 10, 5, 8), H)


def test_weekends_and_holidays():
    assert expected_session_date(at(2026, 10, 3, 10), H) == date(2026, 10, 1)   # Saturday
    assert expected_session_date(at(2026, 10, 4, 22), H) == date(2026, 10, 1)   # Sunday night
    assert expected_session_date(at(2026, 10, 20, 9), H) == date(2026, 10, 19)  # Dussehra morning
    assert expected_session_date(at(2026, 10, 20, 20), H) == date(2026, 10, 19)  # holiday after the close
    assert not is_trading_day(date(2026, 10, 2), H) and previous_trading_day(date(2026, 10, 5), H) == date(2026, 10, 1)


def test_staleness_against_existing_watchlists(tmp_path):
    now = at(2026, 10, 5, 8)
    assert is_stale(str(tmp_path), now, H) == (True, None, date(2026, 10, 1))
    (tmp_path / "2026-09-29_final_watchlist.xlsx").write_text("x")
    (tmp_path / "2026-09-29_final_watchlist_with_fundamentals.xlsx").write_text("x")  # not a daily file
    assert latest_watchlist_date(str(tmp_path)) == date(2026, 9, 29)
    assert is_stale(str(tmp_path), now, H)[0] is True
    (tmp_path / "2026-10-01_final_watchlist.xlsx").write_text("x")
    assert is_stale(str(tmp_path), now, H)[0] is False
    # a late start the same morning is still current; after the close of 5 Oct it is stale again
    assert is_stale(str(tmp_path), at(2026, 10, 5, 11), H)[0] is False
    assert is_stale(str(tmp_path), at(2026, 10, 5, 18), H)[0] is True


def test_shipped_holiday_file_loads():
    holidays = load_holidays()
    assert date(2026, 10, 2) in holidays and len(holidays) == 16
