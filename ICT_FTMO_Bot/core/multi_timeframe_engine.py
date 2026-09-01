"""Multi-Timeframe Engine - pulls OHLC candles for a symbol on both the
higher timeframe (bias/structure) and lower timeframe (entries) and attaches
them to the MarketState. Data comes from mt5_connector; in backtests the
simulator fills htf_data/ltf_data directly from historical CSVs instead of
calling this engine.
"""

import config
from mt5_connector import MT5Connector
from core.market_state import MarketState


def update(state: MarketState, connector: MT5Connector) -> MarketState:
    state.htf_data = connector.get_rates(state.symbol, config.HTF, config.BARS_TO_FETCH)
    state.ltf_data = connector.get_rates(state.symbol, config.LTF, config.BARS_TO_FETCH)
    return state
