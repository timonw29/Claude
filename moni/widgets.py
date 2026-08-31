import datetime
import json
import os

from . import config


def _load():
    if not os.path.exists(config.WIDGETS_FILE):
        return []
    try:
        with open(config.WIDGETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(widgets):
    os.makedirs(config.HISTORY_DIR, exist_ok=True)
    with open(config.WIDGETS_FILE, "w", encoding="utf-8") as f:
        json.dump(widgets, f, ensure_ascii=False, indent=2)


def pin(title, content):
    widgets = _load()
    now = datetime.datetime.now().isoformat()
    for w in widgets:
        if w["title"].lower() == title.lower():
            w["content"] = content
            w["updated_at"] = now
            _save(widgets)
            return f"Aktualisiert: {title}"
    widgets.append({"title": title, "content": content, "updated_at": now})
    _save(widgets)
    return f"Auf der Startseite angeheftet: {title}"


def unpin(title_substring):
    widgets = _load()
    remaining = [w for w in widgets if title_substring.lower() not in w["title"].lower()]
    removed = len(widgets) - len(remaining)
    if removed:
        _save(remaining)
        return f"{removed} Pin(s) entfernt."
    return f"Kein Pin zu '{title_substring}' gefunden."


def list_widgets():
    return _load()
