from pydantic import BaseModel
from uuid import UUID

class MessageSchemaFull(BaseModel):
    id: UUID
