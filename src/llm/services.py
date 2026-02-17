from typing import List, Dict, Optional

from pathlib import Path
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


from src.llm.interfaces import LLMServicePort
from src.llm.schemas import LLMMessage, LLMResponse


class LLMService(LLMServicePort):
    async def generate_response(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> LLMResponse: ...
    
    async def generate_embedding(self, text: str) -> List[float]: ...
    
    async def analyze_sentiment(self, text: str) -> Dict[str, float]: ...
