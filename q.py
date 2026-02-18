import os
import asyncio
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Set

# Импорты ваших моделей и сервисов
from src.llm.schemas import Message, MessageMemoryView
from src.llm.schemas import AgentContextInput
from src.llm.services import LLMService

import json
from typing import Dict, Any, Set
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
import asyncio
from datetime import datetime

from src.memory.models import Memory
from src.memory.repositories import MemoryRepository


from src.message.interfaces import MessageRepositoryPort
from src.message.repositories import MessageRepository
from src.message.dependencies import get_message_repository

from src.current_mood.models import CurrentMood
from src.current_mood.repositories import CurrentMoodRepository

from src.message.models import Message as Message_

from fastapi import Depends
from src.database import get_session, AsyncSession

from uuid import uuid4



app = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
)

# ==============================================================================
# ПРЕДПОЛАГАЕМЫЕ ИМПОРТЫ МОДЕЛЕЙ БАЗЫ ДАННЫХ (SQLAlchemy)
# Вам нужно создать эти классы на основе вашей схемы
# ==============================================================================
# from src.db.models import DBAgent, DBChat, DBMessage, DBMemory, DBRelationship, DBWorldState, DBEvent
# from src.db.session import get_db_session 

# ==================== WEBSOCKET MANAGER ====================

class ConnectionManager:
    def __init__(self):
        # Храним активные подключения
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"[WS] Client connected. Total clients: {len(self.active_connections)}")
        
        # Отправляем приветственное сообщение
        await websocket.send_json({
            "type": "system",
            "message": "Connected to Simulation Stream",
            "timestamp": datetime.utcnow().isoformat()
        })

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        print(f"[WS] Client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, data: Dict[str, Any]):
        if not self.active_connections:
            return
        
        message = json.dumps(data)
        # Отправляем всем подключенным клиентам
        # copy() используем, чтобы избежать изменения множества во время итерации, 
        # если кто-то отключится в процессе отправки
        disconnected_clients = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Если отправка не удалась (клиент отключился), помечаем его
                disconnected_clients.append(connection)
        
        # Очищаем список отключившихся
        for client in disconnected_clients:
            self.disconnect(client)

manager = ConnectionManager()


# ==================== ENDPOINTS ====================
@app.websocket("/events")
async def websocket_endpoint(
    websocket: WebSocket,
    session: AsyncSession = Depends(get_session)
):
    await manager.connect(websocket)
    try:
        while True:
            # Ожидаем сообщения от клиента (если нужно)
            # В оригинале сообщение просто игнорировалось (pass), но соединение держалось
            data = await websocket.receive_text()
            
            # Здесь можно добавить логику обработки входящих сообщений
            # Например: await manager.manager.broadcast({"type": "echo", "data": data})
            pass 
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"[WS] Error: {e}")
        manager.disconnect(websocket)

# ==================== STARTUP EVENT ====================

@app.on_event("startup")
async def startup_event():
    print("WebSocket Server started on ws://localhost:8000/ws")
    # Запускаем симуляцию в фоновом режиме, чтобы не блокировать сервер
    asyncio.create_task(simulation_loop())

# ==================== FILE LOGGING ====================

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE_PATH = os.path.join(
    LOG_DIR,
    f"simulation_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt"
)

_log_file = open(LOG_FILE_PATH, "w", encoding="utf-8")

def log_print(*args, sep=" ", end="\n"):
    text = sep.join(str(a) for a in args) + end
    print(text, end="")
    _log_file.write(text)
    _log_file.flush()

# ==================== SETTINGS ====================

PARALLEL_AGENTS = os.getenv("PARALLEL_AGENTS", "0") == "1"

# ==================== MOCK DATA / DB INIT ====================

# В реальном коде здесь будет запрос к БД: session.query(DBAgent).all()
agents = [
    {"id": "1", "name": "Алекс", "mood": "neutral", "personality": "дружелюбный"},
    {"id": "2", "name": "Борис", "mood": "happy", "personality": "саркастичный"},
    {"id": "3", "name": "Вика", "mood": "sad", "personality": "серьезный"},
]

chats = [
    {"id": "c1", "participants": ("Алекс", "Борис"), "type": "dm"},
    {"id": "c2", "participants": ("Вика", "Борис"), "type": "dm"},
    {"id": "c3", "participants": ("Алекс", "Вика"), "type": "dm"},
]

MESSAGES: List[Message] = []
MEMORY_VIEWS: List[MessageMemoryView] = []

_next_message_id = 1
_next_view_id = 1
_world_ts = 1

