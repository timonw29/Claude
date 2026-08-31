import json
import os

from . import config


def _load():
    if not os.path.exists(config.PROFILE_FILE):
        return []
    try:
        with open(config.PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(facts):
    os.makedirs(config.HISTORY_DIR, exist_ok=True)
    with open(config.PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(facts, f, ensure_ascii=False, indent=2)


def remember(category, fact):
    facts = _load()
    facts.append({"category": category, "fact": fact})
    _save(facts)
    return f"Gemerkt ({category}): {fact}"


def list_facts():
    facts = _load()
    if not facts:
        return "Noch nichts über den Nutzer gespeichert."
    return "\n".join(f"- [{f['category']}] {f['fact']}" for f in facts)


def forget(fact_substring):
    facts = _load()
    remaining = [f for f in facts if fact_substring.lower() not in f["fact"].lower()]
    removed = len(facts) - len(remaining)
    if removed:
        _save(remaining)
        return f"{removed} Eintrag/Einträge entfernt."
    return f"Kein passender Eintrag zu '{fact_substring}' gefunden."


def get_location():
    if not os.path.exists(config.LOCATION_FILE):
        return None
    try:
        with open(config.LOCATION_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("city")
    except (json.JSONDecodeError, OSError):
        return None


def set_location(city):
    os.makedirs(config.HISTORY_DIR, exist_ok=True)
    with open(config.LOCATION_FILE, "w", encoding="utf-8") as f:
        json.dump({"city": city}, f, ensure_ascii=False)
    return f"Standort gespeichert: {city}"


def summary_for_prompt(limit=40):
    facts = _load()
    if not facts:
        return ""
    lines = [f"- [{f['category']}] {f['fact']}" for f in facts[-limit:]]
    return "Was du bereits über den Nutzer weißt (nutze das, ohne es abzufragen):\n" + "\n".join(
        lines
    )
