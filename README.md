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

- **Chat**: normale Unterhaltung über die Claude API (`claude-sonnet-5` als
  Standardmodell, überschreibbar via `MONI_MODEL`).
- **Automatisierung**: Moni kann Shell-Befehle ausführen, Dateien lesen/
  schreiben/auflisten und im Web suchen. Shell-Befehle und Schreibzugriffe
  fragen standardmäßig vor Ausführung nach (außer mit `--yes`).
- **Gedächtnis**: der Gesprächsverlauf wird in `~/.moni/history.json`
  gespeichert und beim nächsten Start wieder geladen.
- **Aufgaben & Ziele**: eine einfache To-do-Liste und Fortschrittsziele mit
  Ist-/Sollwert, die Moni direkt im Gespräch pflegt (`~/.moni/todos.json`,
  `~/.moni/goals.json`).
- **Gmail & Google Kalender** (optional, siehe eigener Abschnitt unten):
  ungelesene E-Mails zusammenfassen, E-Mails senden, den Tagesplan abrufen,
  Termine anlegen/löschen - nach einer einmaligen Google-Anmeldung.
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

**Wichtig, falls du eine eigene, vom Repo abweichende Compose-Datei pflegst**
(z. B. `/root/n8n/docker-compose.yml` statt der hier mitgelieferten): Das
`moni_data:/root/.moni`-Volume muss dort manuell ergänzt werden (siehe
`docker-compose.yml` in diesem Repo). Ohne dieses Volume gehen Portfolio,
Gedächtnis, Aufgaben, Ziele, Pins und der Google-Token bei jedem
`docker compose up -d --build` verloren, weil `~/.moni` sonst nur im
Container-Dateisystem liegt.

## Persönlichkeit & Gedächtnis

Moni hat eine feste Persönlichkeit (höflich-direkt, trockener Humor, JARVIS-
artig) im Systemprompt (`moni/config.py`). Zusätzlich lernt sie den Nutzer
über die Zeit kennen: Wenn beiläufig etwas Dauerhaftes erwähnt wird (Beruf,
Tagesablauf, Vorlieben), merkt Moni es sich selbstständig (Tools
`remember_about_user` / `recall_about_user` / `forget_about_user`,
gespeichert in `~/.moni/profile.json`) und bezieht es in künftige Antworten
ein - ganz ohne erneutes Nachfragen.

## Sprachein- und -ausgabe

**Eingabe:** Das Mikrofon-Symbol neben dem Textfeld startet die
Spracherkennung des Browsers (`SpeechRecognition`/`webkitSpeechRecognition`,
Deutsch). Nach dem Sprechen wird die erkannte Nachricht automatisch
gesendet, kein zusätzliches Antippen von "Senden" nötig. Läuft komplett im
Browser, kein Account, kein Key. Bei fehlender Unterstützung (z. B. manche
Browser ohne Web-Speech-API) ist der Button deaktiviert und Tippen
funktioniert wie gewohnt weiter.

**Ausgabe:** Im Web-Modus liest Moni jede Chat-Antwort automatisch laut vor. Standardmäßig
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

Der Web-Modus ist eine einzige Ansicht im **Nocturne**-Design (dunkles,
dichtes Interface): oben eine Topbar, darunter ein Kachelraster mit dem
rotierbaren 3D-"Kern" in der Mitte, ganz unten ein fest angedockter
Chat-Bereich - kein separates Dashboard/Chat-Tab-Umschalten mehr.

- **Topbar** - Datum/Uhrzeit, echte CPU-/RAM-Auslastung des Droplets
  (`moni/system_stats.py`), Online-Status, sowie der Button
  **"Kacheln anpassen"** für den Edit-Modus.
- **Kern-Kachel** - die 3D-Präsenz als eigene Web-Component
  (`moni/web_static/moni-core.js`, `<moni-core>`, three.js), mit der Maus
  drehbar. Zeigt oben rechts echtes Modell, Kontext-Auslastung (grob
  geschätzt aus den zuletzt genutzten Input-Tokens) und die Latenz der
  letzten Anfrage.
- **Termine** - ehrlich als "Kalender nicht verbunden" markiert; es gibt
  noch keine echte Kalenderanbindung, deshalb werden hier keine
  erfundenen Termine gezeigt.
- **Wetter** - sobald du Moni im Chat sagst, wo du wohnst (Tool
  `set_location`, `~/.moni/location.json`), holt sie sich aktuelle
  Temperatur/Bedingung über die kostenlose, schlüssellose Open-Meteo-API
  (`moni/weather.py`).
