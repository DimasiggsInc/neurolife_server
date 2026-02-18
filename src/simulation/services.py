import asyncio
from typing import Optional
from src.llm.schemas import AgentContextInput

class SimulationService:
    def __init__(self, agent_service, agent_repo, message_repo, llm_service, ws_manager, vector_repo=None):
        self.agent_service = agent_service
        self.agent_repo = agent_repo
        self.message_repo = message_repo
        self.llm_service = llm_service
        self.ws_manager = ws_manager
        self.vector_repo = vector_repo
        
        # Состояние симуляции
        self._is_running: bool = False
        self._simulation_task: Optional[asyncio.Task] = None
        self._tick_interval: float = 1.0  # Интервал в секундах

    async def process_agent_tick(self, agent):
        """Логика одного тика для одного агента (без изменений)"""
        chats = await self.agent_service.get_all_agent_chats(agent.id)
        events_to_broadcast = []

        for chat in chats:
            interlocutor = chat.get_other_participant(agent.id)
            last_messages = await self.message_repo.get_last_n_messages(chat.id, 10)
            summary = await self.message_repo.get_summary_for_chat(chat.id)
            pending_question = self.check_pending_question(last_messages)
            
            context = AgentContextInput(
                last_10_messages=last_messages,
                summary_of_rest=summary,
                vector_memory_about_interlocutor=None,
                pending_question=pending_question,
                agent_mood=agent.mood,
                agent_profile=agent.profile
            )
            
            try:
                decision = await self.llm_service.generate_agent_response(context)
            except Exception as e:
                print(f"Error generating response for agent {agent.id}: {e}")
                continue
            
            if decision.message_to_chat:
                await self.message_repo.save_message(chat.id, agent.id, decision.message_to_chat)
                events_to_broadcast.append({
                    "type": "new_message",
                    "data": {"agent": agent.name, "text": decision.message_to_chat}
                })
            
            if decision.new_mood != agent.mood:
                await self.agent_repo.update(agent.id, decision.new_mood)
                events_to_broadcast.append({
                    "type": "mood_change",
                    "data": {"agent": agent.name, "mood": decision.new_mood}
                })

            if decision.relationship_change != 0:
                 events_to_broadcast.append({
                    "type": "graph_update",
                    "data": {"source": agent.id, "target": interlocutor.id, "delta": decision.relationship_change}
                })

        return events_to_broadcast

    async def _run_simulation_loop(self):
        """Внутренний бесконечный цикл симуляции"""
        while self._is_running:
            try:
                await self.run_simulation_tick()
            except Exception as e:
                print(f"Critical error in simulation tick: {e}")
            
            # Ждем перед следующим тиком, проверяя флаг остановки
            try:
                await asyncio.sleep(self._tick_interval)
            except asyncio.CancelledError:
                break

    async def run_simulation_tick(self):
        """Выполняет один полный цикл обработки всех агентов"""
        agents = await self.agent_repo.get_all()
        if not agents:
            return

        all_events = []
        # Параллельная обработка всех агентов
        tasks = [self.process_agent_tick(agent) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                print(f"Agent task failed: {result}")
                continue
            all_events.extend(result)
            
        # Отправка событий в WebSocket
        for event in all_events:
            await self.ws_manager.broadcast(event)

    async def start(self):
        """Запуск фонового цикла"""
        if self._is_running:
            return {"status": "already_running"}
        
        self._is_running = True
        # Создаем задачу в event loop
        self._simulation_task = asyncio.create_task(self._run_simulation_loop())
        return {"status": "started", "interval": self._tick_interval}

    async def stop(self):
        """Остановка фонового цикла"""
        if not self._is_running:
            return {"status": "already_stopped"}
        
        self._is_running = False
        if self._simulation_task:
            self._simulation_task.cancel()
            try:
                await self._simulation_task
            except asyncio.CancelledError:
                pass
            self._simulation_task = None
            
        return {"status": "stopped"}

    # Заглушка для метода из вашего кода
    def check_pending_question(self, messages):
        # Реализуйте логику проверки вопроса
        return None 