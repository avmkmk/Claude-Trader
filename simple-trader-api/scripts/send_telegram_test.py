"""Send one test message to Telegram.   python scripts/send_telegram_test.py "hello"

Also: --whoami lists the chat ids that have messaged your bot (send the bot any message first),
which is how you find TELEGRAM_CHAT_ID. Only chat ids and names are printed, never the token.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests  # noqa: E402

from app.services.telegram_notifier import API_URL, load_env, send_message  # noqa: E402


def whoami() -> int:
    load_env()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("TELEGRAM_BOT_TOKEN is not set (put it in simple-trader-api/.env)")
        return 1
    r = requests.get(API_URL.format(token=token, method="getUpdates"), timeout=20)
    if r.status_code != 200:
        print(f"HTTP {r.status_code}: {r.json().get('description', '')}")
        return 1
    seen = {}
    for u in r.json().get("result", []):
        chat = (u.get("message") or u.get("channel_post") or {}).get("chat")
        if chat:
            seen[chat["id"]] = chat.get("username") or chat.get("title") or chat.get("first_name", "")
    if not seen:
        print("No messages yet - open your bot in Telegram, press Start / send it any message, then re-run.")
        return 1
    for cid, name in seen.items():
        print(f"chat_id={cid}  ({name})")
    return 0


def main() -> int:
    if "--whoami" in sys.argv:
        return whoami()
    text = " ".join(a for a in sys.argv[1:]) or "SimpleTrader test message"
    ok, detail = send_message(text)
    print(("OK: " if ok else "FAILED: ") + detail)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
