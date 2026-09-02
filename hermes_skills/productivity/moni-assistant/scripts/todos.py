#!/usr/bin/env python3
"""To-do list CLI - same ~/.moni/todos.json format as the original Moni web
app (moni/todos.py), so existing data carries over unchanged."""

import argparse
import json
import os

FILE = os.path.expanduser("~/.moni/todos.json")


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(todos):
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def cmd_list(_args):
    todos = _load()
    if not todos:
        print("Keine Aufgaben.")
        return
    for i, t in enumerate(todos):
        mark = "x" if t["done"] else " "
        print(f"[{mark}] {i}: {t['text']}")


def cmd_add(args):
    todos = _load()
    todos.append({"text": args.text, "done": False})
    _save(todos)
    print(f"Aufgabe hinzugefügt: {args.text}")


def cmd_complete(args):
    todos = _load()
    match = next((t for t in todos if not t["done"] and args.text_substring.lower() in t["text"].lower()), None)
    if not match:
        print(f"Keine offene Aufgabe zu '{args.text_substring}' gefunden.")
        return
    match["done"] = True
    _save(todos)
    print(f"Erledigt: {match['text']}")


def cmd_remove(args):
    todos = _load()
    remaining = [t for t in todos if args.text_substring.lower() not in t["text"].lower()]
    removed = len(todos) - len(remaining)
    if removed:
        _save(remaining)
        print(f"{removed} Aufgabe(n) entfernt.")
    else:
        print(f"Keine Aufgabe zu '{args.text_substring}' gefunden.")


def main():
    parser = argparse.ArgumentParser(description="Moni-Aufgabenliste verwalten")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list").set_defaults(func=cmd_list)
    p_add = sub.add_parser("add")
    p_add.add_argument("text")
    p_add.set_defaults(func=cmd_add)
    p_complete = sub.add_parser("complete")
    p_complete.add_argument("text_substring")
    p_complete.set_defaults(func=cmd_complete)
    p_remove = sub.add_parser("remove")
    p_remove.add_argument("text_substring")
    p_remove.set_defaults(func=cmd_remove)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
