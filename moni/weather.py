import json
import urllib.parse
import urllib.request

_CONDITIONS = {
    0: "Klar",
    1: "Meist klar",
    2: "Teilweise bewölkt",
    3: "Bedeckt",
    45: "Nebel",
    48: "Nebel (Reif)",
    51: "Leichter Nieselregen",
    53: "Nieselregen",
    55: "Starker Nieselregen",
    61: "Leichter Regen",
    63: "Regen",
    65: "Starker Regen",
    71: "Leichter Schneefall",
    73: "Schneefall",
    75: "Starker Schneefall",
    80: "Regenschauer",
    81: "Regenschauer",
    82: "Heftige Regenschauer",
    95: "Gewitter",
    96: "Gewitter mit Hagel",
    99: "Gewitter mit Hagel",
}


def fetch_weather(city):
    """Looks up current weather for a city via the free, keyless Open-Meteo
    API. Returns None on any failure (unknown city, network issue, ...)."""
    try:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode(
            {"name": city, "count": 1, "language": "de"}
        )
        with urllib.request.urlopen(geo_url, timeout=5) as r:
            geo = json.load(r)
        results = geo.get("results")
        if not results:
            return None
        lat, lon, resolved_name = (
            results[0]["latitude"],
            results[0]["longitude"],
            results[0]["name"],
        )

        forecast_url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(
            {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code",
                "timezone": "auto",
            }
        )
        with urllib.request.urlopen(forecast_url, timeout=5) as r:
            forecast = json.load(r)
        current = forecast.get("current", {})
        code = current.get("weather_code")
        return {
            "city": resolved_name,
            "temperature": current.get("temperature_2m"),
            "condition": _CONDITIONS.get(code, "Unbekannt"),
        }
    except Exception:
        return None
