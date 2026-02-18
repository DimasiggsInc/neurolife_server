from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.chat_participant.repositories import ChatParticipantRepository
from src.chat_participant.services import ChatParticipantService
from src.chat_participant.interfaces import ChatParticipantRepositoryPort, ChatParticipantServicePort


async def get_chat_participant_repository(
    db: AsyncSession = Depends(get_session),
) -> ChatParticipantRepositoryPort:
    return ChatParticipantRepository(db)


async def get_chat_participant_service(
    session: AsyncSession = Depends(get_session),
    repo: ChatParticipantRepositoryPort = Depends(get_chat_participant_repository),
) -> ChatParticipantServicePort:
    return ChatParticipantService(session=session, repo=repo)
