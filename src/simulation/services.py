import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.websocket.manager import manager
from src.agent.repositories import AgentRepository
from src.event.services import EventService

logger = logging.getLogger(__name__)


class SimulationService:
    """Сервис для управления симуляцией мира агентов"""
    
    def __init__(
        self,
        session: AsyncSession,
        agent_repository: AgentRepository,
        event_service: EventService
    ):
        self.session = session
        self.agent_repository = agent_repository
        self.event_service = event_service
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.interval_seconds = 5  # Интервал обновления
    
    async def start(self):
        """Запустить фоновую симуляцию"""
        if self.is_running:
            logger.warning("Симуляция уже запущена")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._simulation_loop())
        logger.info(f"🚀 Симуляция запущена (интервал: {self.interval_seconds}с)")
    
    async def stop(self):
        """Остановить симуляцию"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ Симуляция остановлена")
    
    async def _simulation_loop(self):
        """Основной цикл симуляции"""
        while self.is_running:
            try:
                await self._tick()
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле симуляции: {e}")
                await asyncio.sleep(self.interval_seconds)
    
    async def _tick(self):
        """Один тик симуляции"""
        # 1. Получаем всех активных агентов
        agents = await self.agent_repository.get_all(active_only=True)
        
        if not agents:
            return
        
        # 2. Для каждого агента генерируем действие
        for agent in agents:
            action = await self._generate_agent_action(agent)
            
            # 3. Отправляем событие клиентам
            await manager.broadcast_event("agent_action", {
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "action": action,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # 4. С небольшой вероятностью создаем событие в мире
            if hash(str(agent.id) + str(datetime.utcnow().second)) % 10 == 0:
                await self._create_random_event(agent)
        
        logger.debug(f"📊 Тик симуляции: {len(agents)} агентов")
    
    async def _generate_agent_action(self, agent) -> dict:
        """Сгенерировать случайное действие для агента"""
        import random
        
        actions = [
            {"type": "thinking", "text": "размышляет о жизни"},
            {"type": "exploring", "text": "исследует окрестности"},
            {"type": "resting", "text": "отдыхает"},
            {"type": "planning", "text": "строит планы"},
            {"type": "observing", "text": "наблюдает за миром"},
            {"type": "chatting", "text": "болтает с другими агентами"},
            {"type": "learning", "text": "учится новому"},
            {"type": "creating", "text": "творит что-то интересное"},
        ]
        
        # Можно учесть настроение агента для выбора действия
        action = random.choice(actions)
        
        return {
            "type": action["type"],
            "description": f"{agent.name} {action['text']}",
            "emoji": self._get_action_emoji(action["type"])
        }
    
    def _get_action_emoji(self, action_type: str) -> str:
        """Получить эмодзи для типа действия"""
        emojis = {
            "thinking": "🤔",
            "exploring": "🗺️",
            "resting": "😴",
            "planning": "📋",
            "observing": "👀",
            "chatting": "💬",
            "learning": "📚",
            "creating": "🎨"
        }
        return emojis.get(action_type, "🤖")
    
    async def _create_random_event(self, agent):
        """Создать случайное событие в мире"""
        import random
        
        events = [
            ("found_item", "Нашел интересный предмет"),
            ("met_agent", "Встретил другого агента"),
            ("discovered_place", "Открыл новое место"),
            ("had_idea", "Пришла гениальная идея"),
            ("felt_emotion", "Испытал сильные эмоции"),
        ]
        
        event_type, description = random.choice(events)
        
        await self.event_service.create_event(
            event_type=event_type,
            description=f"{agent.name}: {description}",
            involved_agents=[str(agent.id)]
        )
    
    def set_interval(self, seconds: int):
        """Изменить интервал симуляции"""
        self.interval_seconds = max(1, min(60, seconds))  # От 1 до 60 секунд
        logger.info(f"⏱️ Интервал симуляции изменен на {self.interval_seconds}с")
