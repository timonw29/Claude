import datetime
import os
import secrets
import threading
import time
from pathlib import Path
from zoneinfo import ZoneInfo

import anthropic
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from . import activity, config, goals, memory, portfolio, profile, system_stats, todos, tts, weather, widgets
from .tools import TOOLS, SAFE_TOOLS, CONFIRM_REQUIRED, run_tool

# Rough context-window budget used only to render a "context used" percentage
# in the dashboard topbar; not an exact accounting of the model's real limit.
CONTEXT_WINDOW_TOKENS = 200_000

BRIEFING_MARKER = "[AUTO-BRIEFING]"
SELFDEV_MARKER = "[AUTO-SELFDEV]"
_MARKER_ROLES = {BRIEFING_MARKER: "briefing", SELFDEV_MARKER: "selfdev"}

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


_last_call = {"latency_ms": None, "input_tokens": None}


def _call_model(tools):
    start = time.monotonic()
    response = _client.messages.create(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        system=config.build_system_prompt(),
        tools=tools,
        output_config={"effort": config.EFFORT},
        messages=_state["messages"],
    )
    _last_call["latency_ms"] = round((time.monotonic() - start) * 1000)
    usage = getattr(response, "usage", None)
    if usage is not None:
        _last_call["input_tokens"] = usage.input_tokens
    return response


def _process_blocks(blocks, results, used):
    """Executes tool_use blocks in order, pausing at the first one that
    needs confirmation. Returns ("confirm", block, remaining, results) or
    ("done", None, None, results). Every block's name is recorded in `used`
    (mutated in place) as soon as it's seen, confirmed or not - the frontend
    uses this to highlight the dashboard panel the turn was "about"."""
    for i, block in enumerate(blocks):
        used.append(block.name)
        if block.name in CONFIRM_REQUIRED:
            return "confirm", block, blocks[i + 1 :], results
        result = run_tool(block.name, block.input)
        activity.log(f"Tool genutzt: {block.name}")
        results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
    return "done", None, None, results


def _run_loop(tools=TOOLS, used=None):
    if used is None:
        used = []
    while True:
        response = _call_model(tools)
        _state["messages"].append({"role": "assistant", "content": response.content})

        if response.stop_reason == "tool_use":
            blocks = [b for b in response.content if b.type == "tool_use"]
            status, block, remaining, results = _process_blocks(blocks, [], used)
            if status == "confirm":
                _state["pending"] = {
                    "block": block,
                    "remaining": remaining,
                    "results": results,
                    "used": used,
                }
                return {"status": "confirm", "tool": block.name, "input": block.input}
            _state["messages"].append({"role": "user", "content": results})
            continue

        if response.stop_reason == "pause_turn":
            continue

        if response.stop_reason == "refusal":
            return {"status": "reply", "text": "[Moni hat die Anfrage abgelehnt.]", "tools_used": used}

        text = "".join(b.text for b in response.content if b.type == "text")
        return {"status": "reply", "text": text, "tools_used": used}


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
        activity.log(f"Tool {'genutzt' if approved else 'abgelehnt'}: {block.name}")
        results = pending["results"]
        results.append({"type": "tool_result", "tool_use_id": block.id, "content": result_text})
        used = pending.get("used", [])

        status, next_block, remaining, results = _process_blocks(pending["remaining"], results, used)
        if status == "confirm":
            _state["pending"] = {
                "block": next_block,
                "remaining": remaining,
                "results": results,
                "used": used,
            }
            return JSONResponse(
                {"status": "confirm", "tool": next_block.name, "input": next_block.input}
            )

        _state["messages"].append({"role": "user", "content": results})
        result = _run_loop(used=used)
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


def _block_text(content):
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        block_type = block.type if hasattr(block, "type") else block.get("type")
        if block_type == "text":
            parts.append(block.text if hasattr(block, "text") else block["text"])
    return "".join(parts)


@app.get("/api/history")
def history(request: Request):
    denied = _require_session(request)
    if denied:
        return denied

    out = []
    next_role = None
    with _lock:
        for m in _state["messages"]:
            text = _block_text(m["content"])
            if m["role"] == "user":
                marker_role = next((r for marker, r in _MARKER_ROLES.items() if text.startswith(marker)), None)
                if marker_role:
                    next_role = marker_role
                elif text:
                    out.append({"role": "user", "text": text})
            elif m["role"] == "assistant" and text:
                out.append({"role": next_role or "moni", "text": text})
                next_role = None
    return JSONResponse(out)


def _generate_briefing():
    prompt = (
        f"{BRIEFING_MARKER} Erstelle mein tägliches Morgen-Briefing. Nutze die "
        "Websuche für aktuelle Zahlen. Fasse kompakt zusammen (max. ca. 150 "
        "Wörter):\n"
        "1. Wichtigste Aktienindizes (DAX, S&P 500, Nasdaq) - aktueller Stand "
        "und Veränderung zum Vortag.\n"
        "2. Meine über list_portfolio abrufbaren Positionen - aktuelle Kurse "
        "und Tagesveränderung.\n"
        "Kein Smalltalk, keine Rückfragen - direkt die Fakten."
    )
    with _lock:
        checkpoint = len(_state["messages"])
        _state["messages"].append({"role": "user", "content": prompt})
        result = _run_loop(tools=SAFE_TOOLS)
        if result["status"] == "reply":
            memory.save_history(_state["messages"])
        else:
            # A safe-tools-only run should never need confirmation; if it
            # somehow does, roll back entirely rather than leave a dangling
            # tool_use in _state that would break the next real /api/chat call.
            _state["messages"] = _state["messages"][:checkpoint]
            _state["pending"] = None


