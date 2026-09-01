import json
import os
import subprocess

from . import gcalendar, gmail, goals, portfolio, profile, todos, trading_bot, widgets

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
    {
        "name": "propose_code_change",
        "description": (
            "Use the Claude coding agent to implement a change to Moni's own "
            "source code, on a new git branch (never the live branch). Does "
            "NOT push, merge, or redeploy - the user reviews and deploys "
            "manually. Use only when the user explicitly asks for a code "
            "change or new feature to be implemented in Moni herself."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Clear description of the change to implement.",
                }
            },
            "required": ["description"],
        },
    },
    {
        "name": "set_location",
        "description": (
            "Save the user's home city/location, e.g. after they mention "
            "where they live. Used for the weather dashboard tile."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name."}},
            "required": ["city"],
        },
    },
    {
        "name": "pin_to_dashboard",
        "description": (
            "Pin or update a custom widget on the user's dashboard home "
            "screen - e.g. a message, a stock price snapshot, a reminder, "
            "or anything else they want visible at a glance. Calling it "
            "again with the same title updates that widget instead of "
            "creating a duplicate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short widget title, e.g. 'Apple-Kurs' or 'Notiz'.",
                },
                "content": {
                    "type": "string",
                    "description": "The text to show, e.g. 'AAPL: 231,50 $ (+0,8%)'.",
                },
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "unpin_from_dashboard",
        "description": "Remove a previously pinned dashboard widget.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title_substring": {
                    "type": "string",
                    "description": "Substring matching the widget title to remove.",
                }
            },
            "required": ["title_substring"],
        },
    },
    {
        "name": "list_todos",
        "description": "List the user's current to-do list (open and done items).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "add_todo",
        "description": "Add a new item to the user's to-do list.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The task text."}
            },
            "required": ["text"],
        },
    },
    {
        "name": "complete_todo",
        "description": "Mark an open to-do item as done, matched by a substring of its text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text_substring": {
                    "type": "string",
                    "description": "Substring matching the open task to complete.",
                }
            },
            "required": ["text_substring"],
        },
    },
    {
        "name": "remove_todo",
        "description": "Delete a to-do item, matched by a substring of its text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text_substring": {
                    "type": "string",
                    "description": "Substring matching the task(s) to remove.",
                }
            },
            "required": ["text_substring"],
        },
    },
    {
        "name": "list_goals",
        "description": "List the user's tracked progress goals (e.g. Laufen, Sparziel) with current/target values.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "set_goal",
        "description": (
            "Create or fully redefine a progress goal with a label, current "
            "value, and target value, e.g. 'Laufen', 6, 20 (km diese Woche)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string", "description": "Short goal label, e.g. 'Laufen'."},
                "current": {"type": "number", "description": "Current progress value."},
                "target": {"type": "number", "description": "Target value."},
            },
            "required": ["label", "current", "target"],
        },
    },
    {
        "name": "update_goal_progress",
        "description": (
            "Update just the current progress value of an existing goal, "
            "matched by a substring of its label, e.g. after the user "
            "mentions new progress ('ich bin heute 6km gelaufen')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string", "description": "Substring matching the goal label."},
                "current": {"type": "number", "description": "New current progress value."},
            },
            "required": ["label", "current"],
        },
    },
    {
        "name": "remove_goal",
        "description": "Delete a tracked progress goal, matched by a substring of its label.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string", "description": "Substring matching the goal(s) to remove."}
            },
            "required": ["label"],
        },
    },
    {
        "name": "list_unread_emails",
        "description": (
            "List the user's unread Gmail messages (sender, subject, "
            "snippet). Requires Google to be connected - if it isn't, say "
            "so honestly instead of inventing emails."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "send_email",
        "description": (
            "Send an email from the user's Gmail account. Requires Google "
            "to be connected. Use only when the user explicitly asks to "
            "send an email."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address."},
                "subject": {"type": "string", "description": "Email subject line."},
                "body": {"type": "string", "description": "Email body text."},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "list_todays_events",
        "description": (
            "List the user's Google Calendar events for today. Requires "
            "Google to be connected - if it isn't, say so honestly instead "
            "of inventing appointments."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "create_calendar_event",
        "description": "Create a new event on the user's Google Calendar. Requires Google to be connected.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Event title."},
                "start_iso": {
                    "type": "string",
                    "description": "Start time, ISO 8601 with timezone offset, e.g. 2026-09-01T15:00:00+02:00.",
                },
                "end_iso": {
                    "type": "string",
                    "description": "End time, ISO 8601 with timezone offset.",
                },
                "description": {"type": "string", "description": "Optional event description."},
            },
            "required": ["summary", "start_iso", "end_iso"],
        },
    },
    {
        "name": "delete_calendar_event",
        "description": (
            "Delete an upcoming event on the user's Google Calendar, "
            "matched by a substring of its title. Requires Google to be "
            "connected."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title_substring": {
                    "type": "string",
                    "description": "Substring matching the event title to delete.",
                }
            },
            "required": ["title_substring"],
        },
    },
    {
        "name": "run_ict_backtest",
        "description": (
            "Run the ICT_FTMO_Bot backtest engine against historical CSV "
            "candle data (no MT5/live account involved) and return the "
            "performance report. Use this whenever the user wants to test "
            "or tune the trading strategy, never to place real trades."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name, e.g. 'EURUSD'."},
                "htf_csv": {
                    "type": "string",
                    "description": "Path to the higher-timeframe (bias/structure) CSV.",
                },
                "ltf_csv": {
                    "type": "string",
                    "description": "Path to the lower-timeframe (entry) CSV.",
                },
                "balance": {"type": "number", "description": "Starting balance for the backtest."},
            },
            "required": ["symbol", "htf_csv", "ltf_csv"],
        },
    },
    {
        "name": "ict_bot_status",
        "description": "Check whether the live ICT_FTMO_Bot process is currently running.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "start_ict_bot",
        "description": (
            "Start ICT_FTMO_Bot's live trading loop as a background "
            "process. It connects to MT5 and trades fully autonomously, "
            "with no further confirmation per trade - only use this when "
            "the user explicitly asks to start live/demo trading, and only "
            "after they understand it needs a real MT5 terminal reachable "
            "from wherever it runs (it will exit immediately with an error "
            "on a plain Linux server without one)."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "stop_ict_bot",
        "description": "Stop the running ICT_FTMO_Bot live trading process.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]

# Tools that touch the filesystem or run commands - callers (CLI, web app)
# are expected to gate these behind a confirmation step before calling
# run_tool; this module only executes.
CONFIRM_REQUIRED = {
    "run_shell_command",
    "write_file",
    "propose_code_change",
    "send_email",
    "create_calendar_event",
    "delete_calendar_event",
    "run_ict_backtest",
    "start_ict_bot",
    "stop_ict_bot",
}

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
        if name == "set_location":
            return profile.set_location(tool_input["city"])
        if name == "pin_to_dashboard":
            return widgets.pin(tool_input["title"], tool_input["content"])
        if name == "unpin_from_dashboard":
            return widgets.unpin(tool_input["title_substring"])
        if name == "list_todos":
            return todos.list_todos()
        if name == "add_todo":
            return todos.add_todo(tool_input["text"])
        if name == "complete_todo":
            return todos.complete_todo(tool_input["text_substring"])
        if name == "remove_todo":
            return todos.remove_todo(tool_input["text_substring"])
        if name == "list_goals":
            return goals.list_goals()
        if name == "set_goal":
            return goals.set_goal(tool_input["label"], tool_input["current"], tool_input["target"])
        if name == "update_goal_progress":
            return goals.update_progress(tool_input["label"], tool_input["current"])
        if name == "remove_goal":
            return goals.remove_goal(tool_input["label"])
        if name == "list_unread_emails":
            return gmail.list_unread()
        if name == "send_email":
            return gmail.send_email(tool_input["to"], tool_input["subject"], tool_input["body"])
        if name == "list_todays_events":
            return gcalendar.list_today_events_text()
        if name == "create_calendar_event":
            return gcalendar.create_event(
                tool_input["summary"],
                tool_input["start_iso"],
                tool_input["end_iso"],
                tool_input.get("description"),
            )
        if name == "delete_calendar_event":
            return gcalendar.delete_event_by_title(tool_input["title_substring"])
        if name == "run_ict_backtest":
            return trading_bot.run_backtest(
                tool_input["symbol"],
                tool_input["htf_csv"],
                tool_input["ltf_csv"],
                tool_input.get("balance", 10000.0),
            )
        if name == "ict_bot_status":
            return trading_bot.bot_status()
        if name == "start_ict_bot":
            return trading_bot.start_live_bot()
        if name == "stop_ict_bot":
            return trading_bot.stop_live_bot()
        if name == "propose_code_change":
            from . import self_dev  # local import: heavier optional dependency

            return self_dev.propose_change(tool_input["description"])
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
