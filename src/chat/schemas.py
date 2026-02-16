from pydantic import BaseModel
from uuid import UUID

class ChatSchemaFull(BaseModel):
    id: UUID
