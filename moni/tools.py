import json
import os
import subprocess

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
]

# Tools that touch the filesystem or run commands - callers (CLI, web app)
# are expected to gate these behind a confirmation step before calling
# run_tool; this module only executes.
CONFIRM_REQUIRED = {"run_shell_command", "write_file"}


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
