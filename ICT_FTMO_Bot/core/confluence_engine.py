"""Confluence Engine V8.6 - scores how many ICT factors line up in favor of
the higher-timeframe bias direction. This does not invent a direction of its
own; it only ever grades confluence *for* the HTF trend (classic ICT
philosophy: trade with the higher-timeframe bias, use the lower timeframe
only to time the entry). If the HTF is ranging, there's no bias to grade and
the score is 0.

Weights are configurable in principle but kept as simple constants here -
tune based on your own backtest results, not gut feel.
"""

from core.market_state import MarketState
from core.ote_engine import price_in_ote

WEIGHTS = {
    "ltf_trend_aligned": 0.15,
    "recent_bos_aligned": 0.15,
    "liquidity_sweep_aligned": 0.15,
    "discount_or_premium_aligned": 0.15,
    "in_ote_zone": 0.20,
    "unmitigated_fvg_aligned": 0.10,
    "unmitigated_order_block_aligned": 0.10,
}


def _sweep_supports_direction(sweep: dict, direction: str) -> bool:
    if not sweep:
        return False
    # A sell-side sweep (stop hunt below lows) supports a bullish reversal;
    # a buy-side sweep supports a bearish reversal.
    return (sweep["side"] == "sell_side" and direction == "bullish") or (
        sweep["side"] == "buy_side" and direction == "bearish"
    )


def _has_unmitigated(items: list, direction: str) -> bool:
    return any(i["direction"] == direction and not i["mitigated"] for i in items)


def score(state: MarketState) -> MarketState:
    direction = state.htf_trend
    notes = []

    if direction not in ("bullish", "bearish"):
        state.confluence_score = 0.0
        state.confluence_notes = ["Kein klarer HTF-Bias (ranging) - kein Setup gescort."]
        return state

    total = 0.0

    if state.ltf_trend == direction:
        total += WEIGHTS["ltf_trend_aligned"]
        notes.append("LTF-Trend bestätigt HTF-Bias.")

    if state.last_bos_direction == direction:
        total += WEIGHTS["recent_bos_aligned"]
        notes.append("Jüngster BOS in Bias-Richtung.")

    if _sweep_supports_direction(state.recent_sweep, direction):
        total += WEIGHTS["liquidity_sweep_aligned"]
        notes.append(f"Liquidity-Sweep ({state.recent_sweep['side']}) stützt {direction}.")

    zone_wanted = "discount" if direction == "bullish" else "premium"
    if state.zone == zone_wanted:
        total += WEIGHTS["discount_or_premium_aligned"]
        notes.append(f"Preis im {zone_wanted}-Bereich der Range.")

    if state.ote_direction == direction and price_in_ote(state):
        total += WEIGHTS["in_ote_zone"]
        notes.append("Preis in der OTE-Zone (61.8-79%).")

    if _has_unmitigated(state.fair_value_gaps, direction):
        total += WEIGHTS["unmitigated_fvg_aligned"]
        notes.append(f"Unmitigierter {direction}er FVG vorhanden.")

    if _has_unmitigated(state.order_blocks, direction):
        total += WEIGHTS["unmitigated_order_block_aligned"]
        notes.append(f"Unmitigierter {direction}er Order Block vorhanden.")

    state.confluence_score = round(total, 4)
    state.confluence_notes = notes
    return state


def update(state: MarketState) -> MarketState:
    return score(state)
