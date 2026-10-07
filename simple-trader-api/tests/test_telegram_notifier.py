"""Tests for telegram_notifier.py (no network: requests.post is mocked)."""
from unittest.mock import MagicMock

import requests

from app.services import telegram_notifier as tn


def _resp(status=200, body=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = body or {}
    return r


def test_split_message_short_text_is_one_chunk():
    assert tn.split_message("hello") == ["hello"]


def test_split_message_respects_limit_and_loses_nothing():
    text = "\n".join(f"line {i} " + "x" * 50 for i in range(200))
    chunks = tn.split_message(text, limit=500)
    assert all(len(c) <= 500 for c in chunks)
    assert "\n".join(chunks) == text


def test_split_message_hard_splits_overlong_line():
    chunks = tn.split_message("a" * 1000, limit=400)
    assert [len(c) for c in chunks] == [400, 400, 200]


def test_missing_config_returns_false_without_calling_network(monkeypatch):
    monkeypatch.setattr(tn, "load_env", lambda *a, **k: None)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    post = MagicMock()
    monkeypatch.setattr(tn.requests, "post", post)
    ok, detail = tn.send_message("hi")
    assert not ok and "not set" in detail
    post.assert_not_called()


def test_success_posts_to_send_message(monkeypatch):
    monkeypatch.setattr(tn, "load_env", lambda *a, **k: None)
    post = MagicMock(return_value=_resp(200))
    monkeypatch.setattr(tn.requests, "post", post)
    ok, _ = tn.send_message("hi", chat_id="123", token="TOK")
    assert ok
    assert post.call_args.args[0].endswith("/botTOK/sendMessage")
    assert post.call_args.kwargs["json"]["chat_id"] == "123"


def test_http_error_is_reported_and_token_not_leaked(monkeypatch):
    monkeypatch.setattr(tn, "load_env", lambda *a, **k: None)
    monkeypatch.setattr(tn.requests, "post", MagicMock(return_value=_resp(401, {"description": "Unauthorized"})))
    ok, detail = tn.send_message("hi", chat_id="1", token="SECRETTOKEN")
    assert not ok and "401" in detail and "SECRETTOKEN" not in detail


def test_network_error_never_raises_and_token_not_leaked(monkeypatch):
    monkeypatch.setattr(tn, "load_env", lambda *a, **k: None)
    monkeypatch.setattr(tn.requests, "post", MagicMock(side_effect=requests.ConnectionError("boom SECRETTOKEN")))
    ok, detail = tn.send_message("hi", chat_id="1", token="SECRETTOKEN")
    assert not ok and "SECRETTOKEN" not in detail


def test_rate_limit_retries_once(monkeypatch):
    monkeypatch.setattr(tn, "load_env", lambda *a, **k: None)
    monkeypatch.setattr(tn.time, "sleep", lambda s: None)
    post = MagicMock(side_effect=[_resp(429, {"parameters": {"retry_after": 1}}), _resp(200)])
    monkeypatch.setattr(tn.requests, "post", post)
    ok, _ = tn.send_message("hi", chat_id="1", token="T")
    assert ok and post.call_count == 2


def test_load_env_sets_missing_only_and_skips_comments(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text('# TELEGRAM_BOT_TOKEN=commented\nTELEGRAM_CHAT_ID="42"\nKEEP=fromfile\n', encoding="utf-8")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setenv("KEEP", "fromenv")
    tn.load_env(str(f))
    assert "TELEGRAM_BOT_TOKEN" not in tn.os.environ
    assert tn.os.environ["TELEGRAM_CHAT_ID"] == "42"
    assert tn.os.environ["KEEP"] == "fromenv"
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
