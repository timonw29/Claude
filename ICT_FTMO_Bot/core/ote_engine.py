"""OTE Engine V2.1 - Optimal Trade Entry. Computes the 61.8%-79% Fibonacci
retracement zone of the most recent swing leg, in the direction of the
current lower-timeframe trend: in an uptrend that's a pullback zone to buy,
in a downtrend a rally zone to sell.
"""

import config
from core.market_state import MarketState


def compute_ote(state: MarketState) -> MarketState:
    highs = [s.price for s in state.swing_points if s.kind == "high"]
    lows = [s.price for s in state.swing_points if s.kind == "low"]
    if not highs or not lows:
        return state

    leg_high, leg_low = highs[-1], lows[-1]
    if leg_high <= leg_low:
        return state

    leg_range = leg_high - leg_low

    if state.ltf_trend == "bullish":
        zone_low = leg_high - leg_range * config.OTE_FIB_HIGH
        zone_high = leg_high - leg_range * config.OTE_FIB_LOW
        state.ote_zone = (zone_low, zone_high)
        state.ote_direction = "bullish"
    elif state.ltf_trend == "bearish":
        zone_low = leg_low + leg_range * config.OTE_FIB_LOW
        zone_high = leg_low + leg_range * config.OTE_FIB_HIGH
        state.ote_zone = (zone_low, zone_high)
        state.ote_direction = "bearish"
    else:
        state.ote_zone = None
        state.ote_direction = None

    return state


def price_in_ote(state: MarketState) -> bool:
    if not state.ote_zone or state.ltf_data is None or len(state.ltf_data) == 0:
        return False
    price = state.ltf_data["close"].iloc[-1]
    zone_low, zone_high = state.ote_zone
    return zone_low <= price <= zone_high


def update(state: MarketState) -> MarketState:
    return compute_ote(state)
