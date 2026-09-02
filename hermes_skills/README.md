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

## Setup auf dem Droplet

1. **Hermes Agent installieren** (Docker, passend zum bestehenden
   n8n/Caddy-Setup):
   ```bash
   git clone https://github.com/NousResearch/hermes-agent /root/hermes-agent
   cd /root/hermes-agent
   HERMES_UID=$(id -u) HERMES_GID=$(id -g) docker compose up -d --build
   ```
   (Baut lokal aus dem Dockerfile - erster Build kann einige Minuten
   dauern.)

2. **Anthropic als Modell-Provider konfigurieren** - denselben Key wie im
   ursprünglichen Moni-`.env` benutzen:
   ```bash
   docker exec -it hermes hermes model
   # → Anthropic wählen → API-Key eingeben (ANTHROPIC_API_KEY), Modell
   #   z. B. claude-sonnet-5
   ```

3. **Telegram-Gateway einrichten** (Bot-Token vorher bei @BotFather auf
   Telegram anlegen, siehe `t.me/BotFather` → `/newbot`):
   ```bash
   docker exec -it hermes hermes gateway setup
   # → Telegram wählen → Bot-Token einfügen → eigene Telegram-User-ID
   #   (von @userinfobot) als erlaubten Nutzer eintragen
   docker exec -it hermes hermes gateway start
   ```

4. **Moni-Persona einspielen:**
   ```bash
   docker cp /root/moni/hermes_skills/persona/SOUL.md hermes:/opt/data/SOUL.md
   ```
   (Pfad ggf. anpassen, falls `~/.hermes` woanders liegt als `/opt/data`
   im Container - siehe Kommentare in `docker-compose.yml` des
   hermes-agent-Checkouts.)

5. **Diese Skills einbinden** - in `~/.hermes/config.yaml` (im Container
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

6. **Bestehende Daten mitnehmen** - `~/.moni/*.json` (Portfolio, Aufgaben,
   Ziele, Gedächtnis, Standort) muss für den Hermes-Container ebenfalls
   erreichbar sein. Einfachster Weg: dasselbe Docker-Volume/denselben
   Host-Pfad wie beim ursprünglichen Moni-Container auch in Hermes'
   `docker-compose.yml` mounten (`~/.moni:/root/.moni` als zusätzliche
   `volumes`-Zeile beim `gateway`-Service).

7. Auf dem iPad: Telegram öffnen, dem eigenen Bot schreiben - fertig.

## Was (noch) nicht portiert ist

- **Gmail/Google Kalender**: Hermes hat eigene Integrationen für viele
  Dienste - vor einer eigenen Skill dafür erst prüfen, ob eine bereits
  mitgelieferte/optionale Hermes-Integration das abdeckt
  (`optional-mcps/`, `optional-skills/` im hermes-agent-Checkout).
- **Tägliches Briefing / wöchentlicher Selbst-Check**: Hermes hat einen
  eigenen Cron-Scheduler (`hermes cron` bzw. das `blueprint`-Feld in
  `SKILL.md`) - dafür müsste ein eigener Cron-Eintrag/Blueprint angelegt
  werden, analog zum bisherigen `07:00`-Briefing.
- Das ursprüngliche `moni/`-Webprojekt (FastAPI + Nocturne-Dashboard)
  bleibt im Repo unverändert bestehen und läuft unabhängig weiter, bis du
  entscheidest, den Container zu stoppen.
