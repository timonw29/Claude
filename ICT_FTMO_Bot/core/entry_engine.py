"""Entry Engine V4 - turns a sufficiently strong confluence read into a
concrete trade signal (entry, stop-loss, take-profit). Requires the
confluence score to clear config.MIN_CONFLUENCE_SCORE and the resulting
risk:reward to clear config.MIN_RISK_REWARD - otherwise no signal is
produced, which is the expected/normal outcome most cycles.
"""

import config
from core.market_state import MarketState

STOP_BUFFER_PIPS = 2.0


def _pip_size(symbol: str) -> float:
    from core.liquidity_engine import pip_size

    return pip_size(symbol)


def _nearest_target(levels: list, entry: float, direction: str):
    if not levels:
        return None
    if direction == "bullish":
        candidates = [lvl for lvl in levels if lvl > entry]
        return min(candidates) if candidates else None
    candidates = [lvl for lvl in levels if lvl < entry]
    return max(candidates) if candidates else None


def build_signal(state: MarketState) -> MarketState:
    state.signal = None
    if state.confluence_score < config.MIN_CONFLUENCE_SCORE:
        return state
    direction = state.htf_trend
    if direction not in ("bullish", "bearish"):
        return state
    if state.ltf_data is None or len(state.ltf_data) == 0:
        return state

    entry = float(state.ltf_data["close"].iloc[-1])
    buffer = STOP_BUFFER_PIPS * _pip_size(state.symbol)

    unmitigated_obs = [o for o in state.order_blocks if o["direction"] == direction and not o["mitigated"]]

    if direction == "bullish":
        stop_ref = min((o["bottom"] for o in unmitigated_obs), default=state.dealing_range_low)
        if stop_ref is None:
            return state
        stop_loss = stop_ref - buffer
        target = _nearest_target(state.buy_side_liquidity, entry, direction)
    else:
        stop_ref = max((o["top"] for o in unmitigated_obs), default=state.dealing_range_high)
        if stop_ref is None:
            return state
        stop_loss = stop_ref + buffer
        target = _nearest_target(state.sell_side_liquidity, entry, direction)

    risk = abs(entry - stop_loss)
    if risk <= 0:
        return state

    if target is None:
        # No known liquidity target - fall back to a fixed R multiple.
        reward = risk * config.MIN_RISK_REWARD
        take_profit = entry + reward if direction == "bullish" else entry - reward
    else:
        take_profit = target
        reward = abs(take_profit - entry)

    if reward / risk < config.MIN_RISK_REWARD:
        return state

    state.signal = {
        "symbol": state.symbol,
        "direction": direction,
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "risk_reward": round(reward / risk, 2),
        "confluence_score": state.confluence_score,
        "reason": "; ".join(state.confluence_notes),
    }
    return state


def update(state: MarketState) -> MarketState:
    return build_signal(state)
