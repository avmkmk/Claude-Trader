"""Tests for build_telegram_digest.py"""
import json

from scripts import build_telegram_digest as bd


def _write(tmp_path, stamp="2026-01-01", gate7=None):
    folder = tmp_path / stamp
    folder.mkdir()
    targets = [
        {"symbol": "WATCHCO", "verdict": "WATCH", "score": 99, "industry": "X"},
        {"symbol": "LOWPASS", "verdict": "PASS", "score": 70, "industry": "Y"},
        {"symbol": "TOPPASS", "verdict": "PASS", "score": 90, "industry": "Z"},
    ]
    (folder / "gate7_targets.json").write_text(json.dumps(targets), encoding="utf-8")
    (folder / "verdicts_details.json").write_text(json.dumps(
        [{"symbol": "TOPPASS", "ema200": 80.0, "close": 100.0, "entry_price": 98.0, "distance_from_entry_pct": 2.04}]), encoding="utf-8")
    if gate7:
        (folder / "gate7.json").write_text(json.dumps(gate7), encoding="utf-8")


def test_every_pass_gets_a_full_block_best_score_first_then_watch(tmp_path):
    _write(tmp_path)
    text = bd.build_digest("2026-01-01", "scan", work_dir=str(tmp_path))
    assert text.index("TOPPASS") < text.index("LOWPASS") < text.index("WATCHCO")
    assert "=== PASS (2) ===" in text and "=== WATCH (1) ===" in text
    assert "TOPPASS - Z\nEntry price: 98\nStop Loss: 80\nLast close: 100 (+2.0% from entry)" in text
    assert "LOWPASS - Y\nEntry price: n/a" in text  # no details: shown as n/a, still listed
    assert "Sentiment: pending" in text and bd.DISCLAIMER in text


def test_no_cap_all_passes_are_listed(tmp_path):
    folder = tmp_path / "2026-01-01"
    folder.mkdir()
    targets = [{"symbol": f"S{i}", "verdict": "PASS", "score": i, "industry": "I"} for i in range(25)]
    (folder / "gate7_targets.json").write_text(json.dumps(targets), encoding="utf-8")
    text = bd.build_digest("2026-01-01", work_dir=str(tmp_path))
    assert all(f"S{i} - I" in text for i in range(25))


def test_gate7_sentiment_wording_and_conflicts(tmp_path):
    _write(tmp_path, gate7={"TOPPASS": {"news_sentiment": "Bullish", "policy_sentiment": "Bullish"},
                            "LOWPASS": {"news_sentiment": "Bearish", "policy_sentiment": "Neutral"}})
    text = bd.build_digest("2026-01-01", "gate7", work_dir=str(tmp_path))
    assert "Sentiment: Bullish by news and policy" in text
    assert "Sentiment: News Bearish, Policy Neutral" in text
    assert "Check: PASS with Bearish news/policy - LOWPASS" in text
    assert "pending" not in text.split("Sentiment: News Bearish")[0].split("WATCHCO")[0]


def test_missing_data_gives_empty_message_not_crash(tmp_path):
    (tmp_path / "2026-01-01").mkdir()
    assert "No PASS/WATCH names today." in bd.build_digest("2026-01-01", work_dir=str(tmp_path))


def test_send_once_sends_a_stage_only_once(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(bd, "send_message", lambda text, chat_id=None: (calls.append(text) or True, "sent"))
    sp = str(tmp_path / "sent.json")
    assert bd.send_once("s", "scan", "hi", sent_path=sp)[0] is True
    assert bd.send_once("s", "scan", "hi", sent_path=sp)[0] is False
    assert bd.send_once("s", "gate7", "hi", sent_path=sp)[0] is True
    assert bd.send_once("s", "scan", "hi", force=True, sent_path=sp)[0] is True
    assert len(calls) == 3


def test_failed_send_is_not_recorded(tmp_path, monkeypatch):
    monkeypatch.setattr(bd, "send_message", lambda text, chat_id=None: (False, "HTTP 401"))
    sp = tmp_path / "sent.json"
    assert bd.send_once("s", "scan", "hi", sent_path=str(sp))[0] is False
    assert not sp.exists()


def test_each_target_is_tracked_separately(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(bd, "send_message", lambda text, chat_id=None: (calls.append(chat_id) or True, "sent"))
    monkeypatch.setattr(bd, "targets", lambda: [("chat", "111"), ("channel", "-100222")])
    sp = str(tmp_path / "sent.json")
    r = bd.send_all("s", "gate7", "hi", sent_path=sp)
    assert all(ok for ok, _ in r.values()) and calls == ["111", "-100222"]
    r = bd.send_all("s", "gate7", "hi", sent_path=sp)  # nothing repeats
    assert not any(ok for ok, _ in r.values()) and len(calls) == 2
    assert json.load(open(sp))["s"] == ["gate7", "gate7@channel"]


def test_one_target_failing_does_not_block_the_other(tmp_path, monkeypatch):
    monkeypatch.setattr(bd, "send_message", lambda text, chat_id=None: (chat_id != "111", "x"))
    monkeypatch.setattr(bd, "targets", lambda: [("chat", "111"), ("channel", "-100222")])
    r = bd.send_all("s", "scan", "hi", sent_path=str(tmp_path / "sent.json"))
    assert r["chat"][0] is False and r["channel"][0] is True


def test_targets_reads_env(monkeypatch):
    monkeypatch.setattr(bd, "load_env", lambda *a, **k: None)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "-1002")
    assert bd.targets() == [("chat", "1"), ("channel", "-1002")]
    monkeypatch.delenv("TELEGRAM_CHANNEL_ID")
    assert bd.targets() == [("chat", "1")]