chat_messages: Dict[str, List[int]] = {c["id"]: [] for c in chats}
viewed_by_agent: Dict[str, set] = {a["name"]: set() for a in agents}

# ==================== HELPERS ====================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def get_agent(name: str) -> Dict:
    for a in agents:
        if a["name"] == name:
            return a
    raise KeyError(name)

def get_agent_chats(agent_name: str) -> List[Dict]:
    return [c for c in chats if agent_name in c["participants"]]

def get_other_participant(chat: Dict, agent_name: str) -> str:
    return [p for p in chat["participants"] if p != agent_name][0]

async def add_message(session: AsyncSession, chat_id: str, sender_name: str, content: str, is_system_event: bool = False) -> Message:
    global _next_message_id, _world_ts
    
    # 1. Create the internal Message object
    m = Message(
        id=_next_message_id,
        chat_id=chat_id,
        sender_name=sender_name,
        content=content,
        created_at=utc_now_iso(),
        world_timestamp=_world_ts,
        is_system_event=is_system_event,
        embedding=None,
    )
    _next_message_id += 1
    _world_ts += 1
    MESSAGES.append(m)
    chat_messages[chat_id].append(m.id)


    message_repo = MessageRepository(session)

    fake_sender_uuid = uuid4()

    _m = await message_repo.add(
        Message_(
            id=uuid4(),
            sender_id=fake_sender_uuid, 
            chat_id=fake_sender_uuid,
            content=m.content,
            created_at=datetime.now(timezone.utc),
            is_system_event=m.is_system_event,
        )
    )
    await session.commit()
    await session.refresh(_m)
    print(f"[DB] Saved message: {_m}")

    # 4. Broadcast
    asyncio.create_task(manager.broadcast({
        "type": "new_message",
        "data": {
            "id": m.id,
            "chat_id": chat_id,
            "sender": sender_name,
            "content": content,
            "timestamp": m.created_at,
            "is_system": is_system_event
        }
    }))
    
    return m

def get_last_n_messages_text(chat_id: str, n: int = 10) -> List[str]:
    ids = chat_messages[chat_id][-n:]
    out = []
    for mid in ids:
        m = next(x for x in MESSAGES if x.id == mid)
        out.append(f"{m.sender_name}: {m.content}")
    return out

def pending_question(last_msgs: List[str]) -> Optional[str]:
    return last_msgs[-1] if last_msgs and "?" in last_msgs[-1] else None

def pick_latest_unscored_incoming_message(agent_name: str, chat_id: str) -> Optional[Message]:
    for mid in reversed(chat_messages[chat_id]):
        if mid in viewed_by_agent[agent_name]:
            continue
        m = next(x for x in MESSAGES if x.id == mid)
        if m.is_system_event:
            continue
        if m.sender_name == agent_name:
            continue
        return m
    return None

async def create_memory_view(session: AsyncSession, agent_name: str, message_id: int, importance: float) -> MessageMemoryView:
    global _next_view_id
    v = MessageMemoryView(
        id=_next_view_id,
        agent_name=agent_name,
        message_id=message_id,
        importance=float(max(0.0, min(1.0, importance))),
        created_at=utc_now_iso(),
    )
    _next_view_id += 1
    MEMORY_VIEWS.append(v)
    viewed_by_agent[agent_name].add(message_id)
    
    memory_repo = MemoryRepository(session)

    fake_uuid = uuid4()

    _v = await memory_repo.add(
        Memory(
            id=uuid4(),
            agent_id=fake_uuid,
            content="",
            importance=float(max(0.0, min(1.0, importance))),
            created_at=datetime.now(timezone.utc),
            is_summarized=False
        )
    )
    await session.commit()
    await session.refresh(_v)
    print(f"[DB] Saved memory: {_v}")


    asyncio.create_task(manager.broadcast({
        "type": "memory_update",
        "data": {
            "agent": agent_name,
            "message_id": message_id,
            "importance": v.importance,
            "timestamp": v.created_at
        }
    }))
    
    return v

def build_context(agent: Dict, chat: Dict, incoming_to_score: Optional[Message]) -> AgentContextInput:
    last = get_last_n_messages_text(chat["id"], 10)

    if incoming_to_score:
        score_block = (
            "ОЦЕНИВАЕМОЕ ВХОДЯЩЕЕ СООБЩЕНИЕ (выставь memory_importance для него):\n"
            f"{incoming_to_score.sender_name}: {incoming_to_score.content}\n"
        )
    else:
        score_block = (
            "ОЦЕНИВАЕМОЕ ВХОДЯЩЕЕ СООБЩЕНИЕ:\n"
            "Нет новых входящих сообщений для оценки. memory_importance выставь 0.0.\n"
        )

    return AgentContextInput(
        last_10_messages=last,
        summary_of_rest=score_block,
        vector_memory_about_interlocutor="",
        pending_question=pending_question(last),
        agent_mood=agent["mood"],
        agent_profile={
            "name": agent["name"],
            "personality": agent["personality"],
            "id": agent["id"],
        },
    )

