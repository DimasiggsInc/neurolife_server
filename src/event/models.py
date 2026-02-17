from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy import String, Text, DateTime, JSON, Integer, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.database import Base


class Event(Base):
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    type: Mapped[str] = mapped_column(
        String(50),nullable=False,
        index=True
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )

    involved_agents: Mapped[List[Any]] = mapped_column(
        JSON, 
        default=list, 
        nullable=False
    )

    payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON, 
        default=dict, 
        nullable=False
    )

    world_timestamp: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False,
        index=True
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, type='{self.type}', timestamp={self.world_timestamp})>"