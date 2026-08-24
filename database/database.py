import os
from pathlib import Path

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base, ChatMessage

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = f"sqlite:///{BASE_DIR / 'data' / 'sales_assistant.db'}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    (BASE_DIR / "data").mkdir(exist_ok=True)
    Base.metadata.create_all(bind=engine)


def add_message(session_id: str, role: str, content: str) -> ChatMessage:
    with SessionLocal() as db:
        message = ChatMessage(session_id=session_id, role=role, content=content)
        db.add(message)
        db.commit()
        db.refresh(message)
        return message



def get_message(
    session_id: str,
    message_id: int
) -> ChatMessage | None:

    with SessionLocal() as db:
        return db.scalar(
            select(ChatMessage).where(
                ChatMessage.session_id == session_id,
                ChatMessage.id == message_id,
            )
        )


def get_history_before(
    session_id: str,
    message_id: int,
    limit: int = 12
) -> list[dict[str, str]]:

    with SessionLocal() as db:

        rows = db.scalars(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.id < message_id,
            )
            .order_by(ChatMessage.id.desc())
            .limit(limit)
        ).all()

        rows = list(reversed(rows))

        return [
            {
                "role": item.role,
                "content": item.content
            }
            for item in rows
        ]


def get_messages(session_id: str, limit: int = 100) -> list[ChatMessage]:
    with SessionLocal() as db:
        rows = db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.desc())
            .limit(limit)
        ).all()
        return list(reversed(rows))


def get_history(session_id: str, limit: int = 12) -> list[dict[str, str]]:
    messages = get_messages(session_id, limit=limit)
    return [{"role": item.role, "content": item.content} for item in messages]


def clear_messages(session_id: str) -> None:
    with SessionLocal() as db:
        db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
        db.commit()
