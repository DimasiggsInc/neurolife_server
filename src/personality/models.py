from sqlalchemy import UUID, String, Float, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from src.database import Base
from src.personality.schemas import PersonalitySchemaFull


class Personality(Base):
    """Модель Участника чата для БД."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    speech_style_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=False
    )

    friendship: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )

    knowledge: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )

    safety: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )

    freedom: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )

    openness: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )

    extraversion: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )

    agreebleness: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )

    neuroticism: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )

    conscientiousness: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )
    
    background: Mapped[str] = mapped_column(
        String(1000)
    )


    def to_read_model(self) -> PersonalitySchemaFull:
        """Преобразует модель в схему для чтения."""
        return PersonalitySchemaFull(
            id=self.id,
        )
