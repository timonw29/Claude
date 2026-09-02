# Moni auf Hermes Agent

Dieser Ordner enthält, was gebraucht wird, um Moni auf
[Hermes Agent](https://github.com/NousResearch/hermes-agent) umzuziehen,
statt des ursprünglichen eigenen `moni/`-Webprojekts:

- `persona/SOUL.md` - Monis Identität/Persönlichkeit, als Hermes-`SOUL.md`.
- `productivity/moni-assistant/` - Skill für Portfolio, Aufgaben, Ziele,
  Gedächtnis und Standort (CLI-Skripte auf denselben `~/.moni/*.json`-
  Dateien wie das ursprüngliche Moni-Webprojekt).
- `finance/ict-trading-bot/` - Skill, die dokumentiert, wie Hermes den
  bestehenden `ICT_FTMO_Bot/` (Backtest, Live-/Demo-Loop) über die Konsole
  bedient - kein neuer Code, nur Anleitung für die bestehende CLI.

Hermes Agent selbst wird **nicht** in dieses Repo geklont - das ist ein
eigenständiges, sehr großes Drittanbieter-Projekt (eigene Python-/Node-
Umgebung, eigenes Docker-Image). Es lebt als eigener Checkout/eigene
Docker-Compose-Stack neben `moni/`, `n8n` und `caddy` auf demselben Droplet.

## Zugriffsweg: das bestehende Nocturne-Dashboard, nicht Telegram

Hermes selbst hat keine passwortgeschützte, im Browser aufrufbare
Oberfläche wie unser Dashboard - nur CLI/TUI, Chat-Plattformen (Telegram
usw.) und eine OpenAI-kompatible API. Wir nutzen **die API**: `moni/web.py`
(das bestehende Nocturne-Dashboard) spricht jetzt mit Hermes statt direkt
mit Anthropic - `moni/hermes_client.py` ist die Brücke. Damit bleibt die
vertraute Oberfläche unter `moni.myjarvis-ai.de` erhalten, nur das "Gehirn"
dahinter ist jetzt Hermes.

**Bewusst in Kauf genommener Sicherheits-Trade-off:** Hermes führt
Tool-/Skill-Aufrufe über die API **serverseitig automatisch aus** und
liefert sie schon erledigt zurück - es gibt keinen Erlauben/Ablehnen-Dialog
mehr für riskante Aktionen (Shell-Befehle, E-Mails, **den vollautonomen
ICT-Trading-Bot starten**). Hermes' eigenes Dangerous-Command-Genehmigungs-
system greift nur im interaktiven CLI-/Gateway-Modus (z. B. Telegram), nicht
über diese API. Das war eine explizite, informierte Entscheidung - wer das
später doch absichern will: dieselbe Telegram-Einrichtung ist weiterhin
möglich und behält den Genehmigungs-Dialog, siehe
[Telegram-Doku](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram).

## Setup auf dem Droplet

1. **Hermes Agent installieren:**
   ```bash
   git clone https://github.com/NousResearch/hermes-agent /root/hermes-agent
   cd /root/hermes-agent
   HERMES_UID=$(id -u) HERMES_GID=$(id -g) docker compose up -d --build
   ```

2. **Anthropic als Modell-Provider konfigurieren** (nicht-interaktiv, per
   `hermes config set`) - denselben Key wie im ursprünglichen Moni-`.env`:
   ```bash
   docker exec hermes hermes config set ANTHROPIC_API_KEY "$(grep ANTHROPIC_API_KEY /root/moni/.env | cut -d= -f2-)"
   docker exec hermes hermes config set model.provider anthropic
   docker exec hermes hermes config set model.default anthropic/claude-sonnet-5
   ```

3. **API-Server aktivieren** - in `~/.hermes/.env` (im Container unter
   `/opt/data/.env`):
   ```bash
   docker exec hermes hermes config set API_SERVER_ENABLED true
   docker exec hermes hermes config set API_SERVER_KEY "$(openssl rand -hex 32)"
   ```
   Den generierten Key merken/kopieren:
   ```bash
   docker exec hermes sh -c "grep API_SERVER_KEY /opt/data/.env"
   ```
   Läuft standardmäßig auf `127.0.0.1:8642` innerhalb des Hermes-Containers
   (der mit `network_mode: host` läuft, ist das faktisch das Droplet selbst)
   - **nicht** `API_SERVER_HOST=0.0.0.0` setzen, das würde die API offen ins
   Internet stellen.

4. **Moni auf die Bridge umstellen** - in `/root/moni/.env`:
   ```
   HERMES_API_KEY=<der API_SERVER_KEY von oben>
   HERMES_API_URL=http://host.docker.internal:8642/v1/chat/completions
   ```
   Danach neu deployen: `cd /root/moni && docker compose up -d --build`.

5. **Moni-Persona einspielen:**
   ```bash
   docker cp /root/moni/hermes_skills/persona/SOUL.md hermes:/opt/data/SOUL.md
   ```

6. **Diese Skills einbinden** - in `~/.hermes/config.yaml` (im Container
   unter `/opt/data/config.yaml`) ergänzen:
   ```yaml
   skills:
     external_dirs:
       - /repo/hermes_skills
   ```
   und `/root/moni:/repo` als zusätzliches Volume in Hermes' eigener
   `docker-compose.yml` ergänzen (derselbe Bind-Mount-Pfad, den auch der
   ursprüngliche Moni-Container für die Selbst-Weiterentwicklung nutzt),
   damit Hermes denselben Checkout sieht.

7. **Bestehende Daten mitnehmen** - `~/.moni/*.json` (Portfolio, Aufgaben,
   Ziele, Gedächtnis, Standort) muss für den Hermes-Container ebenfalls
   erreichbar sein: `~/.moni:/root/.moni` als zusätzliche `volumes`-Zeile
   beim `gateway`-Service in Hermes' eigener `docker-compose.yml`.

8. Auf dem iPad: `https://moni.myjarvis-ai.de` wie gewohnt öffnen - jetzt
   antwortet Hermes über die Nocturne-Oberfläche.

## Was sich am Dashboard-Verhalten ändert

- Der Erlauben/Ablehnen-Dialog für riskante Aktionen ist weg (siehe
  Sicherheits-Trade-off oben) - `moni/web.py` hat dafür keinen Code mehr,
  das ist kein UI-Bug.
- Die "Kachel wird kurz größer, wenn das Thema im Chat vorkam"-Hervorhebung
  ist ebenfalls weg - ohne Streaming sieht `moni/web.py` nicht, welches
  Tool Hermes benutzt hat. Tiles aktualisieren sich trotzdem nach jeder
  Antwort (nur ohne Hervorhebung).
- Portfolio/Aufgaben/Ziele/Gedächtnis/Standort-Kacheln funktionieren
  unverändert weiter - sie lesen weiterhin direkt aus `~/.moni/*.json`,
  unabhängig vom Chat-Backend.

## Was (noch) nicht portiert ist

- **Gmail/Google Kalender im Chat**: Die alten Tools (`send_email`,
  `create_calendar_event`, ...) existieren nur noch in `moni/tools.py`,
  das der Hermes-Chat nicht mehr aufruft. Die Termine-Kachel selbst
  funktioniert weiter (liest direkt über `gcalendar.py`). Für Gmail/
  Kalender im Chat: erst prüfen, ob eine mitgelieferte/optionale
  Hermes-Integration das abdeckt (`optional-mcps/`, `optional-skills/` im
  hermes-agent-Checkout), bevor eine eigene Skill dafür gebaut wird.
- **Tägliches Briefing / wöchentlicher Selbst-Check**: laufen weiterhin
  über `moni/web.py`s eigene Scheduler-Threads (jetzt via
  `hermes_client.py` statt direkt Anthropic) - unverändert funktional,
  nicht auf Hermes' eigenen Cron-Scheduler umgestellt.
- Das self_dev.py-Feature (`propose_code_change`) ist ebenfalls nicht
  mehr im Chat aufrufbar (war ein `moni/tools.py`-Tool) - lief aber schon
  vorher über eine direkte Claude-Agent-SDK-Verbindung, unabhängig vom
  Chat-Modell, und bleibt als automatischer wöchentlicher Lauf bestehen.
