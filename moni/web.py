import os
import secrets
import threading
import time
from pathlib import Path

import anthropic
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from . import config, memory
from .tools import TOOLS, CONFIRM_REQUIRED, run_tool

STATIC_DIR = Path(__file__).parent / "web_static"
COOKIE_NAME = "moni_session"

WEB_PASSWORD = os.environ.get("MONI_WEB_PASSWORD")
if not WEB_PASSWORD:
    raise RuntimeError("MONI_WEB_PASSWORD muss gesetzt sein, um den Webmodus zu starten.")

SESSION_SECRET = os.environ.get("MONI_SESSION_SECRET") or secrets.token_hex(32)

app = FastAPI()

_client = anthropic.Anthropic()
_lock = threading.Lock()
_state = {"messages": memory.load_history(), "pending": None}

# Simple brute-force guard on the login endpoint.
_failed_attempts = []
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 900


def _is_locked_out():
    now = time.time()
    _failed_attempts[:] = [t for t in _failed_attempts if now - t < _WINDOW_SECONDS]
    return len(_failed_attempts) >= _MAX_ATTEMPTS


def _valid_session(request: Request) -> bool:
    token = request.cookies.get(COOKIE_NAME)
    return token is not None and secrets.compare_digest(token, SESSION_SECRET)


def _require_session(request: Request):
    if not _valid_session(request):
        return JSONResponse({"status": "error", "text": "Nicht eingeloggt."}, status_code=401)
    return None


@app.get("/login")
def login_page():
    return FileResponse(STATIC_DIR / "login.html")


@app.post("/api/login")
async def login(request: Request):
    if _is_locked_out():
        return JSONResponse(
            {"ok": False, "error": "Zu viele Fehlversuche. Bitte später erneut versuchen."},
            status_code=429,
        )
    body = await request.json()
    password = body.get("password", "")
    if not secrets.compare_digest(password, WEB_PASSWORD):
        _failed_attempts.append(time.time())
        return JSONResponse({"ok": False, "error": "Falsches Passwort."}, status_code=401)

    response = JSONResponse({"ok": True})
    response.set_cookie(
        COOKIE_NAME,
        SESSION_SECRET,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return response


@app.post("/logout")
def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response


@app.get("/")
def index(request: Request):
    if not _valid_session(request):
        return RedirectResponse("/login", status_code=302)
    return FileResponse(STATIC_DIR / "index.html")


def _call_model():
    return _client.messages.create(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        system=config.SYSTEM_PROMPT,
        tools=TOOLS,
        output_config={"effort": config.EFFORT},
        messages=_state["messages"],
    )


def _process_blocks(blocks, results):
    """Executes tool_use blocks in order, pausing at the first one that
    needs confirmation. Returns ("confirm", block, remaining, results) or
    ("done", None, None, results)."""
    for i, block in enumerate(blocks):
        if block.name in CONFIRM_REQUIRED:
            return "confirm", block, blocks[i + 1 :], results
        result = run_tool(block.name, block.input)
        results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
    return "done", None, None, results


def _run_loop():
    while True:
        response = _call_model()
        _state["messages"].append({"role": "assistant", "content": response.content})

        if response.stop_reason == "tool_use":
            blocks = [b for b in response.content if b.type == "tool_use"]
            status, block, remaining, results = _process_blocks(blocks, [])
            if status == "confirm":
                _state["pending"] = {"block": block, "remaining": remaining, "results": results}
                return {"status": "confirm", "tool": block.name, "input": block.input}
            _state["messages"].append({"role": "user", "content": results})
            continue

        if response.stop_reason == "pause_turn":
            continue

        if response.stop_reason == "refusal":
            return {"status": "reply", "text": "[Moni hat die Anfrage abgelehnt.]"}

        text = "".join(b.text for b in response.content if b.type == "text")
        return {"status": "reply", "text": text}


@app.post("/api/chat")
async def chat(request: Request):
    denied = _require_session(request)
    if denied:
        return denied
    if _state["pending"] is not None:
        return JSONResponse(
            {"status": "error", "text": "Es wartet noch eine Bestätigung."}, status_code=409
        )

    body = await request.json()
    message = (body.get("message") or "").strip()
    if not message:
        return JSONResponse({"status": "error", "text": "Leere Nachricht."}, status_code=400)

    with _lock:
        _state["messages"].append({"role": "user", "content": message})
        result = _run_loop()
        if result["status"] == "reply":
            memory.save_history(_state["messages"])
    return JSONResponse(result)


@app.post("/api/confirm")
async def confirm(request: Request):
    denied = _require_session(request)
    if denied:
        return denied

    body = await request.json()
    approved = bool(body.get("approved"))

    with _lock:
        pending = _state.pop("pending", None)
        if pending is None:
            return JSONResponse(
                {"status": "error", "text": "Keine offene Bestätigung."}, status_code=409
            )

        block = pending["block"]
        result_text = run_tool(block.name, block.input) if approved else "Vom Nutzer abgelehnt."
        results = pending["results"]
        results.append({"type": "tool_result", "tool_use_id": block.id, "content": result_text})

        status, next_block, remaining, results = _process_blocks(pending["remaining"], results)
        if status == "confirm":
            _state["pending"] = {"block": next_block, "remaining": remaining, "results": results}
            return JSONResponse(
                {"status": "confirm", "tool": next_block.name, "input": next_block.input}
            )

        _state["messages"].append({"role": "user", "content": results})
        result = _run_loop()
        if result["status"] == "reply":
            memory.save_history(_state["messages"])
    return JSONResponse(result)


@app.post("/api/reset")
def reset(request: Request):
    denied = _require_session(request)
    if denied:
        return denied
    with _lock:
        _state["messages"] = []
        _state["pending"] = None
        memory.clear_history()
    return JSONResponse({"ok": True})
