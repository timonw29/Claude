import json
import os

from . import config


def _load():
    if not os.path.exists(config.TODOS_FILE):
        return []
    try:
        with open(config.TODOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(todos):
    os.makedirs(config.HISTORY_DIR, exist_ok=True)
    with open(config.TODOS_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def list_todos():
    return _load()


def add_todo(text):
    todos = _load()
    todos.append({"text": text, "done": False})
    _save(todos)
    return f"Aufgabe hinzugefügt: {text}"


def complete_todo(text_substring):
    todos = _load()
    match = next(
        (t for t in todos if not t["done"] and text_substring.lower() in t["text"].lower()), None
    )
    if not match:
        return f"Keine offene Aufgabe zu '{text_substring}' gefunden."
    match["done"] = True
    _save(todos)
    return f"Erledigt: {match['text']}"


def remove_todo(text_substring):
    todos = _load()
    remaining = [t for t in todos if text_substring.lower() not in t["text"].lower()]
    removed = len(todos) - len(remaining)
    if removed:
        _save(remaining)
        return f"{removed} Aufgabe(n) entfernt."
    return f"Keine Aufgabe zu '{text_substring}' gefunden."


def toggle_by_index(index):
    todos = _load()
    if 0 <= index < len(todos):
        todos[index]["done"] = not todos[index]["done"]
        _save(todos)
        return True
    return False
