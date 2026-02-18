from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class ChatParticipantSchemaFull(BaseModel):
    id: UUID


class ChatParticipantRead(BaseModel):
    id: UUID
    chat_id: UUID
    agent_id: UUID
    joined_at: datetime
    world_joined_at: datetime
