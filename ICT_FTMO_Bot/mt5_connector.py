"""MT5 Connector - thin wrapper around the official `MetaTrader5` Python
package.

Important, honestly stated constraint: the `MetaTrader5` package only works
where a real MetaTrader 5 terminal is installed and running - officially
Windows only (it talks to the terminal over a local IPC channel, not a
remote API). It will NOT work as-is on a headless Linux droplet. Running
this against a real account means either running it on a Windows machine/VM,
or a Wine-based terminal install - that is infrastructure you set up
separately; nothing here fakes that requirement away.

Safety gate: connect() refuses to proceed against a non-demo account unless
config.ALLOW_LIVE_TRADING is explicitly true. This is deliberate - the bot
trades fully autonomously with no per-trade confirmation, so this import-time
check is the only thing stopping an accidental live connection.
"""

import config

try:
    import MetaTrader5 as mt5

    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False


class MT5ConnectionError(RuntimeError):
    pass


class MT5Connector:
    def __init__(self):
        if not MT5_AVAILABLE:
            raise MT5ConnectionError(
                "Das MetaTrader5-Paket ist hier nicht installierbar/nutzbar "
                "(officially Windows-only, braucht ein laufendes MT5-Terminal). "
                "Für Backtests wird es nicht gebraucht - siehe backtest_engine.py."
            )
        self._connected = False

    def connect(self):
        if config.MT5_ACCOUNT_TYPE != "demo" and not config.ALLOW_LIVE_TRADING:
            raise MT5ConnectionError(
                "MT5_ACCOUNT_TYPE ist nicht 'demo' und ALLOW_LIVE_TRADING ist nicht "
                "gesetzt - Verbindung zu einem echten Konto wird verweigert. Setze "
                "ALLOW_LIVE_TRADING=true erst, wenn du das wirklich willst."
            )

        kwargs = {}
        if config.MT5_PATH:
            kwargs["path"] = config.MT5_PATH
        if not mt5.initialize(**kwargs):
            raise MT5ConnectionError(f"MT5 initialize() fehlgeschlagen: {mt5.last_error()}")

        if config.MT5_LOGIN and config.MT5_PASSWORD and config.MT5_SERVER:
            ok = mt5.login(
                int(config.MT5_LOGIN), password=config.MT5_PASSWORD, server=config.MT5_SERVER
            )
            if not ok:
                raise MT5ConnectionError(f"MT5 login() fehlgeschlagen: {mt5.last_error()}")

        self._connected = True

    def disconnect(self):
        if MT5_AVAILABLE and self._connected:
            mt5.shutdown()
            self._connected = False

    def get_rates(self, symbol: str, timeframe: str, count: int):
        import pandas as pd

        tf = getattr(mt5, f"TIMEFRAME_{timeframe}", None)
        if tf is None:
            raise ValueError(f"Unbekannte Zeiteinheit: {timeframe}")
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        if rates is None:
            raise MT5ConnectionError(f"copy_rates_from_pos({symbol}, {timeframe}) fehlgeschlagen: {mt5.last_error()}")
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        return df[["time", "open", "high", "low", "close"]]

    def get_account_info(self) -> dict:
        info = mt5.account_info()
        if info is None:
            raise MT5ConnectionError(f"account_info() fehlgeschlagen: {mt5.last_error()}")
        return info._asdict()

    def get_symbol_info(self, symbol: str) -> dict:
        info = mt5.symbol_info(symbol)
        if info is None:
            raise MT5ConnectionError(f"symbol_info({symbol}) fehlgeschlagen: {mt5.last_error()}")
        return info._asdict()

    def get_open_positions(self, symbol: str = None) -> list:
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        return [p._asdict() for p in (positions or [])]

    def place_order(self, symbol: str, direction: str, size: float, stop_loss: float, take_profit: float) -> dict:
        order_type = mt5.ORDER_TYPE_BUY if direction == "bullish" else mt5.ORDER_TYPE_SELL
        tick = mt5.symbol_info_tick(symbol)
        price = tick.ask if direction == "bullish" else tick.bid
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": size,
            "type": order_type,
            "price": price,
            "sl": stop_loss,
            "tp": take_profit,
            "deviation": 10,
            "magic": 20260901,
            "comment": "ICT_FTMO_Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        return result._asdict()

    def close_position(self, position: dict, volume: float = None) -> dict:
        direction = "bearish" if position["type"] == mt5.ORDER_TYPE_BUY else "bullish"
        order_type = mt5.ORDER_TYPE_SELL if direction == "bearish" else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(position["symbol"])
        price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position["symbol"],
            "volume": volume or position["volume"],
            "type": order_type,
            "position": position["ticket"],
            "price": price,
            "deviation": 10,
            "magic": 20260901,
            "comment": "ICT_FTMO_Bot close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        return result._asdict()

    def modify_stop_loss(self, position: dict, new_stop_loss: float) -> dict:
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position["symbol"],
            "position": position["ticket"],
            "sl": new_stop_loss,
            "tp": position["tp"],
        }
        result = mt5.order_send(request)
        return result._asdict()
