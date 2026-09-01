"""Trade - a single simulated position, from signal to close. Shares the
entry/stop_loss/take_profit/direction shape that trade_management_engine
expects, so the same management rules apply in backtest and live."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Trade:
    symbol: str
    direction: str  # "bullish" | "bearish"
    entry: float
    stop_loss: float
    take_profit: float
    size: float
    open_time: datetime
    reason: str = ""

    close_time: Optional[datetime] = None
    close_price: Optional[float] = None
    pnl: Optional[float] = None
    closed_reason: Optional[str] = None  # "stop_loss" | "take_profit" | "partial" | "manual"

    breakeven_done: bool = False
    partial_done: bool = False
    remaining_size: float = field(default=None)  # set to size in __post_init__
    realized_pnl: float = 0.0  # accumulates partial closes; final close adds the rest

    def __post_init__(self):
        if self.remaining_size is None:
            self.remaining_size = self.size

    def as_position_dict(self) -> dict:
        """Shape expected by trade_management_engine.evaluate()."""
        return {
            "entry": self.entry,
            "stop_loss": self.stop_loss,
            "direction": self.direction,
            "breakeven_done": self.breakeven_done,
            "partial_done": self.partial_done,
        }

    def is_open(self) -> bool:
        return self.close_time is None

    def _leg_pnl(self, price: float, size: float, pip_value_per_lot: float, pip_size: float) -> float:
        pips = (price - self.entry) if self.direction == "bullish" else (self.entry - price)
        pips /= pip_size
        return pips * pip_value_per_lot * size

    def close_partial(self, price: float, fraction: float, pip_value_per_lot: float, pip_size: float):
        partial_size = self.remaining_size * fraction
        self.realized_pnl += self._leg_pnl(price, partial_size, pip_value_per_lot, pip_size)
        self.remaining_size -= partial_size

    def close(self, price: float, time: datetime, reason: str, pip_value_per_lot: float, pip_size: float):
        self.realized_pnl += self._leg_pnl(price, self.remaining_size, pip_value_per_lot, pip_size)
        self.pnl = self.realized_pnl
        self.close_price = price
        self.close_time = time
        self.closed_reason = reason
        self.remaining_size = 0.0
