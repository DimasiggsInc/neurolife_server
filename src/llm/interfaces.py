from typing import Optional, List, Dict, Protocol
from pydantic import BaseModel

from src.llm.schemas import LLMMessage, LLMResponse


class LLMServicePort(Protocol):
    async def generate_response(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> LLMResponse: ...
    
    async def generate_embedding(self, text: str) -> List[float]: ...
    
    async def analyze_sentiment(self, text: str) -> Dict[str, float]: ...
