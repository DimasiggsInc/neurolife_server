import json
from typing import Any, Dict

import httpx
from pydantic import ValidationError

from src.llm.schemas import (
    AgentContextInput,
    AgentDecisionOutput,
    OpenAIChatCompletionResponse,
)

from src.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential

class LLMService:
    def __init__(self) -> None:
        self.base_url = settings.FREEQWEN_BASE_URL
        self.model = settings.FREEQWEN_MODEL
        self.timeout_s = settings.FREEQWEN_TIMEOUT

    def _build_system_prompt(self, ctx: AgentContextInput) -> str:
        agent_name = ctx.agent_profile.get("name", "Agent")
        return (
            f"Ты агент {agent_name}. Твое настроение: {ctx.agent_mood}.\n\n"
            "ВАЖНО:\n"
            "- Верни ТОЛЬКО валидный JSON. Никакого markdown. Никаких пояснений.\n"
            "- Строго по схеме:\n"
            "{"
            "\"new_mood\": \"happy\"|\"neutral\"|\"sad\", "
            "\"message_to_chat\": string|null, "
            "\"relationship_affinity\": number, "
            "\"memory_importance\": number"
            "}\n"
            "- memory_importance ∈ [0.0, 1.0]\n"
            "- relationship_affinity ∈ [-1.0, 1.0]\n"
        )

    def _extract_json(self, text: str) -> str:
        t = (text or "").strip()
        if not t:
            return ""

        # убрать ```json ... ```
        if "```" in t:
            t = t.replace("```json", "```").replace("```JSON", "```")
            parts = t.split("```")
            # берем кусок с максимальным числом фигурных скобок
            t = max(parts, key=lambda s: s.count("{") + s.count("}")).strip()

        # вырезать от первой { до последней }
        start = t.find("{")
        end = t.rfind("}")
        if start != -1 and end != -1 and end > start:
            return t[start:end + 1].strip()

        return ""

    def _build_user_prompt(self, ctx: AgentContextInput) -> str:
        return (
            "КОНТЕКСТ:\n"
            f"- История чата (последнее): {ctx.last_10_messages}\n"
            f"- Прошлое (саммари): {ctx.summary_of_rest}\n"
            f"- Память о собеседнике: {ctx.vector_memory_about_interlocutor}\n\n"
            "ЗАДАЧА:\n"
            f"Если есть вопрос ({ctx.pending_question}), ответь на него.\n"
            "Если вопроса нет — продолжай как агент.\n"
            "Верни JSON по схеме из system.\n"
        )

    def _build_user_prompt(self, ctx: AgentContextInput) -> str:
        return (
            "КОНТЕКСТ:\n"
            f"- История чата (последнее): {ctx.last_10_messages}\n"
            f"- Прошлое (саммари): {ctx.summary_of_rest}\n"
            f"- Память о собеседнике: {ctx.vector_memory_about_interlocutor}\n\n"
            "ЗАДАЧА:\n"
            f"Если есть вопрос ({ctx.pending_question}), ответь на него.\n"
            "Если вопроса нет — продолжай как агент.\n"
            "Верни JSON по схеме из system.\n"
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _call_chat_completions(self, payload: Dict[str, Any]) -> OpenAIChatCompletionResponse:
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            r = await client.post(f"{self.base_url}/chat/completions", json=payload)
            r.raise_for_status()
            raw = r.json()
        return OpenAIChatCompletionResponse.model_validate(raw)

    async def generate_agent_response(self, ctx: AgentContextInput) -> AgentDecisionOutput:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._build_system_prompt(ctx)},
                {"role": "user", "content": self._build_user_prompt(ctx)},
            ],
            "stream": False,
        }

        resp = await self._call_chat_completions(payload)
        raw_content = (resp.choices[0].message.content or "").strip()

        # если модель вернула пусто — НЕ делаем repair (иначе "нет сообщений от пользователя")
        if not raw_content:
            out = AgentDecisionOutput(
                new_mood=ctx.agent_mood,
                message_to_chat=None,
                relationship_affinity=0.0,
                memory_importance=0.0,
            )
            return out

        extracted = self._extract_json(raw_content)

        try:
            if not extracted:
                raise json.JSONDecodeError("no_json_found", raw_content, 0)
            data = json.loads(extracted)
            if "relationship_affinity" not in data:
                data["relationship_affinity"] = 0.0
            out = AgentDecisionOutput.model_validate(data)
        except (json.JSONDecodeError, ValidationError):
            # user content гарантированно НЕ пустой
            repair_payload: Dict[str, Any] = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Ты валидатор JSON. Верни ТОЛЬКО валидный JSON без markdown и пояснений "
                            "по схеме:\n"
                            "{"
                            "\"new_mood\":\"happy\"|\"neutral\"|\"sad\","
                            "\"message_to_chat\":string|null,"
                            "\"relationship_affinity\":number,"
                            "\"memory_importance\":number"
                            "}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Исправь и верни JSON. Вход ниже:\n"
                            f"{raw_content}\n\n"
                            "Если JSON отсутствует — сгенерируй корректный JSON сам."
                        ),
                    },
                ],
                "stream": False,
            }

            resp2 = await self._call_chat_completions(repair_payload)
            fixed_raw = (resp2.choices[0].message.content or "").strip()

            fixed = self._extract_json(fixed_raw)
            if not fixed:
                out = AgentDecisionOutput(
                    new_mood=ctx.agent_mood,
                    message_to_chat=None,
                    relationship_affinity=0.0,
                    memory_importance=0.0,
                )
                return out
            data = json.loads(fixed)
            if "relationship_affinity" not in data:
                data["relationship_affinity"] = 0.0
            out = AgentDecisionOutput.model_validate(data)

        out.relationship_affinity = max(-0.1, min(0.1, out.relationship_affinity))
        return out
