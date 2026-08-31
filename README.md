# Moni

Moni ist ein persönlicher CLI-Assistent, der ausschließlich über die Claude API
läuft (kein n8n, keine anderen Dienste). Gedacht als Testversion für ein
"Jarvis"-ähnliches Setup - Chat, einfache Automatisierung (Shell/Dateien,
Websuche) und optional Sprachein-/ausgabe.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # trage deinen ANTHROPIC_API_KEY ein
export $(cat .env | xargs)   # oder eine .env-Ladehilfe deiner Wahl
```

Für den Sprachmodus zusätzlich:

```bash
pip install SpeechRecognition pyttsx3 PyAudio
```

`PyAudio` braucht auf manchen Systemen zuerst `portaudio` (z. B. `brew install
portaudio` auf macOS, `apt install portaudio19-dev` auf Debian/Ubuntu).

## Nutzung

```bash
python -m moni              # Text-Chat
python -m moni --voice      # Sprachmodus (braucht Mikrofon/Lautsprecher)
python -m moni --yes        # Shell-/Datei-Aktionen ohne Rückfrage erlauben
python -m moni --reset      # gespeicherten Verlauf löschen
```

Befehle im Chat: `exit` beendet, `reset` löscht den Verlauf.

## Was Moni kann

- **Chat**: normale Unterhaltung über die Claude API (`claude-opus-5` als
  Standardmodell, überschreibbar via `MONI_MODEL`).
- **Automatisierung**: Moni kann Shell-Befehle ausführen, Dateien lesen/
  schreiben/auflisten und im Web suchen. Shell-Befehle und Schreibzugriffe
  fragen standardmäßig vor Ausführung nach (außer mit `--yes`).
- **Gedächtnis**: der Gesprächsverlauf wird in `~/.moni/history.json`
  gespeichert und beim nächsten Start wieder geladen.
- **Voice** (optional): Spracheingabe über das Mikrofon (Google
  Web-Speech-API, kostenlos, braucht Internet) und Sprachausgabe offline über
  `pyttsx3`. Funktioniert nur lokal auf einem Rechner mit Mikrofon/
  Lautsprecher - nicht in einer Remote-/Sandbox-Umgebung.

## Architektur

```
moni/
  cli.py      - Chat-Loop, Argumente
  agent.py    - Claude-API-Aufrufe inkl. Tool-Use-Loop
  tools.py    - Tool-Definitionen + Ausführung (Shell, Dateien, Websuche)
  memory.py   - Persistenter Gesprächsverlauf
  voice.py    - Optionale Sprachein-/ausgabe
  config.py   - Modell, Systemprompt, Einstellungen
```

## Nächste Schritte

Das hier ist bewusst ein schlankes Test-Setup. Wenn es sich bewährt, lässt es
sich später um weitere Tools erweitern (Kalender, Mail, Smart-Home-APIs etc.)
oder parallel als n8n-Workflow weiterbauen, wie beim ursprünglichen
Jarvis-Setup.