def _next_briefing_datetime():
    tz = ZoneInfo(config.BRIEFING_TIMEZONE)
    now = datetime.datetime.now(tz)
    hour, minute = (int(x) for x in config.BRIEFING_TIME.split(":"))
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return target


def _seconds_until_next_briefing():
    tz = ZoneInfo(config.BRIEFING_TIMEZONE)
    return (_next_briefing_datetime() - datetime.datetime.now(tz)).total_seconds()


def _briefing_scheduler():
    while True:
        time.sleep(_seconds_until_next_briefing())
        try:
            _generate_briefing()
        except Exception:
            pass  # never let a bad run kill the scheduler thread


def _generate_self_dev_suggestion():
    from . import self_dev  # local import: heavier optional dependency

    text = self_dev.suggest_improvements()
    with _lock:
        _state["messages"].append({"role": "user", "content": SELFDEV_MARKER})
        _state["messages"].append({"role": "assistant", "content": text})
        memory.save_history(_state["messages"])


def _next_selfdev_datetime():
    tz = ZoneInfo(config.BRIEFING_TIMEZONE)
    now = datetime.datetime.now(tz)
    hour, minute = (int(x) for x in config.SELFDEV_TIME.split(":"))
    days_ahead = (config.SELFDEV_WEEKDAY - now.weekday()) % 7
    target = (now + datetime.timedelta(days=days_ahead)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    if target <= now:
        target += datetime.timedelta(days=7)
    return target


def _selfdev_scheduler():
    while True:
        tz = ZoneInfo(config.BRIEFING_TIMEZONE)
        target = _next_selfdev_datetime()
        time.sleep((target - datetime.datetime.now(tz)).total_seconds())
        try:
            _generate_self_dev_suggestion()
        except Exception:
            pass  # never let a bad run kill the scheduler thread


@app.on_event("startup")
def _start_scheduler():
    threading.Thread(target=_briefing_scheduler, daemon=True).start()
    threading.Thread(target=_selfdev_scheduler, daemon=True).start()


_weather_cache = {"city": None, "data": None, "ts": 0}
_WEATHER_TTL_SECONDS = 600


def _cached_weather():
    city = profile.get_location()
    if not city:
        return None
    now = time.time()
    if _weather_cache["city"] == city and now - _weather_cache["ts"] < _WEATHER_TTL_SECONDS:
        return _weather_cache["data"]
    data = weather.fetch_weather(city)
    _weather_cache.update({"city": city, "data": data, "ts": now})
    return data


@app.post("/api/speak")
async def speak(request: Request):
    denied = _require_session(request)
    if denied:
        return denied

    body = await request.json()
    text = (body.get("text") or "").strip()
    if not text:
        return JSONResponse({"error": "empty"}, status_code=400)

    audio = tts.synthesize(text)
    if audio is None:
        return JSONResponse({"error": "tts_unavailable"}, status_code=502)
    return Response(content=audio, media_type="audio/mpeg")


@app.get("/api/status")
def status(request: Request):
    denied = _require_session(request)
    if denied:
        return denied
    input_tokens = _last_call["input_tokens"]
    context_pct = (
        round(min(input_tokens, CONTEXT_WINDOW_TOKENS) / CONTEXT_WINDOW_TOKENS * 100)
        if input_tokens is not None
        else None
    )
    return JSONResponse(
        {
            "model": config.MODEL,
            "portfolio_count": len(portfolio._load()),
            "portfolio_positions": portfolio._load(),
            "profile_facts": len(profile._load()),
            "profile_fact_list": profile._load()[-5:],
            "next_briefing": _next_briefing_datetime().isoformat(),
            "briefing_time": config.BRIEFING_TIME,
            "tools": sorted(t.get("name") or t.get("type") for t in TOOLS),
            "weather": _cached_weather(),
            "system": system_stats.get_system_stats(),
            "widgets": widgets.list_widgets(),
            "todos": todos.list_todos(),
            "goals": goals.list_goals(),
            "activity": activity.recent(10),
            "latency_ms": _last_call["latency_ms"],
            "context_pct": context_pct,
        }
    )


@app.post("/api/todo/toggle")
async def toggle_todo(request: Request):
    denied = _require_session(request)
    if denied:
        return denied
    body = await request.json()
    index = body.get("index")
    if not isinstance(index, int):
        return JSONResponse({"error": "index fehlt"}, status_code=400)
    ok = todos.toggle_by_index(index)
    if not ok:
        return JSONResponse({"error": "ungültiger index"}, status_code=400)
    return JSONResponse({"ok": True, "todos": todos.list_todos()})


@app.get("/moni-core.js")
def moni_core_js():
    return FileResponse(STATIC_DIR / "moni-core.js", media_type="application/javascript")


@app.post("/api/unpin")
async def unpin(request: Request):
    denied = _require_session(request)
    if denied:
        return denied
    body = await request.json()
    title = (body.get("title") or "").strip()
    if not title:
        return JSONResponse({"error": "empty"}, status_code=400)
    widgets.unpin(title)
    return JSONResponse({"ok": True})
