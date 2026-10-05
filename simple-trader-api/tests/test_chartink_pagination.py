"""The Chartink scraper must survive stale elements while paging instead of silently truncating results."""
import pytest
from selenium.common.exceptions import StaleElementReferenceException

import app.services.chartink_scraper as cs


class Btn:
    def __init__(self, text, disabled=None, shown=True, stale=False):
        self.text, self._disabled, self._shown, self._stale = text, disabled, shown, stale

    def get_attribute(self, name):
        if self._stale:
            raise StaleElementReferenceException("stale element reference")
        return self._disabled if name == "disabled" else None

    def is_displayed(self):
        return self._shown


class Driver:
    """find_elements returns a different list per call, mimicking the table re-rendering after a page change."""
    def __init__(self, *calls):
        self.calls = list(calls)

    def find_elements(self, *_):
        result = self.calls.pop(0) if len(self.calls) > 1 else self.calls[0]
        if isinstance(result, Exception):
            raise result
        return result


def scraper_with(driver):
    s = object.__new__(cs.ChartinkScraper)
    s.driver = driver
    return s


def test_next_button_search_retries_through_stale_elements(monkeypatch):
    monkeypatch.setattr(cs.time, "sleep", lambda *_: None)
    good = [Btn("Previous"), Btn("Next")]
    drv = Driver(StaleElementReferenceException("stale"), [Btn("Next", stale=True)], good)
    found = scraper_with(drv)._enabled_next_buttons()
    assert [b.text for b in found] == ["Next"]


def test_disabled_and_hidden_next_buttons_mean_last_page(monkeypatch):
    monkeypatch.setattr(cs.time, "sleep", lambda *_: None)
    drv = Driver([Btn("Next", disabled="true"), Btn("Next", shown=False), Btn("Previous")])
    assert scraper_with(drv)._enabled_next_buttons() == []


def test_persistent_staleness_is_raised_not_swallowed(monkeypatch):
    monkeypatch.setattr(cs.time, "sleep", lambda *_: None)
    drv = Driver(StaleElementReferenceException("stale"))
    with pytest.raises(StaleElementReferenceException):
        scraper_with(drv)._enabled_next_buttons(attempts=3)


def test_scan_candidates_refuses_a_partial_screener(monkeypatch):
    import scripts.scan_candidates as sc

    class FakeScraper:
        last_scrape_incomplete = False

        def scrape_single_screener(self, name):
            self.last_scrape_incomplete = (name == "stage-2-trend")   # paging ended early on the second screener
            return {"stocks": [{"symbol": "AAA"}], "errors": []}

    monkeypatch.setattr(sc, "ChartinkScraper", FakeScraper)
    with pytest.raises(RuntimeError, match="stage-2-trend.*partial"):
        sc.scrape_all_symbols()
