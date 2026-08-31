import base64
import json
import urllib.request
from email.mime.text import MIMEText

from . import google_auth

API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


def _request(path, method="GET", data=None):
    token = google_auth.get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(API_BASE + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as r:
        raw = r.read()
        return json.loads(raw) if raw else None


def _header(headers, name):
    return next((h["value"] for h in headers if h["name"].lower() == name.lower()), "")


def list_unread(max_results=10):
    listing = _request(f"/messages?q=is:unread&maxResults={max_results}")
    ids = [m["id"] for m in listing.get("messages", [])]
    if not ids:
        return "Keine ungelesenen E-Mails."
    lines = []
    for msg_id in ids:
        msg = _request(
            f"/messages/{msg_id}?format=metadata&metadataHeaders=Subject&metadataHeaders=From"
        )
        headers = msg.get("payload", {}).get("headers", [])
        subject = _header(headers, "Subject") or "(kein Betreff)"
        sender = _header(headers, "From") or "?"
        snippet = msg.get("snippet", "")
        lines.append(f"- Von {sender}: {subject} - {snippet}")
    return "\n".join(lines)


def send_email(to, subject, body):
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    _request("/messages/send", method="POST", data={"raw": raw})
    return f"E-Mail an {to} gesendet: {subject}"
