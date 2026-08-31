import json
import os

from . import config


def load_history():
    if not os.path.exists(config.HISTORY_FILE):
        return []
    try:
        with open(config.HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_history(messages):
    os.makedirs(config.HISTORY_DIR, exist_ok=True)
    plain = [_to_plain(m) for m in messages]
    with open(config.HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(plain, f, ensure_ascii=False, indent=2)


def clear_history():
    if os.path.exists(config.HISTORY_FILE):
        os.remove(config.HISTORY_FILE)


def _to_plain(message):
    """Collapses a message (which may hold rich content blocks such as
    tool_use/tool_result) down to plain text for cross-session persistence."""
    content = message["content"]
    if isinstance(content, str):
        return {"role": message["role"], "content": content}

    text_parts = []
    for block in content:
        block_type = block.type if hasattr(block, "type") else block.get("type")
        if block_type == "text":
            text_parts.append(block.text if hasattr(block, "text") else block["text"])
    return {"role": message["role"], "content": "".join(text_parts)}
