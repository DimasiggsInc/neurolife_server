from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime


class LLMMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
