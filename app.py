# python3 -m venv .venv
# source .venv/bin/activate

# pip install -r requirements.txt

# python app.py

import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from database.database import init_db  # noqa: E402
from routes.chat import router as chat_router  # noqa: E402
from routes.pages import router as pages_router  # noqa: E402
from services.ai_sales import MODEL, SALES_PROMPT  # noqa: E402

app = FastAPI(title="Mount Olympus AI Sales Assistant")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(pages_router)
app.include_router(chat_router)


@app.on_event("startup")
def startup() -> None:
    init_db()
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY is not set. Add it to .env before using the assistant.")


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "model": MODEL,
        "promptLoaded": bool(SALES_PROMPT.strip()),
        "backend": "FastAPI",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "3000"))
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=True)
