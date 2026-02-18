from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from src.current_mood.repositories import CurrentMoodRepository
from src.personality.repositories import PersonalityRepository
from src.speech_style.repositories import SpeechStyleRepository
from src.agent.services import AgentService
from src.agent.repositories import AgentRepository
from src.agent.interfaces import AgentServicePort, AgentRepositoryPort, ImageGeneratorPort
from src.agent.utils import ImageGenerator, generate_color
from src.chat.repositories import ChatRepository
from src.database import get_session


async def get_image_generator():
    return ImageGenerator()


async def get_agent_repository(
    db: AsyncSession = Depends(get_session),
) -> AgentRepositoryPort:
    return AgentRepository(db)


async def get_agent_service(session: AsyncSession = Depends(get_session), image_gen: ImageGeneratorPort = Depends(get_image_generator), ):
    return AgentService(
        session=session,
        image_generator=image_gen,
        agent_repository=AgentRepository(session),
        speech_style_repository=SpeechStyleRepository(session),
        personality_repository=PersonalityRepository(session),
        current_mood_repository=CurrentMoodRepository(session),
        chat_repository=ChatRepository(session)
    )
