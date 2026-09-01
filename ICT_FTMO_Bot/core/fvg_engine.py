"""FVG Engine V3.5 - detects Fair Value Gaps (a 3-candle imbalance: candle 1
and candle 3 don't overlap, leaving a gap candle 2 displaced through).
Bullish FVG: candle1.high < candle3.low. Bearish FVG: candle1.low > candle3.high.
Each gap is tracked until price trades back into it ("mitigated").
"""

from core.market_state import MarketState


def detect_fvgs(df) -> list:
    gaps = []
    n = len(df)
    for i in range(2, n):
        c1, c3 = df.iloc[i - 2], df.iloc[i]
        if c1["high"] < c3["low"]:
            gaps.append(
                {
                    "direction": "bullish",
                    "top": c3["low"],
                    "bottom": c1["high"],
                    "time": df["time"].iloc[i],
                    "mitigated": False,
                }
            )
        elif c1["low"] > c3["high"]:
            gaps.append(
                {
                    "direction": "bearish",
                    "top": c1["low"],
                    "bottom": c3["high"],
                    "time": df["time"].iloc[i],
                    "mitigated": False,
                }
            )
    return gaps


def mark_mitigated(gaps: list, df) -> list:
    if not gaps or df is None or len(df) == 0:
        return gaps
    last = df.iloc[-1]
    for gap in gaps:
        if gap["mitigated"]:
            continue
        if gap["bottom"] <= last["close"] <= gap["top"]:
            gap["mitigated"] = True
    return gaps


def update(state: MarketState) -> MarketState:
    gaps = detect_fvgs(state.ltf_data)
    state.fair_value_gaps = mark_mitigated(gaps, state.ltf_data)
    return state
