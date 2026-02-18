from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.chat.repositories import ChatRepository
from src.chat.services import ChatService
from src.chat.interfaces import ChatRepositoryPort, ChatServicePort


async def get_chat_repository(db: AsyncSession = Depends(get_session)) -> ChatRepositoryPort:
    return ChatRepository(db)


async def get_chat_service(
    session: AsyncSession = Depends(get_session),
    repo: ChatRepositoryPort = Depends(get_chat_repository),
) -> ChatServicePort:
    return ChatService(session=session, chat_repository=repo)
