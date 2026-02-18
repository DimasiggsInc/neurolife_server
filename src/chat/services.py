from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from uuid import UUID
import uuid as uuid_lib

from sqlalchemy.ext.asyncio import AsyncSession

from src.chat.interfaces import ChatServicePort, ChatRepositoryPort
from src.chat.models import Chat
from src.chat.schemas import ChatCreate, ChatOverview, AgentChatList, ChatSchemaFull, ChatType
from src.chat_participant.models import ChatParticipant

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class ChatService(ChatServicePort):
    def __init__(self, session: AsyncSession, chat_repository: ChatRepositoryPort) -> None:
        self.session = session
        self.chat_repo = chat_repository

    async def create_chat(self, payload: ChatCreate) -> ChatSchemaFull:
        # Валидация DIRECT: ровно 2 участника
        if payload.type == ChatType.DIRECT and len(payload.participant_ids) != 2:
            raise ValueError("DIRECT chat должен иметь ровно 2 участника")

        now = utc_now()

        chat = Chat(
            id=uuid_lib.uuid4(),
            name=payload.name,
            type=payload.type,
            is_active=True,
            updated_at=now,
            world_timestamp_created=now,
        )

        self.session.add(chat)
        await self.session.flush()

        participants = [
            ChatParticipant(
                id=uuid_lib.uuid4(),
                chat_id=chat.id,
                agent_id=pid,
                joined_at=now,
                world_joined_at=now,
            )
            for pid in payload.participant_ids
        ]

        self.session.add_all(participants)

        await self.session.commit()
        await self.session.refresh(chat)

        return chat.to_read_model()
    
    async def delete_chat(self, chat_id: UUID) -> bool:
        chat = await self.chat_repo.get_chat(chat_id)
        if not chat:
            raise ValueError("Чат не найден")

        await self.session.delete(chat)
        await self.session.commit()
        return True

    
    async def get_agent_chat_ids(self, agent_id: UUID, limit: int = 50) -> List[UUID]:
        chats = await self.chat_repo.get_all_chats_for_agent(agent_id=agent_id, limit=limit)
        return [c.id for c in chats]

    async def get_agent_chats(self, agent_id: UUID, limit: int = 50) -> AgentChatList:
        chats = await self.chat_repo.get_all_chats_for_agent(agent_id=agent_id, limit=limit)

        items: List[ChatOverview] = []
        for chat in chats:
            last_msg = await self.chat_repo.get_last_message_for_chat(chat.id)
            participants_count = await self.chat_repo.get_participants_count(chat.id)

            items.append(
                ChatOverview(
                    id=chat.id,
                    name=chat.name,
                    type=chat.type,
                    is_active=chat.is_active,
                    created_at=chat.created_at,
                    updated_at=chat.updated_at,
                    last_message_preview=(last_msg.content if last_msg else None),
                    unread_count=0,  # нет last_read_at -> пока 0
                    participants_count=participants_count,
                )
            )

        return AgentChatList(chats=items, total_count=len(items), agent_id=agent_id)
    
    async def list_all_chats(self, limit: int = 100, offset: int = 0) -> List[ChatOverview]:
        chats = await self.chat_repo.list_all_chats(limit=limit, offset=offset)

        items: List[ChatOverview] = []
        for chat in chats:
            last_msg = await self.chat_repo.get_last_message_for_chat(chat.id)
            participants_count = await self.chat_repo.get_participants_count(chat.id)

            items.append(
                ChatOverview(
                    id=chat.id,
                    name=chat.name,
                    type=chat.type,
                    is_active=chat.is_active,
                    created_at=chat.created_at,
                    updated_at=chat.updated_at,
                    last_message_preview=(last_msg.content if last_msg else None),
                    unread_count=0,
                    participants_count=participants_count,
                )
            )

        return items  # <- ВАЖНО: всегда list, даже если пусто