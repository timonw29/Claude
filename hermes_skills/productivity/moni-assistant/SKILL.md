---
name: moni-assistant
description: Portfolio-Tracking, Aufgabenliste, Fortschrittsziele, Nutzer-Gedächtnis und Standort - die persönlichen Moni-Funktionen, portiert aus dem ursprünglichen Moni-Webprojekt.
version: 1.0.0
author: Timon Wickenhöfer
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Persönlich, Portfolio, Aufgaben, Gedächtnis, Moni]
    related_skills: [ict-trading-bot]
---

# Moni-Assistent

Diese Skill bündelt die persönlichen Kernfunktionen, die Moni schon als
eigenständige Web-App hatte: Portfolio-Positionen, eine Aufgabenliste,
Fortschrittsziele mit Ist-/Sollwert, dauerhaftes Nutzer-Gedächtnis und den
gemerkten Standort. Alle Skripte liegen unter `scripts/` und schreiben auf
dieselben `~/.moni/*.json`-Dateien wie das ursprüngliche Moni-Projekt -
bestehende Daten funktionieren unverändert weiter, sofern `~/.moni` auf
demselben Host verfügbar ist (z. B. per Bind-Mount, falls Hermes in einem
Container läuft).

## Wann diese Skill nutzen

Immer wenn der Nutzer beiläufig etwas über sich selbst erzählt, das
langfristig nützlich ist (Beruf, Gewohnheiten, Vorlieben), eine
Aktien-/ETF-Position erwähnt (gekauft/verkauft), eine Aufgabe nennt oder
erledigt, Fortschritt zu einem Ziel meldet, oder erwähnt, wo er wohnt.
Handle proaktiv - ohne extra nachzufragen oder anzukündigen, dass du dir
etwas merkst.

## Quick Reference

| Wofür | Befehl |
| --- | --- |
| Portfolio anzeigen | `python3 scripts/portfolio.py list` |
| Position hinzufügen | `python3 scripts/portfolio.py add "Nvidia"` |
| Position entfernen | `python3 scripts/portfolio.py remove "Nvidia"` |
| Aufgaben anzeigen | `python3 scripts/todos.py list` |
| Aufgabe hinzufügen | `python3 scripts/todos.py add "Rechnung Q3 prüfen"` |
| Aufgabe erledigen | `python3 scripts/todos.py complete "Rechnung"` |
| Aufgabe löschen | `python3 scripts/todos.py remove "Rechnung"` |
| Ziele anzeigen | `python3 scripts/goals.py list` |
| Ziel setzen/überschreiben | `python3 scripts/goals.py set "Laufen" 6 20` |
| Ziel-Fortschritt aktualisieren | `python3 scripts/goals.py update "Laufen" 8` |
| Ziel löschen | `python3 scripts/goals.py remove "Laufen"` |
| Fakt merken | `python3 scripts/profile.py remember "Beruf" "Arbeitet remote, MESZ"` |
| Gemerkte Fakten anzeigen | `python3 scripts/profile.py list` |
| Fakt vergessen | `python3 scripts/profile.py forget "MESZ"` |
| Standort merken | `python3 scripts/profile.py set-location "Regensburg"` |
| Standort abrufen | `python3 scripts/profile.py get-location` |

## Verhalten

- Bittet der Nutzer erneut um dieselbe Position/Aufgabe/Ziel mit leicht
  anderem Wortlaut, nutze eine Substring-/Case-insensitive-Übereinstimmung
  (die Skripte machen das bereits selbst) statt Duplikate anzulegen.
- `goals.py set` überschreibt ein bestehendes Ziel komplett (neuer
  Ist-/Sollwert); `goals.py update` ändert nur den Ist-Wert eines
  bestehenden Ziels.
- Nutze bereits bekannte Fakten aus `profile.py list` selbstverständlich in
  Antworten, ohne sie erst abzufragen.

## Verification

Nach jeder Änderung den passenden `list`-Befehl erneut aufrufen und das
Ergebnis kurz gegen die erwartete Änderung prüfen, bevor du dem Nutzer
bestätigst, dass es geklappt hat.