# ==================== LLM ====================

_llm = LLMService()

async def llm_agent_tick(ctx: AgentContextInput) -> Dict:
    out = await _llm.generate_agent_response(ctx)
    return {
        "message_to_chat": out.message_to_chat,
        "new_mood": out.new_mood,
        "relationship_affinity": float(out.relationship_affinity),
        "memory_importance": float(out.memory_importance or 0.0),
    }

# ==================== SIMULATION ====================

async def process_agent_tick(session: AsyncSession, agent: Dict) -> List[Dict]:
    events: List[Dict] = []
    agent_name = agent["name"]

    for chat in get_agent_chats(agent_name):
        chat_id = chat["id"]
        other = get_other_participant(chat, agent_name)

        incoming = pick_latest_unscored_incoming_message(agent_name, chat_id)
        ctx = build_context(agent, chat, incoming)

        decision = await llm_agent_tick(ctx)

        log_print(
            f"AGENT={agent_name} CHAT={chat_id} WITH={other} | "
            f"speak={'yes' if decision['message_to_chat'] else 'no'}"
        )

        # 1) сохранить оценку важности входящего DB SAVE
        if incoming:
            v = await create_memory_view(session, agent_name, incoming.id, decision["memory_importance"])
            events.append({
                "type": "memory_view_created",
                "data": {"agent": agent_name, "message_id": incoming.id, "importance": v.importance, "chat_id": chat_id}
            })

        # 2) mood update
        if decision["new_mood"] != agent["mood"]:
            old = agent["mood"]
            agent["mood"] = decision["new_mood"]
            events.append({
                "type": "mood_change",
                "data": {"agent": agent_name, "old_mood": old, "mood": agent["mood"]}
            })
            print("\n"*10)
            print(agent["mood"])
            print("\n"*10)

            # mood_repo = CurrentMoodRepository(session)
            # from src.agent.utils import generate_color

            # from src.agent.repositories import AgentRepository

            # agent_repo = AgentRepository(session)

            # agent_repo.get_by_name()

            
            # joy = 1 if agent["mood"] == "happy" else 0
            # sadness = 1 if agent["mood"] == "sad" else 0
            # anger = 1 if agent["mood"] == "anger" else 0
            # fear = 1 if agent["mood"] == "fear" else 0

            # _v = await mood_repo.update(
            #     CurrentMood(
            #         joy = joy,
            #         sadness = sadness,
            #         anger = anger,
            #         fear = fear,
            #         color=generate_color(sadness, joy, anger, fear),
            #         updated_at=datetime.now(timezone.utc)
            #     )
            # )
            # await session.commit()
            # await session.refresh(_v)
            # print(f"[DB] Saved message: {_v}")
            
            # ---------------------------------------------------------
            # >>> DB SAVE: TABLE 'Agent' (или 'current_mood') <<<
            # ---------------------------------------------------------
            # Обновляем текущее настроение агента.
            # В схеме есть таблица current_mood, связанная с Agent.
            # Либо обновляем поле mood_level в Agent, либо создаем новую запись в current_mood.
            #
            # Пример (псевдокод):
            # db_agent = session.query(DBAgent).filter_by(name=agent_name).first()
            # db_agent.mood_level = decision['new_mood'] # или обновить связь current_mood_id
            # session.commit()
            # ---------------------------------------------------------

            asyncio.create_task(manager.broadcast({
                "type": "mood_change",
                "data": {
                    "agent": agent_name,
                    "new_mood": agent["mood"],
                    "old_mood": old
                }
            }))

        # 3) agent speaks
        if decision["message_to_chat"]:
            
            m = await add_message(session, chat_id, agent_name, decision["message_to_chat"], is_system_event=False)
            events.append({
                "type": "new_message",
                "data": {"chat_id": chat_id, "sender": agent_name, "message_id": m.id}
            })
            
            # ---------------------------------------------------------
            # >>> DB SAVE: TABLE 'Relationship' <<<
            # ---------------------------------------------------------
            # Если было взаимодействие, нужно обновить отношения между агентами.
            # Найти запись Relationship где (agent_a=Alex, agent_b=Boris) или наоборот.
            # Увеличить interaction_count, обновить affinity (на основе decision['relationship_change']).
            #
            # Пример (псевдокод):
            # rel = session.query(DBRelationship).filter(
            #     or_(
            #         and_(DBRelationship.agent_a_id == agent_id, DBRelationship.agent_b_id == other_id),
            #         and_(DBRelationship.agent_a_id == other_id, DBRelationship.agent_b_id == agent_id)
            #     )
            # ).first()
            # if not rel:
            #     rel = DBRelationship(agent_a_id=agent_id, agent_b_id=other_id, affinity=0.5)
            #     session.add(rel)
            # 
            # rel.interaction_count += 1
            # rel.affinity += decision['relationship_change']
            # rel.last_interaction_timestamp = datetime.now()
            # session.commit()
            # ---------------------------------------------------------

    return events

