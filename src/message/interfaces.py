from typing import Protocol
from uuid import UUID

from typing import Optional, List
from src.message.models import Message



class MessageRepositoryPort(Protocol):
    """Интерфейс репозитория сообщений"""
    async def add(self, message: Message) -> Message: ...
    async def get_by_id(self, message_id: UUID) -> Optional[Message]: ...
    async def get_all(self, active_only: bool = True, limit: int = 20) -> List[Message]: ...
    async def delete(self, message_id: int) -> bool: ...
    async def update(self, message: Message) -> Message: ...


# class AgentServicePort(Protocol):
#     async def create_agent(self, new_agent: AgentCreate) -> AgentFullInfo: ...  # TODO



