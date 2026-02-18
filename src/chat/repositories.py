from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from src.chat.models import Chat
from src.chat_participant.models import ChatParticipant
from src.message.models import Message
from src.chat.schemas import ChatOverview
from typing import List, Optional
import uuid


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_active_chats_for_agent(
        self, 
        agent_id: uuid.UUID, 
        limit: int = 50
    ) -> List[Chat]:
        """
        Получить все активные чаты, где агент является участником
        """
        # Субзапрос для получения ID чатов, где участвует агент
        participant_subquery = select(ChatParticipant.chat_id).where(
            ChatParticipant.agent_id == agent_id,
            ChatParticipant.is_active == True
        )
        
        query = (
            select(Chat)
            .where(
                Chat.id.in_(participant_subquery),
                Chat.is_active == True
            )
            .order_by(Chat.updated_at.desc())  # Сначала новые
            .limit(limit)
            .options(selectinload(Chat.participants))  # Загружаем участников
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_last_message_for_chat(self, chat_id: uuid.UUID) -> Optional[Message]:
        """Получить последнее сообщение в чате для превью"""
        query = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_unread_count_for_agent(self, chat_id: uuid.UUID, agent_id: uuid.UUID) -> int:
        """Получить количество непрочитанных сообщений для агента в чате"""
        # Получаем timestamp последнего прочтения
        participant_query = select(ChatParticipant).where(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.agent_id == agent_id
        )
        participant_result = await self.session.execute(participant_query)
        participant = participant_result.scalar_one_or_none()
        
        if not participant or not participant.last_read_at:
            # Если нет записи о прочтении, считаем все сообщения непрочитанными
            count_query = select(func.count(Message.id)).where(Message.chat_id == chat_id)
        else:
            # Считаем сообщения после последнего прочтения
            count_query = select(func.count(Message.id)).where(
                Message.chat_id == chat_id,
                Message.created_at > participant.last_read_at
            )
        
        result = await self.session.execute(count_query)
        return result.scalar() or 0

    async def get_participants_count(self, chat_id: uuid.UUID) -> int:
        """Получить количество участников в чате"""
        query = select(func.count(ChatParticipant.id)).where(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.is_active == True
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
