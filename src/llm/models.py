from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class Message:
    id: int
    chat_id: str
    sender_name: str
    content: str
    created_at: str
    world_timestamp: int
    is_system_event: bool = False
    embedding: Optional[Any] = None  # позже


@dataclass
class MessageMemoryView:
    """
    Аналог таблицы Message_memory_view:
    агент оценил важность ЧУЖОГО сообщения для будущей памяти.
    """
    id: int
    agent_name: str
    message_id: int
    importance: float
    created_at: str
