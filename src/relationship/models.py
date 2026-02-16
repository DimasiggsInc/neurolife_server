from sqlalchemy import UUID, String, Integer, DateTime, Float, CheckConstraint
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

    agent_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=False
    )

    agent_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=False
    )

    affinity: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=1
    )

    interaction_count: Mapped[int] = mapped_column(
        Integer,
        default=1
    )
    
    last_interaction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow(),
        nullable=False
    )

    history_summary_text: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        unique=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow(),
        nullable=False
    )


    def to_read_model(self) -> MessageSchemaFull:
        """Преобразует модель в схему для чтения."""
        return MessageSchemaFull(
            id=self.id,
        )
