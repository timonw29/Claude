"""Reporter - formats backtest results as readable text and optionally
writes a CSV of individual trades for further analysis in a spreadsheet."""

import csv
import os


def format_report(symbol: str, stats: dict, starting_balance: float, ending_balance: float) -> str:
    lines = [
        f"=== Backtest-Report: {symbol} ===",
        f"Trades:            {stats['trade_count']}",
        f"Trefferquote:       {stats['win_rate']}%",
        f"Profit-Faktor:      {stats['profit_factor']}",
        f"Ø R-Multiple:       {stats['avg_r']}",
        f"Erwartungswert:     {stats['expectancy']} pro Trade",
        f"Max. Drawdown:      {stats['max_drawdown_pct']}%",
        f"Startkapital:       {starting_balance}",
        f"Endkapital:         {round(ending_balance, 2)}",
        f"Gesamt-PnL:         {stats['total_pnl']}",
    ]
    return "\n".join(lines)


def write_trades_csv(trades: list, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["symbol", "direction", "entry", "stop_loss", "take_profit", "size", "open_time", "close_time", "closed_reason", "pnl", "reason"]
        )
        for t in trades:
            writer.writerow(
                [t.symbol, t.direction, t.entry, t.stop_loss, t.take_profit, t.size, t.open_time, t.close_time, t.closed_reason, t.pnl, t.reason]
            )
