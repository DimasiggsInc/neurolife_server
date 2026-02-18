from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import StrEnum


class ChatType(StrEnum):
    DIRECT = "DIRECT"
    GROUP = "GROUP"
    SYSTEM = "SYSTEM"


class ChatCreate(BaseModel):
    type: ChatType
    name: Optional[str] = Field(default=None, max_length=100)
    participant_ids: List[UUID]

class ChatOverview(BaseModel):
    id: UUID
    name: Optional[str]
    type: ChatType
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_message_preview: Optional[str] = None
    unread_count: int = 0
    participants_count: int = 0


class AgentChatList(BaseModel):
    chats: List[ChatOverview]
    total_count: int
    agent_id: UUID


class AgentChatIds(BaseModel):
    agent_id: UUID
    chat_ids: List[UUID]
    total_count: int


class ChatSchemaFull(BaseModel):
    id: UUID
    name: Optional[str]
    type: ChatType
    is_active: bool
    created_at: datetime
    updated_at: datetime
    world_timestamp_created: datetime

class MessageRead(BaseModel):
    id: UUID
    chat_id: UUID
    sender_id: UUID
    content: str
    created_at: datetime
    is_system_event: bool
    
class ChatDetail(BaseModel):
    chat: ChatSchemaFull
    messages: List[MessageRead]
    messages_total: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "chat": {
                        "id": "11111111-2222-3333-4444-555555555555",
                        "name": "Test chat",
                        "type": "DIRECT",
                        "is_active": True,
                        "created_at": "2026-02-18T05:00:00Z",
                        "updated_at": "2026-02-18T05:10:00Z",
                        "world_timestamp_created": "2026-02-18T05:00:00Z",
                    },
                    "messages": [
                        {
                            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                            "chat_id": "11111111-2222-3333-4444-555555555555",
                            "sender_id": "99999999-8888-7777-6666-555555555555",
                            "content": "Привет!",
                            "created_at": "2026-02-18T05:01:00Z",
                            "is_system_event": False,
                        },
                        {
                            "id": "bbbbbbbb-cccc-dddd-eeee-ffffffffffff",
                            "chat_id": "11111111-2222-3333-4444-555555555555",
                            "sender_id": "55555555-4444-3333-2222-111111111111",
                            "content": "Здорово 👋",
                            "created_at": "2026-02-18T05:02:00Z",
                            "is_system_event": False,
                        },
                    ],
                    "messages_total": 2,
                }
            ]
        }
    }