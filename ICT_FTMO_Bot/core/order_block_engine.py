"""Order Block Engine V2.2 - the last opposing candle before a displacement
move that breaks structure. Bullish OB: the last bearish (down-close) candle
right before an impulsive up-move that produces a BOS/CHoCH up. Bearish OB:
the last bullish candle before an impulsive down-move / BOS down.

Mitigation: an order block is considered tapped once price trades back into
its candle range.
"""

import config
from core.market_state import MarketState


def _is_bearish(candle) -> bool:
    return candle["close"] < candle["open"]


def _is_bullish(candle) -> bool:
    return candle["close"] > candle["open"]


def find_order_blocks(df, swings: list) -> list:
    blocks = []
    swing_by_index = {s.index: s for s in swings}

    for idx, swing in swing_by_index.items():
        if idx < 1 or idx + config.SWING_LOOKBACK >= len(df):
            continue
        move_end = min(idx + config.SWING_LOOKBACK + 2, len(df) - 1)
        displacement = df["close"].iloc[move_end] - df["close"].iloc[idx]

        if swing.kind == "low" and displacement > 0:
            # bullish move off this low - look back for the last down candle
            for j in range(idx, max(idx - 5, -1), -1):
                if _is_bearish(df.iloc[j]):
                    blocks.append(
                        {
                            "direction": "bullish",
                            "top": df["high"].iloc[j],
                            "bottom": df["low"].iloc[j],
                            "time": df["time"].iloc[j],
                            "mitigated": False,
                        }
                    )
                    break
        elif swing.kind == "high" and displacement < 0:
            # bearish move off this high - look back for the last up candle
            for j in range(idx, max(idx - 5, -1), -1):
                if _is_bullish(df.iloc[j]):
                    blocks.append(
                        {
                            "direction": "bearish",
                            "top": df["high"].iloc[j],
                            "bottom": df["low"].iloc[j],
                            "time": df["time"].iloc[j],
                            "mitigated": False,
                        }
                    )
                    break

    return blocks


def mark_mitigated(blocks: list, df) -> list:
    if not blocks or df is None or len(df) == 0:
        return blocks
    last_close = df["close"].iloc[-1]
    for block in blocks:
        if block["bottom"] <= last_close <= block["top"]:
            block["mitigated"] = True
    return blocks


def update(state: MarketState) -> MarketState:
    blocks = find_order_blocks(state.ltf_data, state.swing_points)
    state.order_blocks = mark_mitigated(blocks, state.ltf_data)
    return state
