from pydantic import BaseModel
from uuid import UUID

class RelationshipSchemaFull(BaseModel):
    id: UUID
