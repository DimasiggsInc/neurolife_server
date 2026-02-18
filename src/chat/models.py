from sqlalchemy import UUID, String, Boolean, DateTime, func, Enum
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from datetime import datetime
from typing import Optional

from src.database import Base
from src.chat.schemas import ChatSchemaFull, ChatType


class Chat(Base):
    __tablename__ = "chat"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    type: Mapped[ChatType] = mapped_column(Enum(ChatType), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    world_timestamp_created: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def to_read_model(self) -> ChatSchemaFull:
        return ChatSchemaFull(
            id=self.id,
            name=self.name,
            type=self.type,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
            world_timestamp_created=self.world_timestamp_created,
        )
