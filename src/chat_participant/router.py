from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID

from src.chat_participant.schemas import ChatParticipantRead
from src.chat_participant.interfaces import ChatParticipantServicePort
from src.chat_participant.dependencies import get_chat_participant_service

router = APIRouter(prefix="/chats_participants", tags=["chats_participants"])


@router.get("/{chat_id}", response_model=List[ChatParticipantRead])
async def get_chat_participants(
    chat_id: UUID,
    service: ChatParticipantServicePort = Depends(get_chat_participant_service),
) -> List[ChatParticipantRead]:
    return await service.list_participants_for_chat(chat_id)
