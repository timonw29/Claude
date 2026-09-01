"""Central configuration for the ICT/FTMO bot.

Safety model: the bot trades fully autonomously (no per-trade confirmation),
so the account-type gate below is the only thing standing between "runs
against a demo account" and "risks real/challenge money." ALLOW_LIVE_TRADING
must be explicitly set to "true" - the default is always demo.
"""

import os

# --- MT5 connection -------------------------------------------------------
MT5_LOGIN = os.environ.get("MT5_LOGIN")
MT5_PASSWORD = os.environ.get("MT5_PASSWORD")
MT5_SERVER = os.environ.get("MT5_SERVER")
MT5_PATH = os.environ.get("MT5_PATH")  # optional: path to terminal64.exe

# "demo" (default) or "live" - main.py refuses to place real orders unless
# this is "live" AND ALLOW_LIVE_TRADING is explicitly "true".
MT5_ACCOUNT_TYPE = os.environ.get("MT5_ACCOUNT_TYPE", "demo").lower()
ALLOW_LIVE_TRADING = os.environ.get("ALLOW_LIVE_TRADING", "false").lower() == "true"

# --- Instruments & timeframes ----------------------------------------------
SYMBOLS = os.environ.get("ICT_SYMBOLS", "EURUSD,GBPUSD,XAUUSD").split(",")

# Higher timeframe = bias/structure, lower timeframe = entries.
HTF = os.environ.get("ICT_HTF", "H4")
LTF = os.environ.get("ICT_LTF", "M15")
TIMEFRAMES = [HTF, LTF]

BARS_TO_FETCH = int(os.environ.get("ICT_BARS", "1000"))

# --- Sessions (UTC hour ranges) --------------------------------------------
SESSIONS = {
    "asia": (0, 7),
    "london": (7, 12),
    "new_york": (12, 21),
}
# ICT "kill zones" - narrower high-probability windows inside a session.
KILL_ZONES = {
    "london_open": (7, 10),
    "new_york_open": (12, 15),
}

# --- Risk / FTMO-style limits ----------------------------------------------
RISK_PER_TRADE_PCT = float(os.environ.get("ICT_RISK_PER_TRADE_PCT", "0.5"))
MAX_DAILY_LOSS_PCT = float(os.environ.get("ICT_MAX_DAILY_LOSS_PCT", "4.0"))
MAX_TOTAL_DRAWDOWN_PCT = float(os.environ.get("ICT_MAX_TOTAL_DRAWDOWN_PCT", "9.0"))
MAX_OPEN_POSITIONS = int(os.environ.get("ICT_MAX_OPEN_POSITIONS", "3"))
MIN_RISK_REWARD = float(os.environ.get("ICT_MIN_RR", "2.0"))

# --- ICT concept parameters -------------------------------------------------
OTE_FIB_LOW = 0.618
OTE_FIB_HIGH = 0.79
SWING_LOOKBACK = int(os.environ.get("ICT_SWING_LOOKBACK", "3"))  # fractal window each side
EQUAL_LEVEL_TOLERANCE_PIPS = float(os.environ.get("ICT_EQ_TOLERANCE_PIPS", "3.0"))
MIN_CONFLUENCE_SCORE = float(os.environ.get("ICT_MIN_CONFLUENCE", "0.7"))

# --- Paths ------------------------------------------------------------------
LOG_DIR = os.environ.get("ICT_LOG_DIR", os.path.join(os.path.dirname(__file__), "logs"))
