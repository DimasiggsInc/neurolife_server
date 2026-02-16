from sqlalchemy import UUID, String, Boolean, DateTime
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from datetime import datetime

from src.database import Base
from src.message.schemas import MessageSchemaFull


class Message(Base):
    """Модель Сообщения для БД."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=False
    )

    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    embedding: Mapped[Vector] = mapped_column(
        Vector(1536),  # ⚠️ ЗАМЕНИТЕ 1536 НА ФАКТИЧЕСКУЮ РАЗМЕРНОСТЬ ВАШЕЙ МОДЕЛИ
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow(),
        nullable=False
    )

    is_system_event: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )


    def to_read_model(self) -> MessageSchemaFull:
        """Преобразует модель в схему для чтения."""
        return MessageSchemaFull(
            id=self.id,
        )
