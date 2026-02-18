from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from uuid import uuid4
import logging

from src.websocket.manager import manager
from src.database import get_session
from src.message.repositories import MessageRepository
from src.message.models import Message as MessageModel
# Предполагаем наличие репозитория событий, аналогично сообщениям
from src.event.repositories import EventRepository
from src.event.models import Event as EventModel
from src.agent.repositories import AgentRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

@router.websocket("/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket для получения событий в реальном времени.
    Клиент получает: новые сообщения, изменения настроения, события мира.
    """
    # Подключаем к глобальной комнате
    await manager.connect(websocket, room="global")
    
    # Получаем сессию БД для этого подключения (или будем создавать новую на каждое сообщение)
    # Для долгоживущих соединений лучше создавать сессию на каждое действие, 
    # чтобы не держать транзакцию открытой вечно.
    
    try:
        await manager.send_personal({
            "type": "connection_established",
            "message": "Подключено к симулятору агентов",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, websocket)
        
        while True:
            # Получаем сессию для обработки входящего сообщения
            async for session in get_session():
                try:
                    data = await websocket.receive_json()
                    await handle_client_message(websocket, data, session)
                finally:
                    await session.close()
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket, room="global")
        logger.info("Клиент отключился от WebSocket /events")
    except Exception as e:
        logger.error(f"Ошибка WebSocket /events: {e}", exc_info=True)
        manager.disconnect(websocket, room="global")

@router.websocket("/agent/{agent_id}")
async def websocket_agent_room(websocket: WebSocket, agent_id: str):
    """
    WebSocket для конкретной комнаты агента.
    Клиент получает события только от конкретного агента.
    """
    room_name = f"agent_{agent_id}"
    await manager.connect(websocket, room=room_name)
    
    try:
        await manager.send_personal({
            "type": "room_joined",
            "agent_id": agent_id,
            "message": f"Вы подписаны на обновления агента {agent_id}"
        }, websocket)
        
        while True:
            async for session in get_session():
                try:
                    data = await websocket.receive_json()
                    await handle_client_message(websocket, data, session, agent_id)
                finally:
                    await session.close()
        
    except WebSocketDisconnect:
        manager.disconnect(websocket, room=room_name)
        logger.info(f"Клиент отключился от комнаты агента {agent_id}")
    except Exception as e:
        logger.error(f"Ошибка WebSocket агент {agent_id}: {e}", exc_info=True)
        manager.disconnect(websocket, room=room_name)

async def handle_client_message(
    websocket: WebSocket,
    data: dict,
    session: AsyncSession,
    agent_id: str = None
):
    """Обработка входящих сообщений от клиента"""
    message_type = data.get("type")
    
    if message_type == "user_message":
        await handle_user_message(websocket, data, session, agent_id)
    elif message_type == "world_event":
        await handle_world_event(websocket, data, session)
    elif message_type == "ping":
        await manager.send_personal({"type": "pong"}, websocket)
    else:
        await manager.send_personal({
            "type": "error",
            "message": f"Неизвестный тип сообщения: {message_type}"
        }, websocket)

async def handle_user_message(
    websocket: WebSocket, 
    data: dict, 
    session: AsyncSession, 
    target_agent_id: str = None
):
    """
    Пользователь отправляет сообщение агенту.
    1. Валидация.
    2. Сохранение в БД через MessageRepository.
    3. Подтверждение клиенту.
    4.Broadcast через менеджер.
    """
    content = data.get("content")
    # Если agent_id не передан в теле, берем из URL (если есть)
    agent_id = data.get("agent_id") or target_agent_id

    if not content or not agent_id:
        await manager.send_personal({
            "type": "error",
            "message": "Требуется content и agent_id"
        }, websocket)
        return

    # Проверка существования агента
    agent_repo = AgentRepository(session)
    agent = await agent_repo.get_by_id(agent_id) # Предполагаемый метод
    if not agent:
        await manager.send_personal({
            "type": "error",
            "message": f"Агент {agent_id} не найден"
        }, websocket)
        return

    try:
        # 1. Сохранение сообщения в БД
        message_repo = MessageRepository(session)
        new_message = MessageModel(
            id=uuid4(),
            sender_id=uuid4(), # ID пользователя (нужно брать из auth контекста в реальном проекте)
            chat_id=uuid4(), # ID чата (нужно определить логику чата пользователь-агент)
            content=content,
            created_at=datetime.now(timezone.utc),
            is_system_event=False
        )
        
        saved_message = await message_repo.add(new_message)
        await session.commit()
        await session.refresh(saved_message)

        # 2. Подтверждение клиенту
        await manager.send_personal({
            "type": "message_received",
            "data": {
                "agent_id": agent_id,
                "content": content,
                "status": "saved",
                "message_id": str(saved_message.id),
                "timestamp": saved_message.created_at.isoformat()
            }
        }, websocket)

        # 3. Broadcast всем подключенным (чтобы другие клиенты видели сообщение)
        await manager.broadcast_message({
            "id": saved_message.id,
            "sender": "User", # Или имя пользователя из токена
            "sender_id": new_message.sender_id,
            "content": saved_message.content,
            "created_at": saved_message.created_at,
            "chat_id": saved_message.chat_id
        })

        # 4. Триггер для реакции агента (опционально, если есть сервис агентов)
        # await agent_service.notify_new_message(agent_id, saved_message)

    except Exception as e:
        await session.rollback()
        logger.error(f"Ошибка сохранения сообщения: {e}", exc_info=True)
        await manager.send_personal({
            "type": "error",
            "message": "Не удалось сохранить сообщение"
        }, websocket)

async def handle_world_event(websocket: WebSocket, data: dict, session: AsyncSession):
    """
    Пользователь создает событие мира.
    1. Валидация.
    2. Сохранение в БД через EventRepository.
    3. Broadcast через менеджер.
    """
    event_type = data.get("event_type")
    description = data.get("description")
    affected_agents = data.get("affected_agents", [])

    if not event_type or not description:
        await manager.send_personal({
            "type": "error",
            "message": "Требуется event_type и description"
        }, websocket)
        return

    try:
        # 1. Сохранение события в БД
        event_repo = EventRepository(session)
        new_event = EventModel(
            id=uuid4(),
            event_type=event_type,
            description=description,
            created_at=datetime.now(timezone.utc),
            created_by="user" # В реальности ID пользователя
        )
        
        saved_event = await event_repo.add(new_event)
        await session.commit()
        await session.refresh(saved_event)

        # 2. Транслируем событие всем подключенным клиентам
        await manager.broadcast_world_event({
            "event_id": str(saved_event.id),
            "event_type": event_type,
            "description": description,
            "affected_agents": affected_agents,
            "created_by": "user",
            "timestamp": saved_event.created_at.isoformat()
        })

        logger.info(f"Событие мира сохранено и транслировано: {event_type}")

    except Exception as e:
        await session.rollback()
        logger.error(f"Ошибка сохранения события мира: {e}", exc_info=True)
        await manager.send_personal({
            "type": "error",
            "message": "Не удалось создать событие мира"
        }, websocket)