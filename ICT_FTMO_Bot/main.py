"""Live entry point - polls MT5 for each configured symbol, runs the full
ICT engine pipeline, manages open positions, and places new trades fully
autonomously (no chat/human confirmation per trade - by design). The only
safety net is mt5_connector's demo-only gate (config.ALLOW_LIVE_TRADING)
and risk_manager's daily-loss/drawdown/position-count limits.

Known v1 limitation, stated plainly: breakeven/partial "already done" flags
for trade_management_engine are not persisted anywhere, so a bot restart
will forget which open positions already had their stop moved to breakeven
or already took a partial. On a resumed position this can very occasionally
re-trigger a breakeven move that already happened (harmless - moving an
already-breakeven stop to the same price is a no-op) but will only ever
under-manage, never double-close a partial beyond what remaining_size on
the actual MT5 position allows. Worth fixing properly (e.g. a small local
state file keyed by position ticket) before running this unattended for
long stretches.
"""

import logging
import os
import time

import config
from core import (
    confluence_engine,
    discount_engine,
    entry_engine,
    fvg_engine,
    liquidity_engine,
    multi_timeframe_engine,
    order_block_engine,
    ote_engine,
    session_engine,
    structure_engine,
    trade_management_engine,
)
from core.market_state import MarketState
from mt5_connector import MT5Connector
from risk.risk_manager import RiskManager

POLL_SECONDS = int(os.environ.get("ICT_POLL_SECONDS", "60"))


def run_cycle(connector: MT5Connector, risk_mgr: RiskManager, symbol: str, last_candle_times: dict):
    state = MarketState(symbol=symbol)
    state = multi_timeframe_engine.update(state, connector)
    if state.ltf_data is None or len(state.ltf_data) == 0:
        return

    latest_time = state.ltf_data["time"].iloc[-1]
    if last_candle_times.get(symbol) == latest_time:
        return  # this candle was already processed - nothing new to do
    last_candle_times[symbol] = latest_time

    state = session_engine.update(state)
    state = structure_engine.update(state)
    state = liquidity_engine.update(state)
    state = fvg_engine.update(state)
    state = order_block_engine.update(state)
    state = discount_engine.update(state)
    state = ote_engine.update(state)
    state = confluence_engine.update(state)

    account = connector.get_account_info()
    balance = account["balance"]
    open_positions = connector.get_open_positions(symbol)
    risk_mgr.update_balance(balance, latest_time.date())

    current_price = float(state.ltf_data["close"].iloc[-1])
    for position in open_positions:
        pos_dict = {
            "entry": position["price_open"],
            "stop_loss": position["sl"],
            "direction": "bullish" if position["type"] == 0 else "bearish",
            "breakeven_done": False,
            "partial_done": False,
        }
        actions = trade_management_engine.evaluate(pos_dict, current_price)
        if actions.get("move_stop_to") is not None:
            connector.modify_stop_loss(position, actions["move_stop_to"])
        if actions.get("close_fraction"):
            connector.close_position(position, volume=round(position["volume"] * actions["close_fraction"], 2))

    allowed, reason = risk_mgr.can_trade(balance, len(open_positions))
    if not allowed:
        logging.info("%s: kein neuer Trade - %s", symbol, reason)
        return

    if state.in_kill_zone is None:
        return  # only look for new entries inside a kill zone window

    state = entry_engine.update(state)
    if not state.signal:
        return

    symbol_info = connector.get_symbol_info(symbol)
    pip_value_per_lot = symbol_info.get("trade_tick_value", 10.0)
    size = risk_mgr.position_size(
        balance, state.signal["entry"], state.signal["stop_loss"], pip_value_per_lot, symbol
    )
    if size <= 0:
        return

    logging.info("%s: Signal %s, Größe %.2f Lots", symbol, state.signal, size)
    connector.place_order(
        symbol, state.signal["direction"], size, state.signal["stop_loss"], state.signal["take_profit"]
    )


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    connector = MT5Connector()
    connector.connect()
    logging.info("Verbunden - Konto-Typ: %s", config.MT5_ACCOUNT_TYPE)

    account = connector.get_account_info()
    risk_mgr = RiskManager(account["balance"])
    last_candle_times = {}

    try:
        while True:
            for symbol in config.SYMBOLS:
                try:
                    run_cycle(connector, risk_mgr, symbol, last_candle_times)
                except Exception:
                    logging.exception("Fehler im Zyklus für %s", symbol)
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        logging.info("Beendet per Strg+C.")
    finally:
        connector.disconnect()


if __name__ == "__main__":
    main()
