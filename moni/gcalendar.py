import datetime
import json
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

from . import config, google_auth

API_BASE = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


def _request(url, method="GET", data=None):
    token = google_auth.get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as r:
        raw = r.read()
        return json.loads(raw) if raw else None


def _today_window():
    tz = ZoneInfo(config.BRIEFING_TIMEZONE)
    now = datetime.datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + datetime.timedelta(days=1)
    return start.isoformat(), end.isoformat()


def list_today_events():
    time_min, time_max = _today_window()
    params = urllib.parse.urlencode(
        {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": "true",
            "orderBy": "startTime",
        }
    )
    data = _request(f"{API_BASE}?{params}")
    events = []
    for item in data.get("items", []):
        start = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
        events.append(
            {
                "id": item["id"],
                "summary": item.get("summary", "(ohne Titel)"),
                "start": start,
                "location": item.get("location"),
            }
        )
    return events


def list_today_events_text():
    events = list_today_events()
    if not events:
        return "Heute keine Termine."
    return "\n".join(f"- {e['start']}: {e['summary']}" for e in events)


def create_event(summary, start_iso, end_iso, description=None):
    body = {
        "summary": summary,
        "start": {"dateTime": start_iso},
        "end": {"dateTime": end_iso},
    }
    if description:
        body["description"] = description
    _request(API_BASE, method="POST", data=body)
    return f"Termin angelegt: {summary} ({start_iso})"


def delete_event_by_title(title_substring):
    time_min, _ = _today_window()
    params = urllib.parse.urlencode(
        {
            "timeMin": time_min,
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": 50,
        }
    )
    data = _request(f"{API_BASE}?{params}")
    match = next(
        (i for i in data.get("items", []) if title_substring.lower() in i.get("summary", "").lower()),
        None,
    )
    if not match:
        return f"Kein Termin zu '{title_substring}' gefunden."
    _request(f"{API_BASE}/{match['id']}", method="DELETE")
    return f"Termin gelöscht: {match.get('summary')}"
