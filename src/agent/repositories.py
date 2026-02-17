from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.agent.models import Agent
from src.agent.interfaces import AgentRepositoryPort
from typing import Optional, List
import uuid

class AgentRepository(AgentRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, agent: Agent) -> Agent:
        self.session.add(agent)
        await self.session.flush()
        return agent

    async def get_by_id(self, agent_id: uuid.UUID) -> Optional[Agent]:
        """Получить агента по UUID"""
        result = await self.session.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True, limit: int = 20) -> List[Agent]:
        """✅ Получить список агентов (без selectinload)"""
        query = select(Agent)
        
        if active_only:
            query = query.where(Agent.is_active == True)
        
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_all(self, active_only: bool = True) -> Optional[int]:
        """✅ Получить общее количество агентов"""
        query = select(func.count(Agent.id))
        
        if active_only:
            query = query.where(Agent.is_active == True)
        
        result = await self.session.execute(query)
        return result.scalar()

    async def update(self, agent: Agent) -> Agent:
        """Обновить данные агента"""
        await self.session.merge(agent)
        await self.session.flush()
        return agent

    async def delete(self, agent_id: uuid.UUID) -> bool:
        """Удалить агента по ID"""
        agent = await self.get_by_id(agent_id)
        if agent:
            await self.session.delete(agent)
            await self.session.commit()
            return True
        return False