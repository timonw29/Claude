"""Liquidity Engine V4 - finds resting liquidity (equal highs/lows and
untested swing points) above/below price, and flags when the most recent
candle just swept one of those levels (wicked through and closed back
inside - the classic ICT "liquidity raid").
"""

import config
from core.market_state import MarketState


def pip_size(symbol: str) -> float:
    symbol = symbol.upper()
    if symbol.endswith("JPY"):
        return 0.01
    if symbol.startswith("XAU") or symbol.startswith("XAG"):
        return 0.1
    return 0.0001


def _group_equal_levels(prices: list, tolerance: float) -> list:
    """Clusters nearby swing prices into single liquidity levels."""
    if not prices:
        return []
    prices = sorted(prices)
    groups = [[prices[0]]]
    for p in prices[1:]:
        if abs(p - groups[-1][-1]) <= tolerance:
            groups[-1].append(p)
        else:
            groups.append([p])
    return [sum(g) / len(g) for g in groups if len(g) >= 1]


def find_liquidity_levels(swings: list, symbol: str) -> tuple:
    tolerance = config.EQUAL_LEVEL_TOLERANCE_PIPS * pip_size(symbol)
    highs = [s.price for s in swings if s.kind == "high"]
    lows = [s.price for s in swings if s.kind == "low"]
    return _group_equal_levels(highs, tolerance), _group_equal_levels(lows, tolerance)


def detect_sweep(df, buy_side: list, sell_side: list) -> dict:
    if len(df) < 2:
        return None
    last = df.iloc[-1]
    for level in buy_side:
        if last["high"] > level and last["close"] < level:
            return {"side": "buy_side", "level": level, "time": last["time"]}
    for level in sell_side:
        if last["low"] < level and last["close"] > level:
            return {"side": "sell_side", "level": level, "time": last["time"]}
    return None


def update(state: MarketState) -> MarketState:
    buy_side, sell_side = find_liquidity_levels(state.swing_points, state.symbol)
    state.buy_side_liquidity = buy_side
    state.sell_side_liquidity = sell_side
    state.recent_sweep = detect_sweep(state.ltf_data, buy_side, sell_side)
    return state
