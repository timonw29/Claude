"""Risk Manager - position sizing and FTMO-style hard stops. This is the
one module that is allowed to veto a trade outright: if the daily loss limit
or the max total drawdown is breached, can_trade() returns False and nothing
else in the pipeline is allowed to open a new position, regardless of how
good the confluence score looks.
"""

import config


class RiskManager:
    def __init__(self, starting_balance: float):
        self.starting_balance = starting_balance
        self.day_start_balance = starting_balance
        self.peak_balance = starting_balance
        self.current_day = None

    def _roll_day_if_needed(self, now_date):
        if self.current_day != now_date:
            self.current_day = now_date
            self.day_start_balance = self.peak_balance  # closing equity carries over

    def update_balance(self, balance: float, now_date):
        self._roll_day_if_needed(now_date)
        self.peak_balance = max(self.peak_balance, balance)

    def daily_loss_pct(self, balance: float) -> float:
        if self.day_start_balance == 0:
            return 0.0
        return (self.day_start_balance - balance) / self.day_start_balance * 100

    def total_drawdown_pct(self, balance: float) -> float:
        if self.peak_balance == 0:
            return 0.0
        return (self.peak_balance - balance) / self.peak_balance * 100

    def can_trade(self, balance: float, open_position_count: int) -> tuple:
        """Returns (allowed: bool, reason: str)."""
        if self.daily_loss_pct(balance) >= config.MAX_DAILY_LOSS_PCT:
            return False, f"Tageslimit erreicht ({self.daily_loss_pct(balance):.2f}%)."
        if self.total_drawdown_pct(balance) >= config.MAX_TOTAL_DRAWDOWN_PCT:
            return False, f"Max. Drawdown erreicht ({self.total_drawdown_pct(balance):.2f}%)."
        if open_position_count >= config.MAX_OPEN_POSITIONS:
            return False, f"Max. offene Positionen erreicht ({open_position_count})."
        return True, ""

    def position_size(
        self, balance: float, entry: float, stop_loss: float, pip_value_per_lot: float, symbol: str
    ) -> float:
        """Lots sized so that a stop-out loses exactly RISK_PER_TRADE_PCT of
        balance. pip_value_per_lot is the account-currency value of one pip
        move for one standard lot of the traded symbol (broker-specific -
        pass it in from mt5_connector's symbol info, never hardcode it)."""
        from core.liquidity_engine import pip_size

        risk_amount = balance * (config.RISK_PER_TRADE_PCT / 100)
        stop_distance = abs(entry - stop_loss)
        if stop_distance <= 0 or pip_value_per_lot <= 0:
            return 0.0
        pips_at_risk = stop_distance / pip_size(symbol)
        lots = risk_amount / (pips_at_risk * pip_value_per_lot)
        return round(max(lots, 0.0), 2)
