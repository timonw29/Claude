# ICT_FTMO_Bot

Ein regelbasierter Trading-Bot nach gängigen ICT-Konzepten (Market
Structure, Liquidity, Fair Value Gaps, Order Blocks, Discount/Premium,
Optimal Trade Entry, Confluence-Scoring) mit einem eigenen Backtest-Framework
und einer MT5-Anbindung. Läuft als eigenständiger Prozess, den Moni startet/
stoppt/überwacht (siehe `moni/trading_bot.py` im Hauptrepo).

**Wichtiger Haftungshinweis, unmissverständlich:** Das hier sind Standard-
ICT-Konzepte nach gängigen, öffentlich bekannten Definitionen - **keine**
geprüfte, garantiert profitable Strategie, kein Ersatz für eigene Recherche,
und keine Finanzberatung. Jede Konfiguration (Confluence-Schwelle, Risiko pro
Trade, Symbole, Zeiteinheiten) ist ein Startpunkt zum Testen, kein fertiges
Ergebnis. Erst ausgiebig backtesten, dann auf einem Demokonto laufen lassen,
bevor auch nur in Erwägung gezogen wird, ein echtes/FTMO-Konto anzubinden.

## Setup

```bash
cd ICT_FTMO_Bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 1. Erst backtesten (kein MT5 nötig)

Historische Kerzendaten als CSV besorgen (Spalten: `time,open,high,low,close`)
- z. B. Export aus MT5 selbst, oder ein Anbieter wie Dukascopy/HistData.
Zwei Dateien pro Symbol: eine für die höhere Zeiteinheit (Bias/Struktur,
Standard `H4`), eine für die niedrigere (Einstieg, Standard `M15`).

```bash
python backtest_engine.py --symbol EURUSD \
  --htf-csv data/EURUSD_H4.csv --ltf-csv data/EURUSD_M15.csv \
  --balance 10000 --trades-csv out/eurusd_trades.csv
```

Ausgabe: Trefferquote, Profit-Faktor, Ø R-Multiple, max. Drawdown,
Erwartungswert pro Trade. **Erst wenn diese Zahlen über genug Trades und
mehrere Marktphasen hinweg überzeugen**, lohnt sich der nächste Schritt.

## 2. Gegen ein MT5-Demokonto laufen lassen

`MT5_ACCOUNT_TYPE=demo` (Standard in `.env.example`) und die MT5-Zugangsdaten
eines **Demokontos** eintragen, dann:

```bash
python main.py
```

**Wichtige technische Einschränkung, offen gesagt:** Das offizielle
`MetaTrader5`-Python-Paket funktioniert nur mit einem laufenden echten
MT5-Terminal - offiziell nur unter Windows. Auf einem headless Linux-Server
(wie eurem DigitalOcean-Droplet) läuft das nicht ohne Weiteres; dafür braucht
es entweder eine Windows-Maschine/VM oder einen Wine-basierten
MT5-Terminal-Aufbau. Das ist eigene Infrastruktur, die hier nicht mit
abgedeckt ist.

## 3. Echtes/FTMO-Konto

Nur wenn Backtest UND Demo-Betrieb über längere Zeit überzeugen: in `.env`
`MT5_ACCOUNT_TYPE=live` **und** `ALLOW_LIVE_TRADING=true` setzen. Ohne
beides zusammen verweigert `mt5_connector.py` die Verbindung - das ist
bewusst so, weil der Bot vollautonom handelt (keine Bestätigung pro Trade).

## Architektur

```
main.py                     Live-Loop (autonom, keine Rückfrage pro Trade)
backtest_engine.py          CLI für Backtests gegen CSV-Daten
config.py                   Alle Parameter (Risiko, Symbole, Zeiteinheiten, ...)
mt5_connector.py            MT5-Anbindung + Demo/Live-Sicherheitssperre

core/
  market_state.py           Gemeinsamer Zustand pro Symbol, den alle Engines lesen/schreiben
  multi_timeframe_engine.py Holt HTF-/LTF-Kerzen
  structure_engine.py       Swing-Points, Trend, BOS/CHoCH
  session_engine.py         Session/Kill-Zone-Erkennung (UTC)
  liquidity_engine.py       Equal Highs/Lows, Liquidity Sweeps
  fvg_engine.py              Fair Value Gaps + Mitigation
  order_block_engine.py     Order Blocks + Mitigation
  discount_engine.py        Discount/Premium-Zone der Dealing Range
  ote_engine.py              Optimal-Trade-Entry-Zone (61.8-79% Fib)
  confluence_engine.py      Gewichteter Score aus allen obigen Faktoren
  entry_engine.py            Konkretes Signal (Entry/SL/TP), wenn Score + RR reichen
  trade_management_engine.py Breakeven/Teil-Gewinnmitnahme für offene Trades

risk/risk_manager.py        Positionsgrößen + FTMO-Style Tages-/Gesamt-Drawdown-Sperre

backtest/
  trade.py                  Trade-Objekt (auch für main.py's Live-Positions-Shape)
  simulator.py               Bar-für-Bar-Simulation über die echte Engine-Pipeline
  statistics.py               Kennzahlen aus geschlossenen Trades
  reporter.py                 Text-/CSV-Ausgabe
```

## Bekannte Grenzen (Stand v1)

- Breakeven-/Partial-Status offener Positionen wird nicht persistiert - ein
  Neustart von `main.py` "vergisst", welche offenen Positionen das schon
  hatten (siehe Kommentar oben in `main.py`).
- `pip_value_per_lot` im Backtest ist ein Platzhalter (10 Einheiten
  Kontowährung pro Pip und Standardlot) - für echte Ergebnisse die realen
  Kontraktspezifikationen des eigenen Brokers eintragen.
- Kill-Zone-Fenster und Session-Zeiten sind Standard-UTC-Fenster, keine
  brokerspezifische Server-Zeit-Umrechnung.
- **Backtest-Performance:** Der Simulator ruft die komplette Engine-Pipeline
  für jede einzelne LTF-Kerze neu auf (wie main.py es live auch täte) - bei
  ~600 M15-Kerzen dauert ein Durchlauf schon eine knappe halbe Minute auf
  gewöhnlicher CPU. Für einen Backtest über mehrere Monate/Jahre (Zehntausende
  Kerzen) plane entsprechend mehrere Minuten bis Stunden Laufzeit ein, oder
  grenze den CSV-Zeitraum bewusst auf das ein, was du gerade wirklich testen
  willst. `structure_engine.detect_swings` ist bereits numpy-vektorisiert;
  `liquidity_engine`, `fvg_engine` und `order_block_engine` sind es (noch)
  nicht - lohnende nächste Stellschraube, falls die Laufzeit zum Problem wird.
