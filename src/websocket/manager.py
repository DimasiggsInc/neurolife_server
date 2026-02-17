from fastapi import WebSocket
from typing import List, Dict, Set
import asyncio
from datetime import datetime


class ConnectionManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        # Активные подключения
        self.active_connections: List[WebSocket] = []
        # Подключения по комнатам (для разных агентов/чатов)
        self.room_connections: Dict[str, Set[WebSocket]] = {}
        # Блокировка для потокобезопасности
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, room: str = "global"):
        """Принять подключение"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
            if room not in self.room_connections:
                self.room_connections[room] = set()
            self.room_connections[room].add(websocket)
    
    def disconnect(self, websocket: WebSocket, room: str = "global"):
        """Отключить клиента"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if room in self.room_connections:
            self.room_connections[room].discard(websocket)
    
    async def broadcast(self, message: dict, room: str = "global"):
        """Отправить сообщение всем в комнате"""
        async with self._lock:
            connections = self.room_connections.get(room, self.active_connections)
            disconnected = []
            
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # Очистка отключенных соединений
            for conn in disconnected:
                self.disconnect(conn, room)
    
    async def send_personal(self, message: dict, websocket: WebSocket):
        """Отправить сообщение конкретному клиенту"""
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)
    
    async def broadcast_event(self, event_type: str, data: dict):
        """Удобный метод для отправки событий"""
        message = {
            "type": "event",
            "event_type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(message)
    
    async def broadcast_agent_update(self, agent_id: str, data: dict):
        """Обновление состояния агента"""
        await self.broadcast_event("agent_update", {
            "agent_id": agent_id,
            **data
        })
    
    async def broadcast_message(self, message_data: dict):
        """Новое сообщение в чате"""
        message = {
            "type": "message_received",  # ✅ Явно указываем тип
            "event_type": "new_message",
            "data": {
                "message_id": message_data.get("message_id"),
                "sender": message_data.get("sender"),
                "sender_id": message_data.get("sender_id"),
                "receiver_id": message_data.get("receiver_id"),
                "content": message_data.get("content"),
                "agent_response": message_data.get("agent_response"),
                "timestamp": message_data.get("timestamp", datetime.utcnow().isoformat())
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_world_event(self, event_data: dict):
        """Событие мира (найден клад, изменилась погода и т.д.)"""
        await self.broadcast_event("world_event", event_data)

    async def broadcast_agent_action(self, agent_id: str, action_data: dict):
        """Отправить действие агента всем клиентам"""
        await self.broadcast_event("agent_action", {
            "agent_id": agent_id,
            **action_data
        })

# Глобальный экземпляр
manager = ConnectionManager()
