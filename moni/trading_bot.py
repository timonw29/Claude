import datetime
import json
import os
import subprocess

from . import config

BOT_DIR = os.path.join(config.REPO_PATH, "ICT_FTMO_Bot")
STATE_FILE = os.path.join(config.HISTORY_DIR, "trading_bot.json")
LOG_FILE = os.path.join(config.HISTORY_DIR, "trading_bot.log")


def _load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(state):
    os.makedirs(config.HISTORY_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def run_backtest(symbol, htf_csv, ltf_csv, balance=10000.0):
    """Runs ICT_FTMO_Bot/backtest_engine.py as a subprocess - no MT5 needed,
    safe to run on the Moni droplet itself - and returns its text report."""
    if not os.path.isdir(BOT_DIR):
        return f"ICT_FTMO_Bot nicht gefunden unter {BOT_DIR}."
    try:
        result = subprocess.run(
            [
                "python3",
                "backtest_engine.py",
                "--symbol",
                symbol,
                "--htf-csv",
                htf_csv,
                "--ltf-csv",
                ltf_csv,
                "--balance",
                str(balance),
            ],
            cwd=BOT_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "Backtest abgebrochen: Zeitlimit (5 min) überschritten."
    if result.returncode != 0:
        return f"Backtest fehlgeschlagen:\n{result.stderr[-3000:]}"
    return result.stdout


def bot_status():
    state = _load_state()
    pid = state.get("pid")
    if not pid:
        return {"running": False}
    try:
        os.kill(pid, 0)
        return {"running": True, "pid": pid, "started_at": state.get("started_at")}
    except OSError:
        return {"running": False}


def start_live_bot():
    """Starts ICT_FTMO_Bot/main.py in the background. Honest limitation:
    main.py needs a real, reachable MT5 terminal - officially Windows-only -
    so on the Linux Moni droplet this process will start and then exit
    almost immediately with a clear MT5ConnectionError (see its log). It
    only actually trades once ICT_FTMO_Bot runs somewhere with a real MT5
    terminal (Windows machine/VM, or a Wine-based setup)."""
    if not os.path.isdir(BOT_DIR):
        return f"ICT_FTMO_Bot nicht gefunden unter {BOT_DIR}."
    status = bot_status()
    if status["running"]:
        return f"Läuft bereits (PID {status['pid']})."

    os.makedirs(config.HISTORY_DIR, exist_ok=True)
    log_handle = open(LOG_FILE, "a", encoding="utf-8")
    proc = subprocess.Popen(["python3", "main.py"], cwd=BOT_DIR, stdout=log_handle, stderr=subprocess.STDOUT)
    _save_state({"pid": proc.pid, "started_at": datetime.datetime.now().isoformat()})
    return (
        f"Gestartet (PID {proc.pid}). Log: {LOG_FILE} - prüf den Status gleich nochmal, "
        "auf einem Server ohne echtes MT5-Terminal beendet sich der Prozess sofort wieder."
    )


def stop_live_bot():
    state = _load_state()
    pid = state.get("pid")
    if not pid:
        return "Läuft nicht."
    try:
        os.kill(pid, 15)  # SIGTERM
    except OSError:
        pass
    _save_state({})
    return f"Gestoppt (PID {pid})."
