from sqlalchemy.ext.asyncio import AsyncSession
from src.current_mood.models import CurrentMood
from src.current_mood.interfaces import CurrentMoodRepositoryPort


class CurrentMoodRepository(CurrentMoodRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, current_mood: CurrentMood) -> CurrentMood:
        self.session.add(current_mood)
        await self.session.flush()  # Чтобы получить ID
        return current_mood
