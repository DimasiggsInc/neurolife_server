from sqlalchemy import UUID, DateTime
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from datetime import datetime

from src.database import Base
from src.chat_participant.schemas import СhatParticipantSchemaFull


class СhatParticipant(Base):
    """Модель Участника чата для БД."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=False
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=False
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow(),
        nullable=False
    )

    world_joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow(),
        nullable=False
    )


    def to_read_model(self) -> СhatParticipantSchemaFull:
        """Преобразует модель в схему для чтения."""
        return СhatParticipantSchemaFull(
            id=self.id,
        )
