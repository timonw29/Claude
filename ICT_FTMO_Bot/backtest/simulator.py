"""Backtest simulator - walks forward bar-by-bar through historical LTF data
(only ever looking at data up to "now", never ahead, to avoid look-ahead
bias), runs the exact same engine pipeline main.py uses live, and tracks
simulated trades through open/manage/close.

Each cycle's engine pipeline only sees the trailing config.BARS_TO_FETCH bars
(same as main.py's live get_rates() call) rather than the entire history to
date - both for parity with live behavior (main.py never has more than that
many bars to look at either) and because re-running swing/liquidity/order-
block detection over an ever-growing window would make a multi-thousand-bar
backtest scale quadratically and become impractically slow.

Caveat, stated plainly: pip_value_per_lot is a placeholder (10 units of
account currency per pip per standard lot), which is only roughly correct
for USD-quoted majors on a USD account. For anything else - JPY pairs,
metals, a non-USD account currency - pull the real contract specs from your
broker (mt5_connector.get_symbol_info) before trusting these numbers.
"""

import config
from backtest.trade import Trade
from core import (
    confluence_engine,
    discount_engine,
    entry_engine,
    fvg_engine,
    liquidity_engine,
    order_block_engine,
    ote_engine,
    session_engine,
    structure_engine,
    trade_management_engine,
)
from core.liquidity_engine import pip_size as get_pip_size
from core.market_state import MarketState
from risk.risk_manager import RiskManager

PLACEHOLDER_PIP_VALUE_PER_LOT = 10.0


def _check_sl_tp(trade: Trade, last_candle) -> dict:
    if trade.direction == "bullish":
        if last_candle["low"] <= trade.stop_loss:
            return {"price": trade.stop_loss, "reason": "stop_loss"}
        if last_candle["high"] >= trade.take_profit:
            return {"price": trade.take_profit, "reason": "take_profit"}
    else:
        if last_candle["high"] >= trade.stop_loss:
            return {"price": trade.stop_loss, "reason": "stop_loss"}
        if last_candle["low"] <= trade.take_profit:
            return {"price": trade.take_profit, "reason": "take_profit"}
    return None


def run_backtest(htf_df, ltf_df, symbol: str, starting_balance: float):
    """Returns (closed_trades: list[Trade], ending_balance: float)."""
    risk_mgr = RiskManager(starting_balance)
    balance = starting_balance
    open_trades = []
    closed_trades = []
    pip_size = get_pip_size(symbol)

    min_bars = config.SWING_LOOKBACK * 2 + 5
    for i in range(min_bars, len(ltf_df)):
        now_time = ltf_df["time"].iloc[i]
        ltf_start = max(0, i + 1 - config.BARS_TO_FETCH)
        ltf_window = ltf_df.iloc[ltf_start : i + 1].reset_index(drop=True)
        htf_window = htf_df[htf_df["time"] <= now_time].tail(config.BARS_TO_FETCH).reset_index(drop=True)
        if len(htf_window) < min_bars:
            continue

        state = MarketState(symbol=symbol)
        state.htf_data = htf_window
        state.ltf_data = ltf_window

        state = session_engine.update(state, now=now_time)
        state = structure_engine.update(state)
        state = liquidity_engine.update(state)
        state = fvg_engine.update(state)
        state = order_block_engine.update(state)
        state = discount_engine.update(state)
        state = ote_engine.update(state)
        state = confluence_engine.update(state)

        last_candle = ltf_window.iloc[-1]
        current_price = float(last_candle["close"])

        still_open = []
        for trade in open_trades:
            hit = _check_sl_tp(trade, last_candle)
            if hit:
                before = trade.realized_pnl
                trade.close(hit["price"], now_time, hit["reason"], PLACEHOLDER_PIP_VALUE_PER_LOT, pip_size)
                balance += trade.pnl - before  # only the final leg - partials were already added
                closed_trades.append(trade)
                continue

            actions = trade_management_engine.evaluate(trade.as_position_dict(), current_price)
            if actions.get("close_fraction"):
                before = trade.realized_pnl
                trade.close_partial(current_price, actions["close_fraction"], PLACEHOLDER_PIP_VALUE_PER_LOT, pip_size)
                balance += trade.realized_pnl - before
                trade.partial_done = True
            if actions.get("move_stop_to") is not None:
                trade.stop_loss = actions["move_stop_to"]
                trade.breakeven_done = True
            still_open.append(trade)
        open_trades = still_open

        risk_mgr.update_balance(balance, now_time.date())
        allowed, _ = risk_mgr.can_trade(balance, len(open_trades))
        if allowed:
            state = entry_engine.update(state)
            if state.signal:
                size = risk_mgr.position_size(
                    balance, state.signal["entry"], state.signal["stop_loss"], PLACEHOLDER_PIP_VALUE_PER_LOT, symbol
                )
                if size > 0:
                    open_trades.append(
                        Trade(
                            symbol=symbol,
                            direction=state.signal["direction"],
                            entry=state.signal["entry"],
                            stop_loss=state.signal["stop_loss"],
                            take_profit=state.signal["take_profit"],
                            size=size,
                            open_time=now_time,
                            reason=state.signal["reason"],
                        )
                    )

    # Force-close anything still open at the last available price so stats
    # reflect a complete, closed book rather than silently dropping trades.
    if len(ltf_df) > 0:
        last_time = ltf_df["time"].iloc[-1]
        last_price = float(ltf_df["close"].iloc[-1])
        for trade in open_trades:
            before = trade.realized_pnl
            trade.close(last_price, last_time, "end_of_data", PLACEHOLDER_PIP_VALUE_PER_LOT, pip_size)
            balance += trade.pnl - before
            closed_trades.append(trade)

    return closed_trades, balance
