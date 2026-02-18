from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, List, Literal, Any
from datetime import datetime

class Message(BaseModel):
    id: int
    chat_id: str
    sender_name: str
    content: str
    created_at: str
    world_timestamp: int
    is_system_event: bool = False
    embedding: Optional[Any] = None  # позже


class MessageMemoryView(BaseModel):
    """
    Аналог таблицы Message_memory_view:
    агент оценил важность ЧУЖОГО сообщения для будущей памяти.
    """
    id: int
    agent_name: str
    message_id: int
    importance: float
    created_at: str



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
    last_10_messages: List[str]
    summary_of_rest: str
    vector_memory_about_interlocutor: str
    pending_question: Optional[str]
    agent_mood: str
    agent_profile: dict


class AgentDecisionOutput(BaseModel):
    new_mood: str
    message_to_chat: Optional[str]
    relationship_affinity: float
    memory_importance: float


class WSEvent(BaseModel):
    type: str  # 'agent_message', 'mood_change', 'graph_update'
    timestamp: datetime
    data: dict


class OpenAIChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class OpenAIChatChoice(BaseModel):
    index: int
    message: OpenAIChatMessage
    finish_reason: Optional[str] = None


class OpenAIUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenAIChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[OpenAIChatChoice]
    usage: Optional[Dict[str, Any]] = None

    chatId: Optional[str] = None
    parentId: Optional[str] = None

    model_config = ConfigDict(extra="allow")
