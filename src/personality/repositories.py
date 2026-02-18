from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.personality.models import Personality
from src.personality.interfaces import PersonalityRepositoryPort
from uuid import UUID


class PersonalityRepository(PersonalityRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, personality: Personality) -> Personality:
        self.session.add(personality)
        await self.session.flush()
        return personality
    
    async def get_by_id(self, personality_id: UUID) -> Personality:
        result = await self.session.execute(
            select(Personality).where(Personality.id == personality_id)
        )
        return result.scalar_one_or_none()
