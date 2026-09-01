"""Session Engine V3 - determines the active trading session and whether
the current time falls inside an ICT "kill zone" (the narrower, higher-
probability windows at the start of London/New York). All times are UTC.
"""

from datetime import datetime, timezone

import config
from core.market_state import MarketState


def _in_range(hour: int, start: int, end: int) -> bool:
    return start <= hour < end


def update(state: MarketState, now: datetime = None) -> MarketState:
    now = now or datetime.now(timezone.utc)
    hour = now.hour

    state.active_session = None
    for name, (start, end) in config.SESSIONS.items():
        if _in_range(hour, start, end):
            state.active_session = name
            break

    state.in_kill_zone = None
    for name, (start, end) in config.KILL_ZONES.items():
        if _in_range(hour, start, end):
            state.in_kill_zone = name
            break

    return state
