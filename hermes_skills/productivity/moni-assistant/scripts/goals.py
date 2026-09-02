#!/usr/bin/env python3
"""Progress-goals CLI - same ~/.moni/goals.json format as the original Moni
web app (moni/goals.py), so existing data carries over unchanged."""

import argparse
import json
import os

FILE = os.path.expanduser("~/.moni/goals.json")


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(goals):
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, ensure_ascii=False, indent=2)


def cmd_list(_args):
    goals = _load()
    if not goals:
        print("Keine Ziele gesetzt.")
        return
    for g in goals:
        print(f"- {g['label']}: {g['current']}/{g['target']}")


def cmd_set(args):
    goals = _load()
    match = next((g for g in goals if g["label"].lower() == args.label.lower()), None)
    if match:
        match["current"] = args.current
        match["target"] = args.target
    else:
        goals.append({"label": args.label, "current": args.current, "target": args.target})
    _save(goals)
    print(f"Ziel '{args.label}': {args.current}/{args.target}")


def cmd_update(args):
    goals = _load()
    match = next((g for g in goals if args.label.lower() in g["label"].lower()), None)
    if not match:
        print(f"Kein Ziel zu '{args.label}' gefunden.")
        return
    match["current"] = args.current
    _save(goals)
    print(f"Ziel '{match['label']}' aktualisiert: {args.current}/{match['target']}")


def cmd_remove(args):
    goals = _load()
    remaining = [g for g in goals if args.label.lower() not in g["label"].lower()]
    removed = len(goals) - len(remaining)
    if removed:
        _save(remaining)
        print(f"{removed} Ziel(e) entfernt.")
    else:
        print(f"Kein Ziel zu '{args.label}' gefunden.")


def main():
    parser = argparse.ArgumentParser(description="Moni-Fortschrittsziele verwalten")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list").set_defaults(func=cmd_list)
    p_set = sub.add_parser("set")
    p_set.add_argument("label")
    p_set.add_argument("current", type=float)
    p_set.add_argument("target", type=float)
    p_set.set_defaults(func=cmd_set)
    p_update = sub.add_parser("update")
    p_update.add_argument("label")
    p_update.add_argument("current", type=float)
    p_update.set_defaults(func=cmd_update)
    p_remove = sub.add_parser("remove")
    p_remove.add_argument("label")
    p_remove.set_defaults(func=cmd_remove)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
