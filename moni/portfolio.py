import json
import os

from . import config


def _load():
    if not os.path.exists(config.PORTFOLIO_FILE):
        return []
    try:
        with open(config.PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(positions):
    os.makedirs(config.HISTORY_DIR, exist_ok=True)
    with open(config.PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(positions, f, ensure_ascii=False, indent=2)


def list_positions():
    positions = _load()
    if not positions:
        return "Keine Positionen hinterlegt."
    return "\n".join(f"- {p}" for p in positions)


def add_position(name):
    positions = _load()
    if name not in positions:
        positions.append(name)
        _save(positions)
    return f"Hinzugefügt: {name}"


def remove_position(name):
    positions = _load()
    match = next((p for p in positions if p.lower() == name.lower()), None)
    if not match:
        return f"Keine Position namens '{name}' gefunden."
    positions.remove(match)
    _save(positions)
    return f"Entfernt: {match}"
