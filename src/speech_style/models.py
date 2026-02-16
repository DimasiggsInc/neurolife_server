from sqlalchemy import UUID, Float, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from src.database import Base
from src.speech_style.schemas import SpeechStyleSchemaFull


class SpeechStyle(Base):
    """Модель Участника чата для БД."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    formality: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )

    verbosity: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )

    emotional_expressiveness: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )


    def to_read_model(self) -> SpeechStyleSchemaFull:
        """Преобразует модель в схему для чтения."""
        return SpeechStyleSchemaFull(
            id=self.id,
        )
