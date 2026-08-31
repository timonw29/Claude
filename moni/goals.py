import json
import os

from . import config


def _load():
    if not os.path.exists(config.GOALS_FILE):
        return []
    try:
        with open(config.GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(goals):
    os.makedirs(config.HISTORY_DIR, exist_ok=True)
    with open(config.GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, ensure_ascii=False, indent=2)


def list_goals():
    return _load()


def set_goal(label, current, target):
    goals = _load()
    match = next((g for g in goals if g["label"].lower() == label.lower()), None)
    if match:
        match["current"] = current
        match["target"] = target
    else:
        goals.append({"label": label, "current": current, "target": target})
    _save(goals)
    return f"Ziel '{label}': {current}/{target}"


def update_progress(label, current):
    goals = _load()
    match = next((g for g in goals if label.lower() in g["label"].lower()), None)
    if not match:
        return f"Kein Ziel zu '{label}' gefunden."
    match["current"] = current
    _save(goals)
    return f"Ziel '{match['label']}' aktualisiert: {current}/{match['target']}"


def remove_goal(label):
    goals = _load()
    remaining = [g for g in goals if label.lower() not in g["label"].lower()]
    removed = len(goals) - len(remaining)
    if removed:
        _save(remaining)
        return f"{removed} Ziel(e) entfernt."
    return f"Kein Ziel zu '{label}' gefunden."
