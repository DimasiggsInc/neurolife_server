from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from src.message.repositories import MessageRepository
from src.message.interfaces import MessageRepositoryPort

from src.database import get_session


async def get_message_repository(
    db: AsyncSession = Depends(get_session),
) -> MessageRepositoryPort:
    return MessageRepository(db)
