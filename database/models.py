from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


ATTACHMENT_PREFIX = "[[ATTACHMENT:"
USER_NOTE_MARKER = "\n[[USER_NOTE]]\n"


class Base(DeclarativeBase):
    pass


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    session_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @property
    def attachment_name(self):
        if (
            self.role != "user"
            or not self.content.startswith(ATTACHMENT_PREFIX)
        ):
            return ""

        first_line = self.content.split("\n", 1)[0]

        if not first_line.endswith("]]"):
            return ""

        return first_line[
            len(ATTACHMENT_PREFIX):-2
        ].strip()

    @property
    def visible_text(self):
        if not self.attachment_name:
            return self.content

        if USER_NOTE_MARKER not in self.content:
            return ""

        return self.content.split(
            USER_NOTE_MARKER,
            1
        )[1].strip()