- **Ziele** - einfache Fortschrittsziele mit Ist-/Sollwert (Tools
  `list_goals`, `set_goal`, `update_goal_progress`, `remove_goal`,
  `~/.moni/goals.json`), z. B. "Laufen 24/40".
- **Portfolio** - deine echten, über `add_portfolio_position` getrackten
  Positionen als Chips (keine erfundenen Kursverläufe/Prozentzahlen, da
  Moni aktuell keine Kurshistorie speichert).
- **Aufgaben** - eine echte To-do-Liste (Tools `list_todos`, `add_todo`,
  `complete_todo`, `remove_todo`, `~/.moni/todos.json`); Klick auf eine
  Zeile im Dashboard toggelt sie direkt (`POST /api/todo/toggle`).
- **Live-Aktivität** - ein rollierendes Log der zuletzt tatsächlich
  ausgeführten Tools (`moni/activity.py`, `~/.moni/activity.json`) mit
  relativer Zeitangabe ("vor 12 s").
- **Gedächtnis** - standardmäßig ausgeblendet (Chip in der Edit-Leiste),
  zeigt Anzahl und letzte Einträge der über dich gelernten Fakten.

**Edit-Modus:** Kacheln lassen sich per Drag & Drop neu anordnen, über
↔/↕ in Breite/Höhe umschalten und über ✕ ausblenden (landen dann als Chip
in der Edit-Leiste). Das Layout wird bewusst nicht gespeichert - jeder
Seitenaufruf startet wieder mit der Standardanordnung.

**Kacheln reagieren auf das Gespräch:** Wenn eine Chat-Antwort ein Tool
benutzt (z. B. Portfolio ändern, ein Ziel aktualisieren, eine Aufgabe
abhaken), liefert `/api/chat`/`/api/confirm` mit `tools_used` zurück,
welches Tool das war. Das Frontend hebt die passende Kachel dann kurz
hervor (Glow in Akzentfarbe, ca. 6 Sekunden).

Die frei anheftbaren Pins (`pin_to_dashboard`/`unpin_from_dashboard`,
`~/.moni/widgets.json`) sind Teil dieses neuen Kachel-Sets nicht mehr -
das Tool und die Daten bleiben aber vollständig erhalten, falls du sie dir
später wieder als eigene Kachel wünschst.

## Google-Integration (Gmail & Kalender)

Moni kann optional dein Gmail-Postfach lesen/senden und deinen Google-Kalender
lesen/beschreiben. Ohne Verbindung sagt sie das ehrlich (die Termine-Kachel
zeigt "Kalender nicht verbunden" statt erfundener Termine).

**Einmalige Einrichtung in der Google Cloud Console:**

1. Projekt anlegen (oder ein bestehendes wählen) unter
   https://console.cloud.google.com/.
2. Unter **APIs & Services → Library**: **Gmail API** und **Google Calendar
   API** aktivieren.
3. Unter **APIs & Services → OAuth consent screen**: User-Typ **"External"**,
   Pflichtfelder ausfüllen (App-Name z. B. "Moni", deine E-Mail als Support-
   und Entwickler-Kontakt). Der Status kann auf **"Testing"** bleiben - dafür
   dich selbst unter **Test users** mit deiner Google-Adresse eintragen
   (sonst verweigert Google die Anmeldung, weil die App nicht verifiziert
   ist). Scopes hinzufügen: `gmail.readonly`, `gmail.send`,
   `calendar.events`.
4. Unter **APIs & Services → Credentials → Create Credentials → OAuth
   client ID**: Anwendungstyp **"Web application"**. Bei **Authorized
   redirect URIs** exakt eintragen:
   `https://moni.myjarvis-ai.de/oauth/google/callback`
   (Domain an deine echte anpassen, falls abweichend).
5. Client-ID und Client-Secret kopieren.

**Auf dem Droplet in `.env` ergänzen:**

```bash
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://moni.myjarvis-ai.de/oauth/google/callback
```

Danach neu deployen (`git pull` + `docker compose up -d --build`, siehe
Deployment-Abschnitt oben) und im Dashboard auf **"Mit Google verbinden"**
in der Termine-Kachel klicken (oder direkt `/oauth/google/start` aufrufen).
Nach der Google-Anmeldung/Zustimmung wird der Token in
`~/.moni/google_token.json` gespeichert und automatisch erneuert - die
Anmeldung ist einmalig.

