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

## Web-Modus (Browser-Chat mit Login)

Für den dauerhaften Zugriff vom Handy/iPad aus gibt es `moni.web`: eine
passwortgeschützte Weboberfläche, die denselben Agenten-Kern nutzt. Shell-
Befehle und Schreibzugriffe zeigen dabei "Erlauben/Ablehnen"-Buttons statt
einer Terminal-Rückfrage.

```bash
export MONI_WEB_PASSWORD='ein-starkes-passwort'
export ANTHROPIC_API_KEY='...'
uvicorn moni.web:app --host 0.0.0.0 --port 8010
```

Danach im Browser: `http://<server>:8010` (bzw. hinter Reverse-Proxy die
eigene Domain).

**Wichtig, weil Moni echte Shell-Befehle ausführen kann:**
- Starkes, einzigartiges Passwort in `MONI_WEB_PASSWORD` setzen.
- Immer hinter HTTPS betreiben (Reverse-Proxy übernimmt das, siehe unten) -
  ohne TLS geht das Passwort/Session-Cookie im Klartext übers Netz.
- Login sperrt sich nach 5 Fehlversuchen für 15 Minuten (einfacher
  Brute-Force-Schutz, `moni/web.py`).

### Portfolio-Tracking & tägliches Briefing

Moni führt eine einfache Liste deiner Aktien-/ETF-Positionen (gespeichert in
`~/.moni/portfolio.json` im Container). Du pflegst sie per Chat - einfach
erwähnen, was du gekauft/verkauft hast, z. B. "Ich habe heute 10 Aktien
Nvidia gekauft" oder "Ich hab meine Coca-Cola-Position verkauft". Moni ruft
dafür selbstständig `add_portfolio_position` / `remove_portfolio_position`
auf. Zum Ansehen: einfach fragen, was aktuell im Depot ist.

Jeden Tag um `MONI_BRIEFING_TIME` (Standard `07:00`, Zeitzone
`MONI_BRIEFING_TIMEZONE`, Standard `Europe/Berlin`) erstellt Moni automatisch
ein kurzes Briefing zu den wichtigsten Börsenindizes und den Kursen der
hinterlegten Positionen (per Websuche - keine Börsen-API nötig) und legt es
in den Gesprächsverlauf, sichtbar beim nächsten Öffnen der Seite. Dieser
automatische Lauf nutzt bewusst nur ungefährliche Tools (Websuche,
Portfolio-Liste) - nie Shell-Befehle oder Schreibzugriffe, damit nachts
nichts auf eine Bestätigung wartet, die niemand gibt.

Eine automatische Trade-Republic-Anbindung gibt es bewusst nicht: Trade
Republic hat keine offizielle Kunden-API, nur inoffizielle,
Nutzungsbedingungs-riskante Community-Tools. Für jetzt trägst du Positionen
manuell/per Chat ein.

### Deployment auf dem eigenen Server (z. B. DigitalOcean-Droplet mit n8n)

1. Repo auf den Server klonen/pullen (`git clone` bzw. `git pull` in einem
   Verzeichnis neben deinem n8n-Setup).
2. `.env` anlegen und befüllen:
   ```bash
   cp .env.example .env
   # ANTHROPIC_API_KEY und MONI_WEB_PASSWORD eintragen
   ```
3. Container bauen und starten:
   ```bash
   docker compose up -d --build
   ```
   Das startet Moni auf `127.0.0.1:8010` (siehe Kommentare in
   `docker-compose.yml` für die Variante, bei der dein Reverse-Proxy selbst
   containerisiert ist und Moni stattdessen über ein gemeinsames
   Docker-Netzwerk erreicht).
4. DNS: A-Record `moni.myjarvis-ai.de` auf die IP deines Droplets zeigen
   lassen (genau wie bei `n8n.myjarvis-ai.de`).
5. Reverse-Proxy-Eintrag ergänzen - Vorlagen liegen in `deploy/`:
   - `deploy/Caddyfile.snippet` (falls Caddy)
   - `deploy/nginx.snippet.conf` (falls nginx - danach `certbot --nginx -d
     moni.myjarvis-ai.de` für das TLS-Zertifikat)
6. Proxy neu laden (`systemctl reload caddy` bzw. `nginx -s reload`) und
   `https://moni.myjarvis-ai.de` im Browser öffnen.

## Persönlichkeit & Gedächtnis

Moni hat eine feste Persönlichkeit (höflich-direkt, trockener Humor, JARVIS-
artig) im Systemprompt (`moni/config.py`). Zusätzlich lernt sie den Nutzer
über die Zeit kennen: Wenn beiläufig etwas Dauerhaftes erwähnt wird (Beruf,
Tagesablauf, Vorlieben), merkt Moni es sich selbstständig (Tools
`remember_about_user` / `recall_about_user` / `forget_about_user`,
gespeichert in `~/.moni/profile.json`) und bezieht es in künftige Antworten
ein - ganz ohne erneutes Nachfragen.

## Sprachausgabe

