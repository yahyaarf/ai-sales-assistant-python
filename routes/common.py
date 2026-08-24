from pathlib import Path
from uuid import uuid4

from fastapi import Request

BASE_DIR = Path(__file__).resolve().parent.parent

MODE_CONFIG = {
    "copilot": {
        "title": "Sales Copilot",
        "subtitle": "Paste what the lead said or ask what to reply next.",
        "banner_title": "Sales Copilot",
        "banner_text": "Get the reply plus the best next move.",
        "placeholder": "Paste the lead message or ask what to say...",
        "empty": "Paste the lead's message, an ongoing conversation, or ask for help with an objection.",
    },
    "full_chat": {
        "title": "Paste Full Chat",
        "subtitle": "The assistant reads the full conversation and returns only the next message.",
        "banner_title": "Full Chat Mode",
        "banner_text": "Paste the full lead conversation. Output = next reply only.",
        "placeholder": "Paste the full conversation here...",
        "empty": "Paste the complete chat. The AI will read the context and give you only the best next message to send.",
    },
    "objection": {
        "title": "Objection Help",
        "subtitle": "Get a short response for a specific objection or sales situation.",
        "banner_title": "Objection Help",
        "banner_text": "Describe the objection. Get the strongest short response.",
        "placeholder": "Example: Client says they already have someone doing this...",
        "empty": "Describe exactly what the client said and any context that changes the response.",
    },
}


def get_session_id(request: Request) -> str:
    return request.cookies.get("sales_session") or uuid4().hex


def safe_mode(mode: str | None) -> str:
    return mode if mode in MODE_CONFIG else "copilot"


def safe_channel(channel: str | None) -> str:
    return channel if channel in {"WhatsApp", "SMS", "Email", "Call"} else "WhatsApp"


def safe_theme(theme: str | None) -> str:
    return theme if theme in {"dark", "light"} else "dark"


def ui_context(
    request: Request,
    *,
    mode: str = "copilot",
    channel: str = "WhatsApp",
    theme: str | None = None,
    imported_text: str = "",
    messages=None,
):
    mode = safe_mode(mode)
    channel = safe_channel(channel)
    theme = safe_theme(theme or request.cookies.get("sales_theme"))

    return {
        "request": request,
        "mode": mode,
        "cfg": MODE_CONFIG[mode],
        "channel": channel,
        "theme": theme,
        "next_theme": "light" if theme == "dark" else "dark",
        "imported_text": imported_text,
        "messages": messages or [],
        "logo_exists": (BASE_DIR / "static" / "assets" / "new.png").exists(),
    }
