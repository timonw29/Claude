#!/usr/bin/env python3
"""User-profile/memory + location CLI - same ~/.moni/profile.json and
~/.moni/location.json format as the original Moni web app (moni/profile.py),
so existing data carries over unchanged."""

import argparse
import json
import os

PROFILE_FILE = os.path.expanduser("~/.moni/profile.json")
LOCATION_FILE = os.path.expanduser("~/.moni/location.json")


def _load(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cmd_remember(args):
    facts = _load(PROFILE_FILE)
    facts.append({"category": args.category, "fact": args.fact})
    _save(PROFILE_FILE, facts)
    print(f"Gemerkt ({args.category}): {args.fact}")


def cmd_list(_args):
    facts = _load(PROFILE_FILE)
    if not facts:
        print("Noch nichts über den Nutzer gespeichert.")
        return
    for f in facts:
        print(f"- [{f['category']}] {f['fact']}")


def cmd_forget(args):
    facts = _load(PROFILE_FILE)
    remaining = [f for f in facts if args.fact_substring.lower() not in f["fact"].lower()]
    removed = len(facts) - len(remaining)
    if removed:
        _save(PROFILE_FILE, remaining)
        print(f"{removed} Eintrag/Einträge entfernt.")
    else:
        print(f"Kein passender Eintrag zu '{args.fact_substring}' gefunden.")


def cmd_set_location(args):
    _save(LOCATION_FILE, {"city": args.city})
    print(f"Standort gespeichert: {args.city}")


def cmd_get_location(_args):
    if not os.path.exists(LOCATION_FILE):
        print("Kein Standort hinterlegt.")
        return
    try:
        with open(LOCATION_FILE, "r", encoding="utf-8") as f:
            print(json.load(f).get("city", "Kein Standort hinterlegt."))
    except (json.JSONDecodeError, OSError):
        print("Kein Standort hinterlegt.")


def main():
    parser = argparse.ArgumentParser(description="Moni-Gedächtnis & Standort verwalten")
    sub = parser.add_subparsers(dest="command", required=True)
    p_remember = sub.add_parser("remember")
    p_remember.add_argument("category")
    p_remember.add_argument("fact")
    p_remember.set_defaults(func=cmd_remember)
    sub.add_parser("list").set_defaults(func=cmd_list)
    p_forget = sub.add_parser("forget")
    p_forget.add_argument("fact_substring")
    p_forget.set_defaults(func=cmd_forget)
    p_set_loc = sub.add_parser("set-location")
    p_set_loc.add_argument("city")
    p_set_loc.set_defaults(func=cmd_set_location)
    sub.add_parser("get-location").set_defaults(func=cmd_get_location)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
