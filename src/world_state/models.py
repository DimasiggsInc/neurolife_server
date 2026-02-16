from sqlalchemy import Boolean, DateTime, Float, CheckConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from src.database import Base
from src.world_state.schemas import WorldStateSchemaFull

import uuid


class WorldState(Base):
    """Модель Агента для БД."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    time_speed: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0.5
    )
    simulation_paused: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow(),
        onupdate=datetime.utcnow(),
        nullable=False
    )


    def to_read_model(self) -> WorldStateSchemaFull:
        """Преобразует модель в схему для чтения."""
        return WorldStateSchemaFull(
            id=self.id,
        )
