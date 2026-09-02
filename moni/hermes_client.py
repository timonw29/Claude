"""Thin bridge to Hermes Agent's OpenAI-compatible API server. Hermes owns
the whole agent loop on its side - system prompt (SOUL.md), tools, and
skills (moni-assistant, ict-trading-bot) - so this module is intentionally
dumb: send the conversation, get back the final assistant text.

Known limitation, stated plainly: Hermes executes any tool/skill calls
server-side and only returns the final message (see
hermes_skills/README.md) - there is no pending tool_use for us to inspect,
confirm, or deny, and no visibility into which tools fired for a given
reply. That means the old per-tool confirmation dialog and the
"topic emphasis" dashboard highlight are both gone; only Hermes' own
built-in approval flow (interactive CLI/gateway sessions) still gates
risky actions, and that flow does not cover this API-server path.
"""

import json
import time
import urllib.error
import urllib.request

from . import config


class HermesError(RuntimeError):
    pass


def chat(messages):
    """Sends the full conversation and returns (reply_text, latency_ms, prompt_tokens)."""
    if not config.HERMES_API_KEY:
        raise HermesError("HERMES_API_KEY ist nicht gesetzt.")

    body = json.dumps({"model": "hermes-agent", "messages": messages, "stream": False}).encode()
    req = urllib.request.Request(
        config.HERMES_API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {config.HERMES_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        raise HermesError(f"Hermes-API-Fehler {e.code}: {detail}")
    except urllib.error.URLError as e:
        raise HermesError(f"Hermes nicht erreichbar: {e.reason}")

    latency_ms = round((time.monotonic() - start) * 1000)
    text = data["choices"][0]["message"]["content"]
    prompt_tokens = (data.get("usage") or {}).get("prompt_tokens")
    return text, latency_ms, prompt_tokens
