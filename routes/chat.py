from html import escape

from fastapi import (
    APIRouter,
    File,
    Form,
    Request,
    UploadFile
)

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from openai import AuthenticationError

from database.database import (
    add_message,
    get_history_before,
    get_message,
    get_messages,
)

from routes.common import (
    BASE_DIR,
    get_session_id,
    safe_channel,
    safe_mode,
    ui_context,
)

from services.ai_sales import generate_sales_reply


router = APIRouter()

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


def build_user_turn(
    message,
    attachment_name,
    attachment_text
):

    message = (
        message or ""
    ).strip()[:120000]

    attachment_text = (
        attachment_text or ""
    ).strip()[:120000]

    attachment_name = (
        attachment_name or ""
    ).strip().replace(
        "\n",
        " "
    )[:180]


    if not attachment_text:
        return message


    filename = (
        attachment_name
        or "chat-export.txt"
    )


    return (
        f"[[ATTACHMENT:{filename}]]\n"
        f"{attachment_text}\n"
        f"[[USER_NOTE]]\n"
        f"{message}"
    )


# ============================================================
# STEP 1:
# Immediately put user message into conversation
# ============================================================

@router.post(
    "/assist/start",
    response_class=HTMLResponse
)
def assist_start(
    request: Request,
    message: str = Form(""),
    mode: str = Form("copilot"),
    channel: str = Form("WhatsApp"),
    attachment_name: str = Form(""),
    attachment_text: str = Form(""),
):

    session_id = get_session_id(request)

    mode = safe_mode(mode)
    channel = safe_channel(channel)


    user_turn = build_user_turn(
        message,
        attachment_name,
        attachment_text
    )


    if not user_turn:

        return HTMLResponse(
            """
            <p class="error-message">
                Add a message or attach a .txt file.
            </p>
            """,
            status_code=400
        )


    current_message = add_message(
        session_id,
        "user",
        user_turn
    )


    context = ui_context(
        request,
        mode=mode,
        channel=channel,
        messages=get_messages(session_id),
    )


    context.update({
        "current_message_id":
            current_message.id,

        "textarea_placeholder":
            context["cfg"]["placeholder"],
    })


    response = templates.TemplateResponse(
        request=request,
        name="partials/assist_response.html",
        context=context,
    )


    response.set_cookie(
        "sales_session",
        session_id,
        httponly=True,
        samesite="lax"
    )


    return response


# ============================================================
# STEP 2:
# AI generates AFTER Thinking is already visible
# ============================================================

@router.post(
    "/assist/generate",
    response_class=HTMLResponse
)
def assist_generate(
    request: Request,
    message_id: int = Form(...),
    mode: str = Form("copilot"),
    channel: str = Form("WhatsApp"),
):

    session_id = get_session_id(request)

    mode = safe_mode(mode)
    channel = safe_channel(channel)


    current_message = get_message(
        session_id,
        message_id
    )


    if (
        not current_message
        or current_message.role != "user"
    ):

        return HTMLResponse(
            """
            <article class="message-row assistant">
                <div class="message-meta">
                    Sales Assistant
                </div>

                <div class="message-card">
                    <div class="message-content error-message">
                        Could not find the message.
                    </div>
                </div>
            </article>
            """,
            status_code=404
        )


    history = get_history_before(
        session_id,
        message_id,
        limit=12
    )


    try:

        reply = generate_sales_reply(
            current_message.content,
            mode,
            channel,
            history
        )


    except AuthenticationError:

        reply = (
            "Error: OpenAI API key rejected. "
            "Check OPENAI_API_KEY."
        )


    except Exception as exc:

        detail = str(exc)

        if "OPENAI_API_KEY" in detail:

            reply = f"Error: {detail}"

        else:

            reply = (
                "Error: Could not generate "
                "a sales response. Please try again."
            )


    assistant_message = add_message(
        session_id,
        "assistant",
        reply
    )


    response = templates.TemplateResponse(
        request=request,
        name="partials/conversation_content.html",
        context={
            "request": request,
            "messages": [assistant_message]
        }
    )


    response.set_cookie(
        "sales_session",
        session_id,
        httponly=True,
        samesite="lax"
    )


    return response


# ============================================================
# TXT IMPORT
# ============================================================

@router.post(
    "/import-chat",
    response_class=HTMLResponse
)
async def import_chat(
    chat_file: UploadFile = File(...)
):

    filename = (
        chat_file.filename or ""
    ).strip()


    if not filename.lower().endswith(".txt"):

        return HTMLResponse(
            """
            <div
                id="attachmentArea"
                class="attachment-area"
            >
                <span class="error-message">
                    Only .txt files are accepted.
                </span>
            </div>
            """,
            status_code=400
        )


    raw = await chat_file.read()


    if len(raw) > 1_500_000:

        return HTMLResponse(
            """
            <div
                id="attachmentArea"
                class="attachment-area"
            >
                <span class="error-message">
                    File is too large.
                </span>
            </div>
            """,
            status_code=400
        )


    try:

        text = raw.decode("utf-8-sig")

    except UnicodeDecodeError:

        text = raw.decode(
            "latin-1",
            errors="replace"
        )


    text = text.strip()[:120000]


    if not text:

        return HTMLResponse(
            """
            <div
                id="attachmentArea"
                class="attachment-area"
            >
                <span class="error-message">
                    The file is empty.
                </span>
            </div>
            """,
            status_code=400
        )


    safe_filename = escape(
        filename[:180],
        quote=True
    )

    safe_text = escape(text)


    return HTMLResponse(
        f"""
        <div
            id="attachmentArea"
            class="attachment-area"
        >

            <div class="attachment-chip">

                <span class="file-type">
                    TXT
                </span>

                <span class="attachment-info">

                    <strong>
                        {safe_filename}
                    </strong>

                    <small>
                        Chat export attached
                    </small>

                </span>

                <button
                    type="button"
                    class="attachment-remove"
                    hx-post="/attachment/clear"
                    hx-target="#attachmentArea"
                    hx-swap="outerHTML"
                >
                    ×
                </button>

            </div>


            <input
                type="hidden"
                name="attachment_name"
                value="{safe_filename}"
            />


            <textarea
                name="attachment_text"
                hidden
            >{safe_text}</textarea>

        </div>
        """
    )


@router.post(
    "/attachment/clear",
    response_class=HTMLResponse
)
def clear_attachment():

    return HTMLResponse(
        """
        <div
            id="attachmentArea"
            class="attachment-area"
        ></div>
        """
    )
