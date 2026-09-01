"""Backtest CLI entry point - run the full ICT engine pipeline against
historical CSV data (no MT5 connection needed, no live/demo account risk at
all). This is the step to run, and re-run, and tune, before main.py ever
touches a real MT5 connection.

CSV format expected for both files: columns time,open,high,low,close
(time as anything pandas.to_datetime can parse, UTC).

Usage:
    python backtest_engine.py --symbol EURUSD --htf-csv data/EURUSD_H4.csv \\
        --ltf-csv data/EURUSD_M15.csv --balance 10000
"""

import argparse
import sys

import pandas as pd

from backtest import reporter, statistics
from backtest.simulator import run_backtest


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.sort_values("time").reset_index(drop=True)
    required = {"time", "open", "high", "low", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} fehlen Spalten: {sorted(missing)}")
    return df


def main():
    parser = argparse.ArgumentParser(description="ICT/FTMO Bot - Backtest")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--htf-csv", required=True, help="Höhere Zeiteinheit (Bias/Struktur), z. B. H4")
    parser.add_argument("--ltf-csv", required=True, help="Niedrigere Zeiteinheit (Einstieg), z. B. M15")
    parser.add_argument("--balance", type=float, default=10000.0)
    parser.add_argument("--trades-csv", default=None, help="Optional: Einzeltrades als CSV schreiben")
    args = parser.parse_args()

    try:
        htf_df = load_csv(args.htf_csv)
        ltf_df = load_csv(args.ltf_csv)
    except (OSError, ValueError) as e:
        print(f"Fehler beim Laden der Daten: {e}", file=sys.stderr)
        sys.exit(1)

    trades, ending_balance = run_backtest(htf_df, ltf_df, args.symbol, args.balance)
    stats = statistics.compute(trades, args.balance)
    print(reporter.format_report(args.symbol, stats, args.balance, ending_balance))

    if args.trades_csv:
        reporter.write_trades_csv(trades, args.trades_csv)
        print(f"\nEinzeltrades geschrieben nach: {args.trades_csv}")


if __name__ == "__main__":
    main()
