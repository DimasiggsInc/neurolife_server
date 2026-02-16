from sqlalchemy import Boolean, DateTime, Float, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from src.database import Base
from src.agent.schemas import AgentSchemaFull


class WorldState(Base):
    """Модель Агента для БД."""

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


    def to_read_model(self) -> AgentSchemaFull:
        """Преобразует модель в схему для чтения."""
        return AgentSchemaFull(
            id=self.id,
        )
