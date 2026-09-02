#!/usr/bin/env python3
"""Portfolio CLI - same ~/.moni/portfolio.json format as the original Moni
web app (moni/portfolio.py), so existing data carries over unchanged."""

import argparse
import json
import os

FILE = os.path.expanduser("~/.moni/portfolio.json")


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(positions):
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(positions, f, ensure_ascii=False, indent=2)


def cmd_list(_args):
    positions = _load()
    print("Keine Positionen hinterlegt." if not positions else "\n".join(f"- {p}" for p in positions))


def cmd_add(args):
    positions = _load()
    if args.name not in positions:
        positions.append(args.name)
        _save(positions)
    print(f"Hinzugefügt: {args.name}")


def cmd_remove(args):
    positions = _load()
    match = next((p for p in positions if p.lower() == args.name.lower()), None)
    if not match:
        print(f"Keine Position namens '{args.name}' gefunden.")
        return
    positions.remove(match)
    _save(positions)
    print(f"Entfernt: {match}")


def main():
    parser = argparse.ArgumentParser(description="Moni-Portfolio verwalten")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list").set_defaults(func=cmd_list)
    p_add = sub.add_parser("add")
    p_add.add_argument("name")
    p_add.set_defaults(func=cmd_add)
    p_remove = sub.add_parser("remove")
    p_remove.add_argument("name")
    p_remove.set_defaults(func=cmd_remove)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
