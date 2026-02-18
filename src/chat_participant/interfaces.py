from typing import Protocol, List
from uuid import UUID

from src.chat_participant.schemas import ChatParticipantRead


class ChatParticipantRepositoryPort(Protocol):
    async def list_participants_for_chat(self, chat_id: UUID) -> List[object]: ...


class ChatParticipantServicePort(Protocol):
    async def list_participants_for_chat(self, chat_id: UUID) -> List[ChatParticipantRead]: ...
