import asyncio

from src.llm.schemas import AgentContextInput


class SimulationService:
    def __init__(self, agent_service, agent_repo, message_repo, llm_service, ws_manager, vector_repo = None):
        self.agent_service = agent_service
        self.agent_repo = agent_repo
        self.message_repo = message_repo
        # self.vector_repo = vector_repo
        self.llm_service = llm_service
        self.ws_manager = ws_manager

    async def process_agent_tick(self, agent):
        """
        Реализация блока "Генерируем ответы/игнор" из твоей схемы
        """
        # 1. Находим все чаты агента
        chats = await self.agent_repo.get_all_agent_chats(agent.id)
        
        events_to_broadcast = []

        for chat in chats:
            interlocutor = chat.get_other_participant(agent.id)
            
            # --- СБОР КОНТЕКСТА (Правая часть твоей схемы) ---
            
            # 1) Последние 10 сообщений
            last_messages = await self.message_repo.get_last_n_messages(chat.id, 10)
            
            # 2) Сумма остальных
            summary = await self.message_repo.get_summary_for_chat(chat.id)
            
            # 3) Инфо о собеседнике из Vector DB
            # vector_info = await self.vector_repo.search_memories(
            #     agent.id, 
            #     query=f"Что я знаю о {interlocutor.name}?"
            # )
            
            # 4) Вопрос (проверяем, есть ли unanswered вопрос в чате)
            pending_question = self.check_pending_question(last_messages)
            
            # 5) Настроение и инфо
            context = AgentContextInput(
                last_10_messages=last_messages,
                summary_of_rest=summary,
                vector_memory_about_interlocutor=None,  # vector_info,
                pending_question=pending_question,
                agent_mood=agent.mood,
                agent_profile=agent.profile
            )
            
            # --- ВЫЗОВ НЕЙРОСЕТИ ---
            decision = await self.llm_service.generate_agent_response(context)
            
            # --- СОХРАНЕНИЕ И ОТПРАВКА (Нижняя часть схемы) ---
            
            if decision.message_to_chat:
                await self.message_repo.save_message(chat.id, agent.id, decision.message_to_chat)
                events_to_broadcast.append({
                    "type": "new_message",
                    "data": {"agent": agent.name, "text": decision.message_to_chat}
                })
            
            if decision.new_mood != agent.mood:
                await self.agent_repo.update_agent_mood(agent.id, decision.new_mood)
                events_to_broadcast.append({
                    "type": "mood_change",
                    "data": {"agent": agent.name, "mood": decision.new_mood}
                })
                
            # Сохраняем новое воспоминание в Vector DB
            # await self.vector_repo.add_memory(agent.id, decision.new_memory_entry)

            # Обновляем граф отношений
            if decision.relationship_change != 0:
                 events_to_broadcast.append({
                    "type": "graph_update",
                    "data": {"source": agent.id, "target": interlocutor.id, "delta": decision.relationship_change}
                })

        return events_to_broadcast

    async def run_simulation_tick(self):
        """
        Запускается циклом в main.py
        """
        agents = await self.agent_repo.get_all_agents()
        all_events = []
        
        # Параллельная обработка всех агентов (asyncio.gather)
        tasks = [self.process_agent_tick(agent) for agent in agents]
        results = await asyncio.gather(*tasks)
        
        # Собираем все события
        for result in results:
            all_events.extend(result)
            
        # Отправляем всё на веб одним пакетом или по очереди
        for event in all_events:
            await self.ws_manager.broadcast(event)
