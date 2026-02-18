from pydantic import BaseModel
from uuid import UUID

class MessageSchemaFull(BaseModel):
    id: UUID


class UserMessageToAgent(BaseModel):
    content: str


class MessageCreate(BaseModel):
    ...
