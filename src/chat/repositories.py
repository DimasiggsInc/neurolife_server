from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import uuid

from src.chat.models import Chat
from src.chat_participant.models import ChatParticipant
from src.message.models import Message


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all_chats(self, limit: int = 100, offset: int = 0) -> List[Chat]:
        query = (
            select(Chat)
            .where(Chat.is_active == True)
            .order_by(Chat.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_chat(self, chat_id: uuid.UUID) -> Optional[Chat]:
        result = await self.session.execute(select(Chat).where(Chat.id == chat_id))
        return result.scalar_one_or_none()

    async def get_last_message_for_chat(self, chat_id: uuid.UUID) -> Optional[Message]:
        query = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    async def delete_chat(self, chat_id: uuid.UUID) -> bool:
        chat = await self.get_chat(chat_id)
        if not chat:
            return False
        await self.session.delete(chat)
        return True
    async def get_participants_count(self, chat_id: uuid.UUID) -> int:
        query = select(func.count(ChatParticipant.id)).where(ChatParticipant.chat_id == chat_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def list_messages_for_chat(self, chat_id: uuid.UUID, limit: int = 200, offset: int = 0) -> List[Message]:
        # Обычно для чата удобнее по времени по возрастанию.
        query = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_messages_for_chat(self, chat_id: uuid.UUID) -> int:
        query = select(func.count(Message.id)).where(Message.chat_id == chat_id)
        result = await self.session.execute(query)
        return result.scalar() or 0
