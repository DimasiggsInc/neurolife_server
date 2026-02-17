from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime

# LLMModelList, LLMModelFullInfo, LLMModelOverview, LLMModelCreate
class LLMMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None


class LLMModelList(BaseModel):
    models: list[str]

class AgentContextInput(BaseModel):
    last_10_messages: List[str]       # 1) Последние 10 сообщений
    summary_of_rest: str              # 2) Сумма остальных (саммари)
    vector_memory_about_interlocutor: str # 3) Инфо о собеседнике из Vector DB
    pending_question: Optional[str]   # 4) Вопрос (если есть)
    agent_mood: str                   # 5) Настроение
    agent_profile: dict               # 5) Инфо об агенте (личность)
    
class AgentDecisionOutput(BaseModel):
    new_mood: str                     # 1) Новое настроение
    new_memory_entry: str             # 2) Новое воспоминание (для векторной БД)
    message_to_chat: Optional[str]    # 3) Сообщение в чат (или None, если игнор)
    relationship_change: float        # Изменение отношения к собеседнику (-0.1 до 0.1)

class WSEvent(BaseModel):
    type: str                         # 'agent_message', 'mood_change', 'graph_update'
    timestamp: datetime
    data: dict