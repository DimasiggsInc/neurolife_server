from sqlalchemy import UUID, String, Text, Boolean, DateTime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from datetime import datetime

from src.database import Base
from src.agent.schemas import AgentFullInfo


class Agent(Base):
    """Модель Агента для БД."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    personality_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=False
    )

    ai_model: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    current_mood_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        unique=True
    )

    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    current_plan: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow(),
        onupdate=datetime.utcnow(),
        nullable=False
    )


    def to_read_model(self) -> AgentFullInfo:
        """Преобразует модель в схему для чтения."""
        return AgentFullInfo(
            id=self.id,
        )
