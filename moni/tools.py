import json
import os
import subprocess

from . import portfolio, profile

TOOLS = [
    {
        "name": "run_shell_command",
        "description": (
            "Execute a shell command on the user's machine and return stdout, "
            "stderr, and the exit code. Use this for automation: file "
            "operations, running scripts, checking system state, opening "
            "applications, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute.",
                }
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of a text file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file."}
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write text content to a file, creating or overwriting it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file."},
                "content": {"type": "string", "description": "Content to write."},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_directory",
        "description": "List files and folders in a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path. Defaults to the current directory.",
                }
            },
            "required": [],
        },
    },
    {"type": "web_search_20260209", "name": "web_search", "max_uses": 3},
    {
        "name": "list_portfolio",
        "description": "List the user's currently tracked stock/ETF portfolio positions.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "add_portfolio_position",
        "description": (
            "Add a new position to the user's tracked portfolio, e.g. after "
            "they mention buying a stock or ETF."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the stock/ETF, e.g. 'Nvidia' or 'MSCI World ETF'.",
                }
            },
            "required": ["name"],
        },
    },
    {
        "name": "remove_portfolio_position",
        "description": (
            "Remove a position from the user's tracked portfolio, e.g. after "
            "they mention selling it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the stock/ETF to remove."}
            },
            "required": ["name"],
        },
    },
    {
        "name": "remember_about_user",
        "description": (
            "Save a durable fact learned about the user (habits, work, "
            "preferences, personality) so future conversations can use it "
            "without asking again."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Short category, e.g. 'Beruf', 'Gewohnheiten', 'Vorlieben'.",
                },
                "fact": {"type": "string", "description": "The fact itself, one sentence."},
            },
            "required": ["category", "fact"],
        },
    },
    {
        "name": "recall_about_user",
        "description": "List everything currently remembered about the user.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "forget_about_user",
        "description": "Remove a previously remembered fact about the user that is outdated or wrong.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fact_substring": {
                    "type": "string",
                    "description": "A substring matching the fact(s) to remove.",
                }
            },
            "required": ["fact_substring"],
        },
    },
]

# Tools that touch the filesystem or run commands - callers (CLI, web app)
# are expected to gate these behind a confirmation step before calling
# run_tool; this module only executes.
CONFIRM_REQUIRED = {"run_shell_command", "write_file"}

# Tools safe to run unattended (e.g. the scheduled morning briefing) - never
# any tool from CONFIRM_REQUIRED, so an automated run can never end up
# blocked on a confirmation nobody is there to answer.
SAFE_TOOLS = [t for t in TOOLS if t.get("name") not in CONFIRM_REQUIRED]


def run_tool(name, tool_input):
    try:
        if name == "run_shell_command":
            return _run_shell_command(tool_input["command"])
        if name == "read_file":
            return _read_file(tool_input["path"])
        if name == "write_file":
            return _write_file(tool_input["path"], tool_input["content"])
        if name == "list_directory":
            return _list_directory(tool_input.get("path", "."))
        if name == "list_portfolio":
            return portfolio.list_positions()
        if name == "add_portfolio_position":
            return portfolio.add_position(tool_input["name"])
        if name == "remove_portfolio_position":
            return portfolio.remove_position(tool_input["name"])
        if name == "remember_about_user":
            return profile.remember(tool_input["category"], tool_input["fact"])
        if name == "recall_about_user":
            return profile.list_facts()
        if name == "forget_about_user":
            return profile.forget(tool_input["fact_substring"])
        return f"Unbekanntes Tool: {name}"
    except Exception as e:
        return f"Fehler: {e}"


def _run_shell_command(command):
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=60
    )
    return json.dumps(
        {
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
            "returncode": result.returncode,
        }
    )


def _read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()[:20000]


def _write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Geschrieben: {path} ({len(content)} Zeichen)"


def _list_directory(path):
    entries = os.listdir(path)
    return "\n".join(sorted(entries))
