"""Lets Moni use the real Claude Agent SDK (a full coding agent, not just her
own chat brain) to work on her own source code - always on a fresh git
branch, never pushing/merging/redeploying. A human reviews and deploys."""

import asyncio
import subprocess

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ResultMessage,
    query,
)

from . import config

REVIEW_SYSTEM_PROMPT = (
    "Du bist ein erfahrener Python-/Webentwickler, der den Code eines "
    "laufenden persönlichen Assistenten ('Moni', FastAPI-Backend + "
    "Vanilla-JS-Frontend) durchsieht. Analysiere den Code NUR - keine "
    "Änderungen. Schlage maximal 3 konkrete, sinnvolle Verbesserungen vor, "
    "kurz und auf Deutsch. Keine Stiländerungen ohne echten Nutzen, keine "
    "Bibliotheks-Wünsche ohne klare Begründung."
)

CHANGE_SYSTEM_PROMPT = (
    "Du bist ein erfahrener Python-/Webentwickler und arbeitest am Code des "
    "persönlichen Assistenten 'Moni' (FastAPI-Backend + Vanilla-JS-Frontend). "
    "Arbeite AUSSCHLIESSLICH auf einem neuen Git-Branch, niemals direkt auf "
    "dem aktuell ausgecheckten Branch: lege zuerst mit "
    "'git checkout -b moni-self-<kurzer-slug>' einen neuen Branch an, setze "
    "die Änderung um, committe sie mit einer klaren Nachricht. Push NICHT, "
    "merge NICHT, starte KEINE Container/Dienste neu - das entscheidet der "
    "Mensch. Fasse am Ende in 2-3 Sätzen zusammen, was du geändert hast und "
    "auf welchem Branch es liegt."
)

_MAX_TURNS_REVIEW = 15
_MAX_TURNS_CHANGE = 30


def _current_branch():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=config.REPO_PATH,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def _run(prompt, system_prompt, allowed_tools, max_turns):
    async def _go():
        options = ClaudeAgentOptions(
            cwd=config.REPO_PATH,
            system_prompt=system_prompt,
            allowed_tools=allowed_tools,
            permission_mode="acceptEdits",
            max_turns=max_turns,
        )
        result_text = None
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                result_text = message.result
        return result_text or "Keine Antwort erhalten."

    return asyncio.run(_go())


def propose_change(description):
    before = _current_branch()
    try:
        result = _run(
            description,
            CHANGE_SYSTEM_PROMPT,
            ["Read", "Edit", "Glob", "Grep", "Bash"],
            _MAX_TURNS_CHANGE,
        )
    except Exception as e:
        return f"Fehler bei der Selbst-Änderung: {e}"

    after = _current_branch()
    if before and after and before == after:
        result += (
            f"\n\n⚠️ Achtung: Es ist weiterhin Branch '{after}' aktiv - "
            "möglicherweise wurde kein neuer Branch angelegt. Bitte auf dem "
            "Server 'git status' und 'git branch' prüfen, bevor du "
            "weitermachst oder pullst."
        )
    return result


def suggest_improvements():
    try:
        return _run(
            "Schau dir den aktuellen Code an und schlage Verbesserungen vor.",
            REVIEW_SYSTEM_PROMPT,
            ["Read", "Glob", "Grep"],
            _MAX_TURNS_REVIEW,
        )
    except Exception as e:
        return f"Fehler beim Code-Review: {e}"
