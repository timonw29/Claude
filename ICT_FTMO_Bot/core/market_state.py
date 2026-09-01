"""MarketState V2 - the shared per-symbol state object every engine reads
from and writes to. Each engine takes the current MarketState, updates its
own section, and returns it - main.py threads one instance per symbol
through the whole engine pipeline each cycle.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SwingPoint:
    index: int
    time: datetime
    price: float
    kind: str  # "high" or "low"


@dataclass
class MarketState:
    symbol: str

    # multi_timeframe_engine
    htf_data: Optional[object] = None  # pandas.DataFrame, higher timeframe OHLC
    ltf_data: Optional[object] = None  # pandas.DataFrame, lower timeframe OHLC

    # session_engine
    active_session: Optional[str] = None
    in_kill_zone: Optional[str] = None

    # structure_engine
    htf_trend: str = "ranging"  # "bullish" | "bearish" | "ranging"
    ltf_trend: str = "ranging"
    swing_points: list = field(default_factory=list)
    last_bos_direction: Optional[str] = None
    last_choch_direction: Optional[str] = None

    # liquidity_engine
    buy_side_liquidity: list = field(default_factory=list)   # levels above price
    sell_side_liquidity: list = field(default_factory=list)  # levels below price
    recent_sweep: Optional[dict] = None

    # fvg_engine
    fair_value_gaps: list = field(default_factory=list)

    # order_block_engine
    order_blocks: list = field(default_factory=list)

    # discount_engine
    dealing_range_high: Optional[float] = None
    dealing_range_low: Optional[float] = None
    zone: Optional[str] = None  # "discount" | "premium" | "equilibrium"

    # ote_engine
    ote_zone: Optional[tuple] = None  # (low_price, high_price) of the 61.8-79% zone
    ote_direction: Optional[str] = None

    # confluence_engine
    confluence_score: float = 0.0
    confluence_notes: list = field(default_factory=list)

    # entry_engine
    signal: Optional[dict] = None  # {"direction", "entry", "stop_loss", "take_profit", "reason"}

    updated_at: Optional[datetime] = None
