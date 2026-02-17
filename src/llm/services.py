import os
import httpx

from typing import List, Dict, Optional

from pathlib import Path
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


from src.llm.interfaces import LLMServicePort
from src.llm.schemas import LLMMessage, LLMResponse

from typing import Any, Dict, Optional, Tuple, Union
from dotenv import load_dotenv


# Формата ответа от qwen
async def qwen_chat(
    *,
    api_url: str,
    model: str,
    message: Union[str, list],
    chat_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    timeout: float = 60.0,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[str, Optional[str], Optional[str]]:
    payload: Dict[str, Any] = {
        "model": model,
        "message": message,
    }
    if chat_id:
        payload["chatId"] = chat_id
    if parent_id:
        payload["parentId"] = parent_id

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(api_url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()

    answer = data["choices"][0]["message"]["content"]

    new_chat_id = data.get("chatId") or data.get("chat_id")
    new_parent_id = data.get("parentId") or data.get("parent_id")

    return answer, new_chat_id, new_parent_id



class LLMService(LLMServicePort):
    async def generate_agent_response(self, context: AgentContextInput) -> AgentDecisionOutput:
        """
        Формирует промпт и отправляет в LLM (OpenAI/Gemini/YandexGPT)
        """
        prompt = f"""
        Ты агент {context.agent_profile['name']}. Твое настроение: {context.agent_mood}.
        
        КОНТЕКСТ:
        - История чата (последнее): {context.last_10_messages}
        - Прошлое (саммари): {context.summary_of_rest}
        - Что ты знаешь о собеседнике (из памяти): {context.vector_memory_about_interlocutor}
        
        ЗАДАЧА:
        Реши, что делать. Если есть вопрос ({context.pending_question}), ответь на него.
        Верни JSON с полями: mood, memory, message, relationship_delta.
        """
        # Тут вызов API нейросети
        # response = await client.chat.completions.create(...)
        return AgentDecisionOutput(...)
    async def generate_embedding(self, text: str) -> List[float]: ...
    
    async def analyze_sentiment(self, text: str) -> Dict[str, float]: ...
