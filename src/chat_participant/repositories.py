from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from src.chat_participant.models import ChatParticipant


class ChatParticipantRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_participants_for_chat(self, chat_id: UUID) -> List[ChatParticipant]:
        result = await self.session.execute(
            select(ChatParticipant).where(ChatParticipant.chat_id == chat_id)
        )
        return list(result.scalars().all())
