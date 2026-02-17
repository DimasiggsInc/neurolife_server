from sqlalchemy.ext.asyncio import AsyncSession
from src.speech_style.models import SpeechStyle
from src.speech_style.interfaces import SpeechStyleRepositoryPort

class SpeechStyleRepository(SpeechStyleRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, speech_style: SpeechStyle) -> SpeechStyle:
        self.session.add(speech_style)
        await self.session.flush()
        return speech_style