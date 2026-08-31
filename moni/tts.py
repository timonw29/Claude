import json
import urllib.request

from . import config


def synthesize(text):
    """Synthesizes speech for `text` via the ElevenLabs TTS API. Returns
    the raw MP3 bytes, or None if no API key is configured or the request
    fails for any reason (caller falls back to text-only silently)."""
    if not config.ELEVENLABS_API_KEY:
        return None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
    payload = json.dumps(
        {
            "text": text,
            "model_id": config.ELEVENLABS_MODEL_ID,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "xi-api-key": config.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read()
    except Exception:
        return None
