"""Structure Engine V4.1 - fractal swing-point detection, trend
classification, and Break of Structure (BOS) / Change of Character (CHoCH)
detection.

A swing high/low is a simple `lookback`-bar fractal: bar i is a swing high
if its high is the max within [i-lookback, i+lookback], and a swing low if
its low is the min within that same window. Trend is read off the last two
confirmed highs/lows: higher-high + higher-low => bullish, lower-high +
lower-low => bearish, anything else => ranging.

BOS = price closes beyond the last swing point *in the direction of* the
current trend (continuation). CHoCH = price closes beyond the last swing
point *against* the current trend (first sign of a possible reversal).
"""

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

import config
from core.market_state import MarketState, SwingPoint


def detect_swings(df, lookback: int = None) -> list:
    """Vectorized fractal detection. This runs once per bar in a backtest,
    so a plain Python loop doing pandas .iloc slicing per index (the
    straightforward way to write this) makes a multi-thousand-bar backtest
    scale quadratically and crawl - rolling max/min via numpy's
    sliding_window_view does the same O(window) comparison in C instead."""
    lookback = lookback or config.SWING_LOOKBACK
    window = 2 * lookback + 1
    n = len(df)
    if n < window:
        return []

    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    times = df["time"].to_numpy()

    rolling_max = sliding_window_view(highs, window).max(axis=1)
    rolling_min = sliding_window_view(lows, window).min(axis=1)

    swings = []
    for k in range(len(rolling_max)):
        i = k + lookback
        if highs[i] == rolling_max[k]:
            swings.append(SwingPoint(index=i, time=times[i], price=float(highs[i]), kind="high"))
        elif lows[i] == rolling_min[k]:
            swings.append(SwingPoint(index=i, time=times[i], price=float(lows[i]), kind="low"))
    return swings


def classify_trend(swings: list) -> str:
    highs = [s for s in swings if s.kind == "high"]
    lows = [s for s in swings if s.kind == "low"]
    if len(highs) < 2 or len(lows) < 2:
        return "ranging"

    higher_high = highs[-1].price > highs[-2].price
    higher_low = lows[-1].price > lows[-2].price
    lower_high = highs[-1].price < highs[-2].price
    lower_low = lows[-1].price < lows[-2].price

    if higher_high and higher_low:
        return "bullish"
    if lower_high and lower_low:
        return "bearish"
    return "ranging"


def detect_break(df, swings: list, trend: str):
    """Returns ("bos" | "choch", direction) if the latest close breaks the
    most recent relevant swing point, else (None, None)."""
    if not swings:
        return None, None

    last_close = df["close"].iloc[-1]
    last_high = next((s for s in reversed(swings) if s.kind == "high"), None)
    last_low = next((s for s in reversed(swings) if s.kind == "low"), None)

    broke_up = last_high is not None and last_close > last_high.price
    broke_down = last_low is not None and last_close < last_low.price

    if broke_up and trend in ("bullish", "ranging"):
        return "bos" if trend == "bullish" else "choch", "bullish"
    if broke_up and trend == "bearish":
        return "choch", "bullish"
    if broke_down and trend in ("bearish", "ranging"):
        return "bos" if trend == "bearish" else "choch", "bearish"
    if broke_down and trend == "bullish":
        return "choch", "bearish"
    return None, None


def update(state: MarketState) -> MarketState:
    htf_swings = detect_swings(state.htf_data)
    state.htf_trend = classify_trend(htf_swings)

    ltf_swings = detect_swings(state.ltf_data)
    state.ltf_trend = classify_trend(ltf_swings)
    state.swing_points = ltf_swings

    kind, direction = detect_break(state.ltf_data, ltf_swings, state.ltf_trend)
    if kind == "bos":
        state.last_bos_direction = direction
    elif kind == "choch":
        state.last_choch_direction = direction

    return state
