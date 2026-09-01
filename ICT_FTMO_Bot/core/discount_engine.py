"""Discount/Premium Engine - where does current price sit inside the active
dealing range (the most recent swing-high-to-swing-low leg)? Below the 50%
midpoint is "discount" (favorable for longs), above is "premium" (favorable
for shorts), and a narrow band around the midpoint is "equilibrium".
"""

from core.market_state import MarketState

EQUILIBRIUM_BAND = 0.05  # +/- 5% around the midpoint counts as equilibrium


def compute_zone(state: MarketState) -> MarketState:
    highs = [s.price for s in state.swing_points if s.kind == "high"]
    lows = [s.price for s in state.swing_points if s.kind == "low"]
    if not highs or not lows or state.ltf_data is None or len(state.ltf_data) == 0:
        return state

    range_high = highs[-1]
    range_low = lows[-1]
    if range_high <= range_low:
        return state

    state.dealing_range_high = range_high
    state.dealing_range_low = range_low

    price = state.ltf_data["close"].iloc[-1]
    position = (price - range_low) / (range_high - range_low)

    if abs(position - 0.5) <= EQUILIBRIUM_BAND:
        state.zone = "equilibrium"
    elif position < 0.5:
        state.zone = "discount"
    else:
        state.zone = "premium"

    return state


def update(state: MarketState) -> MarketState:
    return compute_zone(state)
