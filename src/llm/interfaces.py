from typing import Protocol



class LLMService(Protocol):
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