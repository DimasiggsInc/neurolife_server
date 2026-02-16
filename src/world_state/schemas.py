from pydantic import BaseModel
from uuid import UUID

class WorldStateSchemaFull(BaseModel):
    id: UUID
