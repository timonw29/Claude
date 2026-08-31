import json
import os
import time
import urllib.parse
import urllib.request

from . import config

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events",
]


def _load():
    if not os.path.exists(config.GOOGLE_TOKEN_FILE):
        return None
    try:
        with open(config.GOOGLE_TOKEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save(tokens):
    os.makedirs(config.HISTORY_DIR, exist_ok=True)
    with open(config.GOOGLE_TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f)


def is_connected():
    return _load() is not None


def disconnect():
    if os.path.exists(config.GOOGLE_TOKEN_FILE):
        os.remove(config.GOOGLE_TOKEN_FILE)


def build_authorize_url():
    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    return AUTH_URL + "?" + urllib.parse.urlencode(params)


def _post_token(payload):
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def exchange_code(code):
    result = _post_token(
        {
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": config.GOOGLE_REDIRECT_URI,
        }
    )
    _save(
        {
            "refresh_token": result["refresh_token"],
            "access_token": result["access_token"],
            "expires_at": time.time() + result.get("expires_in", 3600),
        }
    )


def get_access_token():
    """Returns a valid access token, refreshing it first if it's expired.
    Raises RuntimeError if Google hasn't been connected yet."""
    tokens = _load()
    if not tokens:
        raise RuntimeError("Google ist noch nicht verbunden.")
    if tokens["expires_at"] > time.time() + 30:
        return tokens["access_token"]

    result = _post_token(
        {
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "refresh_token": tokens["refresh_token"],
            "grant_type": "refresh_token",
        }
    )
    tokens["access_token"] = result["access_token"]
    tokens["expires_at"] = time.time() + result.get("expires_in", 3600)
    _save(tokens)
    return tokens["access_token"]
