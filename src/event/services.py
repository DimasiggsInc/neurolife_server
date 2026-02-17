from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.websocket.manager import manager
from src.event.models import Event
import logging
import uuid

logger = logging.getLogger(__name__)


class EventService:
    """Сервис для управления событиями мира"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_event(
        self,
        event_type: str,
        description: str,
        involved_agents: list = None,
        payload: dict = None
    ) -> Event:
        """Создать событие и уведомить клиентов"""
        event = Event(
            type=event_type,
            description=description,
            involved_agents=involved_agents or [],
            payload=payload or {},
            world_timestamp=datetime.utcnow()
        )
        
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        
        # Уведомляем всех подключенных клиентов
        await manager.broadcast_world_event({
            "event_id": event.id,
            "event_type": event_type,
            "description": description,
            "world_timestamp": event.world_timestamp.isoformat()
        })
        
        logger.info(f"Событие создано: {event_type} - {description}")
        return event
    
    async def notify_agent_mood_change(
        self,
        agent_id: str,
        old_mood: str,
        new_mood: str,
        trigger: str
    ):
        """Уведомить об изменении настроения агента"""
        await manager.broadcast_agent_update(agent_id, {
            "update_type": "mood_change",
            "old_mood": old_mood,
            "new_mood": new_mood,
            "trigger": trigger
        })
    
    async def notify_new_message(self, message_data: dict):
        """Уведомить о новом сообщении в чате"""
        # ✅ Гарантируем, что все поля существуют
        full_message_data = {
            "message_id": message_data.get("message_id", str(uuid.uuid4())),
            "sender": message_data.get("sender", "unknown"),
            "sender_id": message_data.get("sender_id"),
            "receiver_id": message_data.get("receiver_id"),
            "content": message_data.get("content", ""),
            "agent_response": message_data.get("agent_response", ""),
            "timestamp": message_data.get("timestamp", datetime.utcnow().isoformat())
        }
        
        await self.manager.broadcast_message(full_message_data)
