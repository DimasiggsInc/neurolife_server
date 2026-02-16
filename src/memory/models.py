from sqlalchemy import UUID, String, Boolean, DateTime, Float, CheckConstraint, ARRAY
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from datetime import datetime

from src.database import Base
from src.memory.schemas import MemorySchemaFull


class Memory(Base):
    """Модель Памяти нейросети для БД."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        unique=True
    )

    embedding: Mapped[Vector] = mapped_column(
        Vector(1536),  # ⚠️ ЗАМЕНИТЕ 1536 НА ФАКТИЧЕСКУЮ РАЗМЕРНОСТЬ ВАШЕЙ МОДЕЛИ
        nullable=False
    )

    world_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow(),
        nullable=False
    )

    importance: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('value >= 0 AND value <= 1'),
        default=0
    )

    is_summarized: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    source_memory_ids: Mapped[list] = mapped_column(
        ARRAY(UUID),
        default=[]
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow(),
        nullable=False
    )


    def to_read_model(self) -> MemorySchemaFull:
        """Преобразует модель в схему для чтения."""
        return MemorySchemaFull(
            id=self.id,
        )
