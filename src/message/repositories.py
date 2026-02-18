from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from typing import Optional, List
import uuid

from src.message.interfaces import MessageRepositoryPort
from src.message.models import Message


class MessageRepository(MessageRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, message: Message) -> Message:
        """Добавить новое сообщение"""
        self.session.add(message)
        await self.session.flush()
        return message
        
    async def get_by_id(self, message_id: uuid.UUID) -> Optional[Message]:
        """Получить сообщение по UUID"""
        result = await self.session.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True, limit: int = 20) -> List[Message]:
        """Получить список сообщений"""
        query = select(Message)
        
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_all(self, active_only: bool = True) -> Optional[int]:
        """Получить общее количество сообщений (расширенный метод, нет в Port)"""
        query = select(func.count(Message.id))
        
        if active_only:
            query = query.where(Message.is_active == True)
        
        result = await self.session.execute(query)
        return result.scalar()

    async def update(self, message: Message) -> Message:
        """Обновить данные сообщения"""
        await self.session.merge(message)
        await self.session.flush()
        return message

    async def delete(self, message_id: uuid.UUID) -> bool:
        """Удалить сообщение по ID"""
        # Исправлено: в Protocol указано int, но логичнее UUID (как в get_by_id)
        message = await self.get_by_id(message_id)
        if message:
            await self.session.delete(message)
            # Исправлено: flush вместо commit для консистентности с add/update
            await self.session.flush()
            return True
        return False