async def run_simulation_tick(session: AsyncSession, tick_number: int):
    # ---------------------------------------------------------
    # >>> DB SAVE: TABLE 'World_state' <<<
    # ---------------------------------------------------------
    # В начале тика обновляем глобальное состояние мира.
    # Увеличиваем time_speed или просто обновляем updated_at.
    #
    # Пример (псевдокод):
    # world_state = session.query(DBWorldState).first()
    # if not world_state:
    #     world_state = DBWorldState(time_speed=1, simulation_paused=False)
    #     session.add(world_state)
    # world_state.updated_at = datetime.now()
    # session.commit()
    # ---------------------------------------------------------

    log_print("\n" + "=" * 60)
    log_print(f"TICK #{tick_number} | {datetime.now(timezone.utc).strftime('%H:%M:%S')}")
    log_print("=" * 60 + "\n")

    all_events: List[Dict] = []

    for a in agents:
        log_print(f"{a['name']} (mood={a['mood']})")
    log_print("-" * 140)

    if PARALLEL_AGENTS:
        results = await asyncio.gather(*(process_agent_tick(session, a) for a in agents))
        for evs in results:
            all_events.extend(evs)
    else:
        for a in agents:
            evs = await process_agent_tick(session, a)
            all_events.extend(evs)

    mem_created = sum(1 for e in all_events if e["type"] == "memory_view_created")
    new_msgs = sum(1 for e in all_events if e["type"] == "new_message")
    
    # ---------------------------------------------------------
    # >>> DB SAVE: TABLE 'Events' <<<
    # ---------------------------------------------------------
    # Логируем системные события тика в таблицу Events.
    #
    # Пример (псевдокод):
    # for event in all_events:
    #     db_event = DBEvent(
    #         type=event['type'],
    #         # можно сохранить JSON данных события в поле details, если оно есть
    #     )
    #     session.add(db_event)
    # session.commit()
    # ---------------------------------------------------------

    await manager.broadcast({
        "type": "tick_complete",
        "data": {
            "tick": tick_number,
            "new_messages_count": new_msgs,
            "memory_views_count": mem_created,
            "agents_status": {a['name']: a['mood'] for a in agents}
        }
    })

    log_print(f"\nEVENTS: memory_views={mem_created}, new_messages={new_msgs}")
    log_print("\n" + "=" * 60 + "\n")

# ==================== MAIN ====================

async def simulation_loop():
    log_print("Initializing Simulation Loop...")
    
    # FIX: Manually acquire the session context. 
    # We assume get_session() is defined as: async def get_session() -> AsyncGenerator[AsyncSession, None]:
    try:
        async for session in get_session():
            try:
                # Now 'session' is a real AsyncSession object, not a Depends object
                log_print("[DB] Session acquired successfully.")
                
                # Initial Messages
                await add_message(session, "c1", "Борис", "Привет, Алекс!")
                await add_message(session, "c1", "Алекс", "Привет, Борис! Как дела?")

                log_print("START SIMULATION...")
                
                for t in range(10):
                    await run_simulation_tick(session, t + 1)
                    await asyncio.sleep(2) 

                log_print("SIMULATION DONE")
            finally:
                # Ensure session is closed
                await session.close()
                log_print("[DB] Session closed.")
            break # Remove this break if you want an infinite loop, keep it for testing
    except Exception as e:
        log_print(f"[ERROR] Simulation loop failed: {e}")
        import traceback
        log_print(traceback.format_exc())

# import uvicorn
# if __name__ == "__main__":
#     # Запуск сервера через uvicorn
#     # host="0.0.0.0" делает сервер доступным не только локально, но и по сети (если нужно)
#     # port=8000 - стандартный порт
#     uvicorn.run(app, host="0.0.0.0", port=8000)
