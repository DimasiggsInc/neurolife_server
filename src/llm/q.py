import os
import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from models import Message, MessageMemoryView

from schemas import AgentContextInput
from services import LLMService


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

# ==================== MOCK DATA ====================

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

# "Таблицы" в памяти
MESSAGES: List[Message] = []
MEMORY_VIEWS: List[MessageMemoryView] = []

# индексы/счетчики
_next_message_id = 1
_next_view_id = 1
_world_ts = 1

# быстрые индексы
# chat_messages[chat_id] -> list[message_id]
chat_messages: Dict[str, List[int]] = {c["id"]: [] for c in chats}

# viewed_by_agent[agent_name] -> set(message_id) (какие message_id агент уже оценил)
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


def add_message(chat_id: str, sender_name: str, content: str, is_system_event: bool = False) -> Message:
    global _next_message_id, _world_ts
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
    """
    Берём самое свежее сообщение в чате:
    - sender != agent
    - не system_event
    - агент ещё НЕ оценивал (нет записи в viewed_by_agent)
    """
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


def create_memory_view(agent_name: str, message_id: int, importance: float) -> MessageMemoryView:
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
        summary_of_rest=score_block,               # ← сюда кладём “что оценить”
        vector_memory_about_interlocutor="",      # позже подключишь
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
        "relationship_change": float(out.relationship_change),
        "memory_importance": float(out.memory_importance or 0.0),
    }


# ==================== SIMULATION ====================

async def process_agent_tick(agent: Dict) -> List[Dict]:
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
            f"last10={len(ctx.last_10_messages)} | "
            f"speak={'yes' if decision['message_to_chat'] else 'no'} | "
            f"rel={decision['relationship_change']:+.2f} | "
            f"memory_importance(incoming)={decision['memory_importance']:.3f}"
        )
        log_print("----- INCOMING TO SCORE -----")
        log_print(ctx.summary_of_rest)
        log_print("-----------------------------")

        # 1) сохранить оценку важности входящего (если было что оценивать)
        if incoming:
            v = create_memory_view(agent_name, incoming.id, decision["memory_importance"])
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

        # 3) agent speaks? → создаём Message в журнале мира
        if decision["message_to_chat"]:
            m = add_message(chat_id, agent_name, decision["message_to_chat"], is_system_event=False)
            events.append({
                "type": "new_message",
                "data": {"chat_id": chat_id, "sender": agent_name, "message_id": m.id}
            })

    return events


async def run_simulation_tick(tick_number: int):
    log_print("\n" + "=" * 60)
    log_print(f"TICK #{tick_number} | {datetime.now(timezone.utc).strftime('%H:%M:%S')} (world_ts={_world_ts})")
    log_print("=" * 60 + "\n")

    all_events: List[Dict] = []

    for a in agents:
        log_print(f"{a['name']} (mood={a['mood']}) | {a['personality']}")
    log_print("-" * 140)

    if PARALLEL_AGENTS:
        results = await asyncio.gather(*(process_agent_tick(a) for a in agents))
        for evs in results:
            all_events.extend(evs)
    else:
        for a in agents:
            evs = await process_agent_tick(a)
            all_events.extend(evs)

    # summary
    mem_created = sum(1 for e in all_events if e["type"] == "memory_view_created")
    new_msgs = sum(1 for e in all_events if e["type"] == "new_message")
    mood_changes = sum(1 for e in all_events if e["type"] == "mood_change")

    log_print(f"\nEVENTS: memory_views={mem_created}, new_messages={new_msgs}, mood_changes={mood_changes}, total={len(all_events)}")
    log_print("\n" + "=" * 60 + "\n")


def dump_all():
    log_print("\n\n==================== DUMP: MESSAGES (WORLD LOG) ====================")
    for m in MESSAGES:
        log_print(asdict(m))

    log_print("\n\n==================== DUMP: MESSAGE_MEMORY_VIEW =====================")
    for v in MEMORY_VIEWS:
        log_print(asdict(v))

    log_print("\n\n==================== DUMP: VIEWED_BY_AGENT =========================")
    for a, s in viewed_by_agent.items():
        log_print(a, sorted(list(s)))

    log_print("\n\n==================== DUMP: CHAT_INDEX ==============================")
    for cid, mids in chat_messages.items():
        log_print(cid, mids)


# ==================== MAIN ====================

async def main():
    # стартовые сообщения в мир-лог
    add_message("c1", "Борис", "Привет, Алекс!")
    add_message("c1", "Алекс", "Привет, Борис! Как дела?")

    log_print("START (БЕЗ БД, НО СО СХОЖЕЙ СХЕМОЙ)")
    log_print(f"Agents: {len(agents)} | Chats: {len(chats)} | Messages(start): {len(MESSAGES)}")
    log_print(f"LLM endpoint: {os.getenv('FREEQWEN_BASE_URL', 'http://localhost:3264/api')}")
    log_print(f"LLM model: {os.getenv('FREEQWEN_MODEL', 'qwen3-omni-flash')}")
    log_print(f"LOG FILE: {LOG_FILE_PATH}\n")

    for t in range(6):
        await run_simulation_tick(t + 1)
        await asyncio.sleep(1)

    log_print("DONE\n")
    dump_all()

    log_print(f"\nLogs saved: {LOG_FILE_PATH}")
    _log_file.close()


if __name__ == "__main__":
    asyncio.run(main())
