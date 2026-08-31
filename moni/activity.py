import json
import os
import time

from . import config

MAX_ENTRIES = 50


def _load():
    if not os.path.exists(config.ACTIVITY_FILE):
        return []
    try:
        with open(config.ACTIVITY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries):
    os.makedirs(config.HISTORY_DIR, exist_ok=True)
    with open(config.ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump(entries[-MAX_ENTRIES:], f, ensure_ascii=False, indent=2)


def log(text):
    entries = _load()
    entries.append({"text": text, "ts": time.time()})
    _save(entries)


def _relative_time(ts):
    delta = max(0, time.time() - ts)
    if delta < 60:
        return f"vor {int(delta)} s"
    if delta < 3600:
        return f"vor {int(delta / 60)} min"
    if delta < 86400:
        return f"vor {int(delta / 3600)} h"
    return f"vor {int(delta / 86400)} d"


def recent(n=10):
    entries = _load()[-n:][::-1]
    return [{"text": e["text"], "relative": _relative_time(e["ts"])} for e in entries]
