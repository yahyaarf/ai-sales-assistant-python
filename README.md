# Mount Olympus AI — Python Sales Assistant

Python migration of the existing AI Sales Assistant.

## Stack

- FastAPI
- Uvicorn
- OpenAI Python SDK / Responses API
- SQLAlchemy + SQLite
- Jinja2
- HTMX
- HTML/CSS
- pandas, python-multipart, httpx ready for the next pipeline phase

## What changed

- `server.js` removed → `app.py` / FastAPI
- custom `public/app.js` removed → HTMX interactions
- UI structure/classes preserved
- `Agent_promptt.txt` remains the system sales prompt
- `.txt` chat import preserved
- Sales Copilot / Paste Full Chat / Objection Help preserved
- light/dark mode preserved
- server-side chat history stored in SQLite

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your real key to `.env`:

```env
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-5.6
PORT=3000
```

Run:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:3000
```

## Logo

If your existing copy already contains the Mount Olympus logo, place/copy it here:

```text
static/assets/new.png
```

The template automatically uses it. If it is missing, it falls back to an `MO` mark.

## Next architecture step

The next phase can add the lead pipeline in Python only:

`CSV → outreach queue → WhatsApp webhook → AI replies → demo queue → approval/send → qualified lead → human handoff`
