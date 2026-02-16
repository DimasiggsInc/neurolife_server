from pydantic import BaseModel
from uuid import UUID

class MemorySchemaFull(BaseModel):
    id: UUID