Im Web-Modus liest Moni jede Chat-Antwort automatisch laut vor. Standardmäßig
über die **kostenlose Sprachausgabe des Browsers** (Web Speech API,
`speechSynthesis` in `moni/web_static/index.html`) - kein Account, kein API-
Key, läuft komplett im Browser. Klingt etwas roboterhafter als eine
Cloud-Stimme, kostet aber nichts.

Für natürlichere Stimmen gibt es optional eine **ElevenLabs**-Anbindung
(`moni/tts.py` + `POST /api/speak`), aktuell aber nicht aktiv verdrahtet im
Frontend (die Browser-Stimme hat Vorrang). ElevenLabs' kostenloser Tarif
erlaubt keine Bibliotheks-Stimmen über die API - dafür braucht es mindestens
den Starter- oder Creator-Tarif (siehe [elevenlabs.io/pricing](https://elevenlabs.io/pricing)).
Falls das später gewünscht ist: Key in `.env` eintragen und in `index.html`
die `speak()`-Funktion wieder auf einen Aufruf von `/api/speak` umstellen
statt `speechSynthesis`.

## Dashboard

Im Web-Modus gibt es zwei Tabs: **Dashboard** (3-Spalten-HUD, nah am
Referenzbild - links Status/Fähigkeiten, Mitte die große 3D-Kugel mit
"MONI"-Schriftzug und Sockel, rechts Wetter/Kalender/Briefing/Pins; auf
schmalen Bildschirmen stapeln sich die Spalten, Mitte zuerst) und **Chat**.
Jedes Panel zeigt echte, live abgefragte Werte - keine Deko-Statistiken:

- **System Status** - echte CPU-Last/RAM/Speicher-Auslastung deines
  Droplets als Gauges (`moni/system_stats.py`, liest `/proc/meminfo` und
  `os.getloadavg()`).
- **Gedächtnis & Portfolio** - Anzahl gelernter Fakten und verfolgter
  Positionen als Balken.
- **Fähigkeiten** - die tatsächlich verfügbaren Tools als Chips.
- **Wetter** - sobald du Moni im Chat sagst, wo du wohnst (Tool
  `set_location`, gespeichert in `~/.moni/location.json`), holt sie sich
  aktuelle Temperatur/Bedingung über die kostenlose, schlüssellose
  Open-Meteo-API (`moni/weather.py`).
- **Kalender** - echtes aktuelles Datum/Uhrzeit plus Wochenstreifen (kein
  Kalender-Sync, das steht auch klar dabei - keine erfundenen Termine).
- **Nächstes Briefing** - Uhrzeit/Datum des nächsten automatischen Laufs.
- **Deine Pins** - frei anheftbare Einträge (Nachricht, Aktienkurs,
  Erinnerung, was auch immer), die du Moni im Chat aufträgst (Tools
  `pin_to_dashboard`, `unpin_from_dashboard`, gespeichert in
  `~/.moni/widgets.json`). Bittest du erneut zum selben Titel (z. B.
  "aktualisier den Apple-Kurs"), wird der bestehende Pin überschrieben statt
  verdoppelt. Jeder Pin hat ein "×" zum direkten Entfernen.

**Panels reagieren auf das Gespräch:** Wenn eine Chat-Antwort ein Tool
benutzt (z. B. Portfolio ändern, Standort setzen, etwas anheften), liefert
`/api/chat`/`/api/confirm` mit `tools_used` zurück, welches Tool das war.
Das Frontend hebt das passende Panel dann kurz hervor (leicht vergrößert,
stärkerer Glow, ca. 6 Sekunden) - so wird sichtbar, worüber gerade
gesprochen wurde, ohne dass Chat-Text geraten werden muss.

## Architektur

```
moni/
  cli.py         - Chat-Loop für die Terminal-Nutzung
  web.py         - FastAPI-App: Login, Session, Chat-API mit Confirm-Flow,
                   Briefing-Scheduler, Status-Endpoint
  web_static/     - Login- und Chat-Oberfläche (HTML/CSS/JS)
  agent.py       - Claude-API-Aufrufe inkl. Tool-Use-Loop (CLI-Pfad)
  tools.py       - Tool-Definitionen + Ausführung (Shell, Dateien, Websuche,
                   Portfolio, Nutzer-Gedächtnis)
  portfolio.py   - Persistente Portfolio-Positionen (~/.moni/portfolio.json)
  profile.py     - Persistente Fakten über den Nutzer (~/.moni/profile.json)
  memory.py      - Persistenter Gesprächsverlauf
  voice.py       - Optionale Sprachein-/ausgabe (nur CLI)
  config.py      - Modell, Persönlichkeit/Systemprompt, Einstellungen
Dockerfile        - Container-Image für den Web-Modus
docker-compose.yml - Compose-Service für's Droplet
deploy/           - Reverse-Proxy-Vorlagen (Caddy/nginx)
```

## Nächste Schritte

Das hier ist bewusst ein schlankes Test-Setup. Wenn es sich bewährt, lässt es
sich später um weitere Tools erweitern (Kalender, Mail, Smart-Home-APIs etc.)
oder parallel als n8n-Workflow weiterbauen, wie beim ursprünglichen
Jarvis-Setup.
