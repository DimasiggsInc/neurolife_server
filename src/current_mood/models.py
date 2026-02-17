from sqlalchemy import UUID, DateTime, Float, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from datetime import datetime

from src.database import Base
from src.current_mood.schemas import AgentCurrentMood


class CurrentMood(Base):
    """Модель Агента для БД."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    joy: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )

    sadness: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )

    anger: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )

    fear: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow(),
        onupdate=datetime.utcnow(),
        nullable=False
    )


    def to_read_model(self) -> AgentCurrentMood:
        """Преобразует модель в схему для чтения."""
        return AgentCurrentMood(
            id=self.id,
        )
