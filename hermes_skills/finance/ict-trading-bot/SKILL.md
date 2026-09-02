---
name: ict-trading-bot
description: Backtesten und (nur auf ausdrücklichen Wunsch) live/demo betreiben des eigenständigen ICT_FTMO_Bot-Trading-Bots.
version: 1.0.0
author: Timon Wickenhöfer
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Trading, ICT, MT5, Backtest]
    related_skills: [moni-assistant]
required_environment_variables:
  - name: ICT_BOT_DIR
    prompt: "Absoluter Pfad zum ICT_FTMO_Bot-Ordner (Checkout des timonw29/Claude-Repos)"
    help: "Beispiel: /root/moni/ICT_FTMO_Bot"
    required_for: "Alle Befehle dieser Skill"
---

# ICT-Trading-Bot

`ICT_FTMO_Bot` ist ein eigenständiges Python-Projekt (eigene
`requirements.txt`), das über die Konsole bedient wird - kein neuer Code
nötig, nur `terminal`-Aufrufe im konfigurierten `$ICT_BOT_DIR`.

**Unbedingt beachten, bevor du irgendeinen Befehl ausführst:**
- Das sind Standard-ICT-Konzepte, selbst implementiert - **keine** geprüfte,
  garantiert profitable Strategie.
- `main.py` (Live-Loop) handelt **vollautonom, ohne Rückfrage pro Trade**,
  sobald es läuft. Starte es nur auf ausdrücklichen, expliziten Wunsch des
  Nutzers - nie proaktiv, nie "weil es gerade passen würde".
- Das offizielle `MetaTrader5`-Python-Paket läuft nur mit einem echten,
  laufenden MT5-Terminal - offiziell nur unter Windows. Läuft `$ICT_BOT_DIR`
  auf einem Linux-Host ohne MT5-Terminal, beendet sich `main.py` sofort mit
  einem klaren Fehler - das ist erwartet, kein Bug.
- Ohne `ALLOW_LIVE_TRADING=true` in der `.env` von `$ICT_BOT_DIR` verweigert
  `mt5_connector.py` jede Verbindung zu einem Nicht-Demo-Konto.

## Quick Reference

| Wofür | Befehl (im Verzeichnis `$ICT_BOT_DIR` ausführen) |
| --- | --- |
| Backtest gegen historische CSV-Daten (kein echtes Konto) | `python3 backtest_engine.py --symbol EURUSD --htf-csv <pfad> --ltf-csv <pfad> --balance 10000` |
| Backtest mit Trade-Export | `... --trades-csv out/trades.csv` |
| Live-/Demo-Loop starten | `python3 main.py` (nur auf expliziten Wunsch, siehe oben!) |
| Live-Loop stoppen | Prozess beenden (z. B. `pkill -f "python3 main.py"`, oder Strg+C im Vordergrund) |

## Verfahren

1. Backtest immer zuerst - nie main.py starten, ohne dass zuvor
   mindestens ein Backtest mit dem Nutzer besprochen wurde.
2. Backtest-Report (Trefferquote, Profit-Faktor, Ø R-Multiple, max.
   Drawdown) dem Nutzer klar zusammenfassen, bevor du irgendetwas Weiteres
   vorschlägst.
3. `main.py` nur nach explizitem "Ja, starte den Live-/Demo-Bot" o. ä.
   ausführen - vorher noch einmal mündlich bestätigen lassen, dass es sich
   um ein Demokonto handelt (siehe `$ICT_BOT_DIR/.env`).
4. Volle Details zu Architektur und bekannten Grenzen stehen in
   `$ICT_BOT_DIR/README.md` - bei Unklarheiten dort nachlesen, statt zu
   raten.
