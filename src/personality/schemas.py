from pydantic import BaseModel
from uuid import UUID

class PersonalitySchemaFull(BaseModel):
    id: UUID
