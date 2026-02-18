from pydantic import BaseModel
from uuid import UUID

class ChatParticipantSchemaFull(BaseModel):
    id: UUID
