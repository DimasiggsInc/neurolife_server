from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.chat_participant.interfaces import ChatParticipantServicePort, ChatParticipantRepositoryPort
from src.chat_participant.schemas import ChatParticipantRead


class ChatParticipantService(ChatParticipantServicePort):
    def __init__(self, session: AsyncSession, repo: ChatParticipantRepositoryPort):
        self.session = session
        self.repo = repo

    async def list_participants_for_chat(self, chat_id: UUID) -> List[ChatParticipantRead]:
        rows = await self.repo.list_participants_for_chat(chat_id)
        return [
            ChatParticipantRead(
                id=r.id,
                chat_id=r.chat_id,
                agent_id=r.agent_id,
                joined_at=r.joined_at,
                world_joined_at=r.world_joined_at,
            )
            for r in rows
        ]
