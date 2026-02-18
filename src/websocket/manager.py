from fastapi import WebSocket
from typing import Dict, Set, Any
import asyncio
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Менеджер WebSocket соединений.
    Отвечает только за поддержку соединений и рассылку сообщений.
    Не содержит бизнес-логики или работы с БД.
    """
    def __init__(self):
        # Активные подключения (глобальные)
        self.active_connections: Set[WebSocket] = set()
        # Подключения по комнатам (агенты, чаты)
        self.room_connections: Dict[str, Set[WebSocket]] = {}
        # Блокировка для потокобезопасности операций с коллекциями
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, room: str = "global") -> None:
        """Принять новое подключение и зарегистрировать в комнате"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
            if room not in self.room_connections:
                self.room_connections[room] = set()
            self.room_connections[room].add(websocket)
        
        logger.info(f"[WS] Client connected. Room: {room}. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, room: str = "global") -> None:
        """Отключить клиента и убрать из списков"""
        # Используем discard, чтобы не вызывать ошибку, если элемента нет
        if websocket in self.active_connections:
            self.active_connections.discard(websocket)
        
        if room in self.room_connections:
            self.room_connections[room].discard(websocket)
            
        logger.info(f"[WS] Client disconnected. Room: {room}. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: dict, room: str = "global") -> None:
        """
        Отправить сообщение всем подключенным клиентам в комнате.
        Автоматически очищает список от отключившихся клиентов.
        """
        async with self._lock:
            # Выбираем целевую группу подключений
            connections = self.room_connections.get(room, self.active_connections)
            # Копируем множество, чтобы безопасно изменять оригинал во время итерации
            active_conns = connections.copy()
        
        disconnected_clients = []

        for connection in active_conns:
            try:
                await connection.send_json(message)
            except Exception as e:
                # Если отправка не удалась, клиент скорее всего отключился
                logger.warning(f"[WS] Failed to send to client, marking for disconnect: {e}")
                disconnected_clients.append(connection)

        # Очищаем отключившиеся соединения вне цикла итерации
        if disconnected_clients:
            async with self._lock:
                for client in disconnected_clients:
                    self.disconnect(client, room)

    async def send_personal(self, message: dict, websocket: WebSocket) -> None:
        """Отправить сообщение конкретному клиенту"""
        try:
            await websocket.send_json(message)
        except Exception:
            # Если не удалось отправить, удаляем из менеджера
            self.disconnect(websocket)

    async def broadcast_event(self, event_type: str, data: Dict[str, Any], room: str = "global") -> None:
        """Удобный метод для отправки структурированных событий"""
        message = {
            "type": "event",
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.broadcast(message, room)

    async def broadcast_agent_update(self, agent_id: str, data: Dict[str, Any]) -> None:
        """Обновление состояния агента (рассылка в комнату агента)"""
        await self.broadcast_event("agent_update", {
            "agent_id": agent_id,
            **data
        }, room=f"agent_{agent_id}")

    async def broadcast_message(self, message_data: Dict[str, Any]) -> None:
        """Новое сообщение в чате (глобальная рассылка или по комнате чата)"""
        message = {
            "type": "message_received",
            "event_type": "new_message",
            "data": {
                "message_id": str(message_data.get("id")),
                "sender": message_data.get("sender"),
                "sender_id": str(message_data.get("sender_id")),
                "content": message_data.get("content"),
                "timestamp": message_data.get("created_at", datetime.now(timezone.utc).isoformat())
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        # Можно отправлять в конкретную комнату чата, если есть chat_id
        chat_id = message_data.get("chat_id")
        room = f"chat_{chat_id}" if chat_id else "global"
        await self.broadcast(message, room)

    async def broadcast_world_event(self, event_data: Dict[str, Any]) -> None:
        """Событие мира (найден клад, изменилась погода и т.д.)"""
        await self.broadcast_event("world_event", event_data)

# Глобальный экземпляр менеджера
manager = ConnectionManager()