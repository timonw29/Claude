"""Trade Management Engine - rules applied to an already-open position:
move to breakeven once price has moved 1R in favor, and take partial profit
at 2R. Works against a plain dict/object with entry, stop_loss, take_profit,
direction and size fields - both the live mt5_connector position wrapper and
the backtest Trade class expose that same shape, so this logic runs
identically in both.
"""

BREAKEVEN_AT_R = 1.0
PARTIAL_AT_R = 2.0
PARTIAL_CLOSE_FRACTION = 0.5


def _r_multiple(position, current_price: float) -> float:
    risk = abs(position["entry"] - position["stop_loss"])
    if risk == 0:
        return 0.0
    if position["direction"] == "bullish":
        return (current_price - position["entry"]) / risk
    return (position["entry"] - current_price) / risk


def evaluate(position: dict, current_price: float) -> dict:
    """Returns a dict of actions to take, e.g. {"move_stop_to": x} and/or
    {"close_fraction": 0.5}. Empty dict means: do nothing this cycle."""
    actions = {}
    r = _r_multiple(position, current_price)

    if r >= BREAKEVEN_AT_R and not position.get("breakeven_done"):
        actions["move_stop_to"] = position["entry"]
        actions["mark_breakeven_done"] = True

    if r >= PARTIAL_AT_R and not position.get("partial_done"):
        actions["close_fraction"] = PARTIAL_CLOSE_FRACTION
        actions["mark_partial_done"] = True

    return actions
