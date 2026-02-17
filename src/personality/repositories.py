from sqlalchemy.ext.asyncio import AsyncSession
from src.personality.models import Personality
from src.personality.interfaces import PersonalityRepositoryPort

class PersonalityRepository(PersonalityRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, personality: Personality) -> Personality:
        self.session.add(personality)
        await self.session.flush()
        return personality