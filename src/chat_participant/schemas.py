from pydantic import BaseModel
from uuid import UUID

class СhatParticipantSchemaFull(BaseModel):
    id: UUID
