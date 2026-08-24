from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from database.database import clear_messages, get_messages
from routes.common import BASE_DIR, get_session_id, safe_channel, safe_mode, ui_context

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/", response_class=HTMLResponse)
def home(request: Request, mode: str = "copilot", channel: str = "WhatsApp"):
    session_id = get_session_id(request)
    context = ui_context(
        request,
        mode=mode,
        channel=channel,
        messages=get_messages(session_id),
    )
    response = templates.TemplateResponse(request=request, name="index.html", context=context)
    response.set_cookie("sales_session", session_id, httponly=True, samesite="lax")
    return response


@router.get("/ui", response_class=HTMLResponse)
def ui(request: Request, mode: str = "copilot", channel: str = "WhatsApp"):
    session_id = get_session_id(request)
    context = ui_context(
        request,
        mode=mode,
        channel=channel,
        messages=get_messages(session_id),
    )
    response = templates.TemplateResponse(request=request, name="partials/app_shell.html", context=context)
    response.set_cookie("sales_session", session_id, httponly=True, samesite="lax")
    return response


@router.post("/ui/new-chat", response_class=HTMLResponse)
def new_chat(request: Request, mode: str = "copilot", channel: str = "WhatsApp"):
    session_id = get_session_id(request)
    clear_messages(session_id)
    context = ui_context(request, mode=mode, channel=channel, messages=[])
    response = templates.TemplateResponse(request=request, name="partials/app_shell.html", context=context)
    response.set_cookie("sales_session", session_id, httponly=True, samesite="lax")
    return response


@router.get("/ui/starter", response_class=HTMLResponse)
def starter(request: Request, text: str = "", mode: str = "copilot"):
    mode = safe_mode(mode)
    return templates.TemplateResponse(
        request=request,
        name="partials/textarea.html",
        context={
            "request": request,
            "value": text[:120000],
            "placeholder": ui_context(request, mode=mode)["cfg"]["placeholder"],
            "oob": False,
        },
    )


@router.get("/theme/{theme}")
def set_theme(theme: str, mode: str = "copilot", channel: str = "WhatsApp"):
    theme = theme if theme in {"dark", "light"} else "dark"
    mode = safe_mode(mode)
    channel = safe_channel(channel)
    response = RedirectResponse(url=f"/?mode={mode}&channel={channel}", status_code=303)
    response.set_cookie("sales_theme", theme, max_age=60 * 60 * 24 * 365, samesite="lax")
    return response
