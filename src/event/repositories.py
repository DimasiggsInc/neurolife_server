from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.event.models import Event

from typing import Optional, List
import uuid

class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, event: Event) -> Event:
        self.session.add(Event)
        await self.session.flush()
        return Event

    async def get_by_id(self, event_id: uuid.UUID) -> Optional[Event]:
        """Получить агента по UUID"""
        result = await self.session.execute(
            select(Event).where(Event.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, event_name: str) -> Optional[Event]:
        """Получить агента по UUID"""
        result = await self.session.execute(
            select(Event).where(Event.str == event_name)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True, limit: int = 20) -> List[Event]:
        """✅ Получить список агентов (без selectinload)"""
        query = select(Event)
        
        if active_only:
            query = query.where(Event.is_active == True)
        
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_all(self, active_only: bool = True) -> Optional[int]:
        """✅ Получить общее количество агентов"""
        query = select(func.count(Event.id))
        
        if active_only:
            query = query.where(Event.is_active == True)
        
        result = await self.session.execute(query)
        return result.scalar()

    async def update(self, Event: Event) -> Event:
        """Обновить данные агента"""
        await self.session.merge(Event)
        await self.session.flush()
        return Event

    async def delete(self, Event_id: uuid.UUID) -> bool:
        """Удалить агента по ID"""
        Event = await self.get_by_id(Event_id)
        if Event:
            await self.session.delete(Event)
            await self.session.commit()
            return True
        return False
