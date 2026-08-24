import os
from pathlib import Path

from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPT_PATH = BASE_DIR / "Agent_promptt.txt"

SALES_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")

MODE_RULES = {
    "copilot": """
MODE: SALES COPILOT
The human sales agent is asking for tactical help.
Follow the core sales prompt's normal agent-help format when useful:
What they really mean / Send this / Next move / If they push back / Important warning only when needed.
Keep the total answer concise. The exact client-facing reply must be immediately usable.
Do not give generic sales theory unless explicitly requested.
""",
    "full_chat": """
MODE: PASTE FULL CHAT
The user is pasting an ongoing lead conversation.
Read the entire conversation and silently determine the sales stage, real objection, buying signals, risk, and best next move.
IMPORTANT OUTPUT OVERRIDE: return ONLY the exact next client-facing message the sales agent should send.
Do NOT show analysis, stage labels, "What they really mean", "Next move", explanations, warnings, or commentary.
Keep it natural and normally 1-4 sentences. If multiple WhatsApp messages are genuinely better, separate them with a blank line, but do not label them.
""",
    "objection": """
MODE: OBJECTION / SITUATION HELP
The sales agent wants help with one objection, client question, or sales stage.
Give the strongest short response first. Add at most one brief tactical note only if it materially helps.
Never over-explain.
""",
}


def generate_sales_reply(
    message: str,
    mode: str,
    channel: str,
    history: list[dict[str, str]],
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured on the server.")

    client = OpenAI(api_key=api_key)
    selected_mode = MODE_RULES.get(mode, MODE_RULES["copilot"])

    instructions = (
        f"{SALES_PROMPT}\n\n"
        "--- APPLICATION MODE RULES ---\n"
        f"{selected_mode}\n"
        f"CHANNEL: {channel}. Adapt length and formatting to this channel.\n"
        "OUTPUT FORMATTING:\n"
        "- Use plain text only. Never use markdown symbols such as **, *, or #.\n"
        "- Put each section on a separate line.\n"
        "- Leave one blank line between sections.\n"
        "- Keep the answer compact and easy to scan.\n"
        "- Never combine all sections into one paragraph."
    )

    clean_history = []
    for item in history[-12:]:
        role = item.get("role")
        content = str(item.get("content", ""))[:12000]
        if role in {"user", "assistant"} and content:
            clean_history.append({"role": role, "content": content})

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=[*clean_history, {"role": "user", "content": message[:120000]}],
    )

    reply = (response.output_text or "").strip()

    # Remove markdown bold markers
    reply = reply.replace("**", "")

    # Force important sections onto separate lines
    labels = [
        "What they really mean:",
        "Send this:",
        "Next move:",
        "If they push back:",
        "Important warning:",
    ]

    for label in labels:
        reply = reply.replace(label, f"\n\n{label}\n")

    # Clean excessive line breaks
    while "\n\n\n" in reply:
        reply = reply.replace("\n\n\n", "\n\n")

    reply = reply.strip()

    if not reply:
        raise RuntimeError("The model returned an empty response.")

    return reply