**Werkzeuge, sobald verbunden:** `list_unread_emails`, `list_todays_events`
sind unkritisch und laufen ohne Rückfrage. `send_email`,
`create_calendar_event` und `delete_calendar_event` sind wie
`run_shell_command` bestätigungspflichtig (Erlauben/Ablehnen-Dialog im
Chat), da sie nach außen sichtbare bzw. schwer rückgängig zu machende
Wirkung haben.

## Selbst-Weiterentwicklung

Moni kann sich selbst weiterentwickeln - aber nie unbeaufsichtigt. Zwei Wege:

- **Auf Zuruf**: Bittest du sie im Chat um eine Code-Änderung/ein neues
  Feature ("Moni, füg X hinzu"), ruft sie über `propose_code_change`
  (`moni/self_dev.py`) den echten **Claude Agent SDK** auf - eine vollwertige
  Coding-Agent-Sitzung mit Datei- und Terminal-Zugriff auf ihren eigenen
  Code. Sie arbeitet dabei **immer auf einem neuen Git-Branch**, committet
  dort, aber **pusht/merged/deployed nichts von selbst** - das entscheidest
  du. Wie `run_shell_command`/`write_file` ist das ein bestätigungspflichtiges
  Tool (Erlauben/Ablehnen-Dialog im Chat).
- **Proaktiv, wöchentlich**: Jeden Montag um `MONI_SELFDEV_TIME` (Standard
  `08:30`) schaut sich Moni automatisch ihren eigenen Code an und schlägt bis
  zu drei Verbesserungen vor - rein lesend, ohne Änderungen. Der Vorschlag
  erscheint als eigene Karte im Chat-Verlauf. Gefällt dir eine Idee, bittest
  du sie im Chat, das umzusetzen (dann läuft der obige, bestätigungspflichtige
  Weg).

**Voraussetzungen:** `docker-compose.yml` bindet das echte Git-Arbeitsverzeichnis
nach `/repo` (siehe `volumes:`), und das Dockerfile installiert `git`. Nach
einer Selbst-Änderung liegt der neue Branch direkt im gewohnten Repo-Ordner
auf dem Droplet (z. B. `/root/moni`) - dort mit `git branch`/`git diff`
prüfen, mergen und danach ganz normal `docker compose up -d --build`.

**Ressourcen-Hinweis:** Eine Agent-SDK-Sitzung ist eine vollständige
Coding-Agent-Ausführung - spürbar mehr RAM- und Tokenverbrauch als normaler
Chat. Auf einem 1-GB-Droplet (wie hier) kann das den Server währenddessen
sichtbar verlangsamen; Swap federt harte Abstürze ab, ist aber kein Ersatz
für mehr RAM, falls das zum Problem wird.

## Architektur

```
moni/
  cli.py         - Chat-Loop für die Terminal-Nutzung
  web.py         - FastAPI-App: Login, Session, Chat-API mit Confirm-Flow,
                   Briefing-/Selfdev-Scheduler, Status-Endpoint
  web_static/     - Login- und Chat-Oberfläche (HTML/CSS/JS)
  agent.py       - Claude-API-Aufrufe inkl. Tool-Use-Loop (CLI-Pfad)
  tools.py       - Tool-Definitionen + Ausführung (Shell, Dateien, Websuche,
                   Portfolio, Nutzer-Gedächtnis, Selbst-Weiterentwicklung)
  self_dev.py    - Claude-Agent-SDK-Aufrufe (Branch-basierte Code-Änderungen,
                   rein lesende Verbesserungsvorschläge)
  portfolio.py   - Persistente Portfolio-Positionen (~/.moni/portfolio.json)
  profile.py     - Persistente Fakten über den Nutzer (~/.moni/profile.json)
  memory.py      - Persistenter Gesprächsverlauf
  voice.py       - Optionale Sprachein-/ausgabe (nur CLI)
  config.py      - Modell, Persönlichkeit/Systemprompt, Einstellungen
Dockerfile        - Container-Image für den Web-Modus (inkl. git)
docker-compose.yml - Compose-Service für's Droplet (mountet /repo)
deploy/           - Reverse-Proxy-Vorlagen (Caddy/nginx)
```

## Nächste Schritte

Das hier ist bewusst ein schlankes Test-Setup. Wenn es sich bewährt, lässt es
sich später um weitere Tools erweitern (Kalender, Mail, Smart-Home-APIs etc.)
oder parallel als n8n-Workflow weiterbauen, wie beim ursprünglichen
Jarvis-Setup.
