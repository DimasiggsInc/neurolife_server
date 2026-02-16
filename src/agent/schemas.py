from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

from src.current_mood.schemas import AgentCurrentMood

class AgentFullInfo(BaseModel):
    id: UUID


class AgentOverview(BaseModel):
    id: UUID
    name: str
    avatar: str
    mood: AgentCurrentMood
    is_active: bool
    last_activity: datetime


class AgentList(BaseModel):
    agents: List[AgentOverview]
    total_count: int
    active_count: int
