from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from src.websocket.manager import manager
from src.agent.schemas import UserMessageToAgent
from src.event.services import EventService
from src.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket для получения событий в реальном времени
    Клиент получает: новые сообщения, изменения настроения, события мира
    """
    await manager.connect(websocket)
    
    try:
        # Отправляем приветственное сообщение
        await manager.send_personal({
            "type": "connection_established",
            "message": "Подключено к симулятору агентов",
            "timestamp": "now"
        }, websocket)
        
        # Слушаем сообщения от клиента
        while True:
            data = await websocket.receive_json()
            await handle_client_message(websocket, data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Клиент отключился от WebSocket")
    except Exception as e:
        logger.error(f"Ошибка WebSocket: {e}")
        manager.disconnect(websocket)


@router.websocket("/agent/{agent_id}")
async def websocket_agent_room(websocket: WebSocket, agent_id: str):
    """
    WebSocket для конкретной комнаты агента
    Клиент получает события только от конкретного агента
    """
    await manager.connect(websocket, room=f"agent_{agent_id}")
    
    try:
        await manager.send_personal({
            "type": "room_joined",
            "agent_id": agent_id,
            "message": f"Вы подписаны на обновления агента {agent_id}"
        }, websocket)
        
        while True:
            data = await websocket.receive_json()
            await handle_client_message(websocket, data, agent_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room=f"agent_{agent_id}")
        logger.info(f"Клиент отключился от комнаты агента {agent_id}")


async def handle_client_message(
    websocket: WebSocket,
    data: dict,
    agent_id: str = None
):
    """Обработка сообщений от клиента"""
    message_type = data.get("type")
    
    if message_type == "user_message":
        # Пользователь отправляет сообщение агенту
        await handle_user_message(websocket, data, agent_id)
    
    elif message_type == "world_event":
        # Пользователь создает событие мира
        await handle_world_event(websocket, data)
    
    elif message_type == "ping":
        # Проверка соединения
        await manager.send_personal({"type": "pong"}, websocket)
    
    else:
        await manager.send_personal({
            "type": "error",
            "message": f"Неизвестный тип сообщения: {message_type}"
        }, websocket)


async def handle_user_message(websocket: WebSocket, data: dict, agent_id: str = None):
    """Пользователь отправляет сообщение агенту"""
    from src.agent.services import AgentService
    from src.database import get_session
    
    content = data.get("content")
    target_agent_id = data.get("agent_id") or agent_id
    
    if not content or not target_agent_id:
        await manager.send_personal({
            "type": "error",
            "message": "Требуется content и agent_id"
        }, websocket)
        return
    
    # ✅ Отправляем подтверждение получения
    await manager.send_personal({
        "type": "message_received",
        "data": {
            "agent_id": target_agent_id,
            "content": content,
            "status": "processing",
            "timestamp": datetime.utcnow().isoformat()
        }
    }, websocket)
    
    # TODO: Вызвать AgentService для обработки сообщения
    # agent_service = AgentService(...)
    # await agent_service.send_message_to_agent(target_agent_id, UserMessageToAgent(content=content))


async def handle_world_event(websocket: WebSocket, data: dict):
    """Пользователь создает событие мира"""
    event_type = data.get("event_type")  # "found_treasure", "weather_change", etc.
    description = data.get("description")
    affected_agents = data.get("affected_agents", [])  # список ID агентов
    
    # Транслируем событие всем подключенным клиентам
    await manager.broadcast_world_event({
        "event_type": event_type,
        "description": description,
        "affected_agents": affected_agents,
        "created_by": "user"
    })
    
    # TODO: Сохранить событие в БД и обработать агентами
