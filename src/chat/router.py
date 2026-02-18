from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from src.chat.schemas import ChatCreate, ChatOverview, ChatSchemaFull, ChatDetail
from src.chat.interfaces import ChatServicePort
from src.chat.dependencies import get_chat_service

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=List[ChatOverview])
async def list_all_chats(
    limit: int = 100,
    offset: int = 0,
    chat_service: ChatServicePort = Depends(get_chat_service),
) -> List[ChatOverview]:
    return await chat_service.list_all_chats(limit=limit, offset=offset)


@router.get("/{chat_id}", response_model=ChatDetail)
async def get_chat(
    chat_id: UUID,
    msg_limit: int = 200,
    msg_offset: int = 0,
    chat_service: ChatServicePort = Depends(get_chat_service),
) -> ChatDetail:
    try:
        return await chat_service.get_chat_detail(chat_id=chat_id, msg_limit=msg_limit, msg_offset=msg_offset)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=ChatSchemaFull, status_code=status.HTTP_201_CREATED)
async def create_chat(
    payload: ChatCreate,
    chat_service: ChatServicePort = Depends(get_chat_service),
) -> ChatSchemaFull:
    try:
        return await chat_service.create_chat(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: UUID,
    chat_service: ChatServicePort = Depends(get_chat_service),
):
    try:
        await chat_service.delete_chat(chat_id)
        return
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
