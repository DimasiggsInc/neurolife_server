from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from enum import StrEnum

class ChatType(StrEnum):
    DIRECT = "direct"
    GROUP = "group"
    SYSTEM = "system"

class ChatOverview(BaseModel):
    """Краткая информация о чате для списка"""
    id: UUID
    name: Optional[str]
    type: ChatType
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_message_preview: Optional[str] = None  # Последнее сообщение для превью
    unread_count: int = 0  # Количество непрочитанных
    participants_count: int = 0  # Количество участников

class AgentChatList(BaseModel):
    """Список чатов агента"""
    chats: List[ChatOverview]
    total_count: int
    agent_id: UUID

class ChatSchemaFull(BaseModel):
    id: UUID
