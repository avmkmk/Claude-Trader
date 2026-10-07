"""
Telegram notifier - sends plain-text messages through the Telegram Bot API.

Config (environment variables, or simple-trader-api/.env which is gitignored):
    TELEGRAM_BOT_TOKEN   token from @BotFather
    TELEGRAM_CHAT_ID     your numeric chat id, or @channelname / -100... for a channel

send_message() never raises: the daily pipeline must not fail because Telegram is down.
The bot token is never logged or included in returned errors.
"""
import logging
import os
import time
from typing import List, Optional, Tuple

import requests

log = logging.getLogger(__name__)

API_URL = "https://api.telegram.org/bot{token}/{method}"
MAX_LEN = 4096
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")


def load_env(path: str = ENV_PATH) -> None:
    """Load KEY=VALUE lines from .env into os.environ (existing variables win; comments ignored)."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def split_message(text: str, limit: int = MAX_LEN) -> List[str]:
    """Split on line breaks so each chunk fits Telegram's per-message limit."""
    chunks, current = [], ""
    for line in text.split("\n"):
        while len(line) > limit:  # a single over-long line: hard split
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]
        if current and len(current) + 1 + len(line) > limit:
            chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        chunks.append(current)
    return chunks


def send_message(text: str, chat_id: Optional[str] = None, token: Optional[str] = None) -> Tuple[bool, str]:
    """Send text to Telegram. Returns (ok, detail). Never raises."""
    load_env()
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return False, "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set"
    url = API_URL.format(token=token, method="sendMessage")
    for chunk in split_message(text):
        for attempt in range(2):  # one retry, only for rate limiting
            try:
                r = requests.post(url, json={"chat_id": chat_id, "text": chunk,
                                             "disable_web_page_preview": True}, timeout=20)
            except requests.RequestException as e:
                return False, f"network error: {type(e).__name__}"
            if r.status_code == 429 and attempt == 0:
                try:
                    wait = int(r.json().get("parameters", {}).get("retry_after", 1))
                except ValueError:
                    wait = 1
                time.sleep(min(wait, 30))
                continue
            if r.status_code != 200:
                try:
                    desc = r.json().get("description", "")
                except ValueError:
                    desc = ""
                return False, f"HTTP {r.status_code}: {desc}"
            break
    return True, "sent"
