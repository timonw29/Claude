"""Statistics - turns a list of closed Trade objects into the numbers people
actually judge a strategy by: win rate, profit factor, average R, max
drawdown on the equity curve, and expectancy."""


def compute(trades: list, starting_balance: float) -> dict:
    if not trades:
        return {
            "trade_count": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "total_pnl": 0.0,
            "avg_r": 0.0,
            "max_drawdown_pct": 0.0,
            "expectancy": 0.0,
        }

    wins = [t for t in trades if (t.pnl or 0) > 0]
    losses = [t for t in trades if (t.pnl or 0) <= 0]

    gross_profit = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in losses))
    total_pnl = sum(t.pnl for t in trades)

    r_multiples = []
    for t in trades:
        risk = abs(t.entry - t.stop_loss)
        if risk > 0 and t.pnl is not None:
            direction_pips = (t.close_price - t.entry) if t.direction == "bullish" else (t.entry - t.close_price)
            r_multiples.append(direction_pips / risk)

    equity = starting_balance
    peak = starting_balance
    max_dd = 0.0
    for t in sorted(trades, key=lambda x: x.close_time):
        equity += t.pnl or 0
        peak = max(peak, equity)
        dd = (peak - equity) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)

    win_rate = len(wins) / len(trades) * 100

    return {
        "trade_count": len(trades),
        "win_rate": round(win_rate, 2),
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss > 0 else float("inf"),
        "total_pnl": round(total_pnl, 2),
        "avg_r": round(sum(r_multiples) / len(r_multiples), 2) if r_multiples else 0.0,
        "max_drawdown_pct": round(max_dd, 2),
        "expectancy": round(total_pnl / len(trades), 2),
    }
