import base64
from typing import Optional
import uuid
from pathlib import Path
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.current_mood.schemas import AgentCurrentMood
from src.agent.interfaces import AgentRepositoryPort, AgentServicePort, ImageGeneratorPort
from src.agent.schemas import AgentCreate, AgentFullInfo, AgentList, AgentOverview
from src.agent.models import Agent

from src.speech_style.models import SpeechStyle
from src.speech_style.repositories import SpeechStyleRepository

from src.personality.models import Personality
from src.personality.repositories import PersonalityRepository

from src.current_mood.models import CurrentMood
from src.current_mood.repositories import CurrentMoodRepository

from src.message.schemas import UserMessageToAgent

from src.llm.interfaces import LLMMessage


class AgentService(AgentServicePort):
    AVATARS_DIR = Path("/server/avatars")

    def __init__(
        self,
        session: AsyncSession,
        image_generator: ImageGeneratorPort,
        agent_repository: AgentRepositoryPort,
        speech_style_repository: SpeechStyleRepository,
        personality_repository: PersonalityRepository,
        current_mood_repository: CurrentMoodRepository
    ):
        self.session = session
        self.image_generator = image_generator
        self.agent_repository = agent_repository
        self.speech_style_repository = speech_style_repository
        self.personality_repository = personality_repository
        self.current_mood_repository = current_mood_repository
        
        # ✅ Создаем директорию при инициализации
        self.AVATARS_DIR.mkdir(parents=True, exist_ok=True)

    async def create_agent(self, new_agent: AgentCreate) -> AgentFullInfo:
        # ✅ 0. Генерируем UUID заранее
        agent_uuid = uuid.uuid4()

        # 1. Создаем речевой стиль
        speech_style = SpeechStyle(
            formality=0.7,
            verbosity=0.6,
            emotional_expressiveness=0.8
        )
        speech_style = await self.speech_style_repository.add(speech_style)

        # 2. Создаем персональность
        personality = Personality(
            speech_style_id=speech_style.id,
            background=new_agent.background,
            knowledge=0.7,
            safety=0.6,
            freedom=0.5,
            extraversion=0.6
        )
        personality = await self.personality_repository.add(personality)

        # 3. Создаем настроение
        current_mood = CurrentMood(
            joy=1.0 if new_agent.mood == "joy" else 0.0,
            sadness=1.0 if new_agent.mood == "sadness" else 0.0,
            anger=1.0 if new_agent.mood == "anger" else 0.0,
            fear=1.0 if new_agent.mood == "fear" else 0.0,
            updated_at=datetime.utcnow()
        )
        current_mood = await self.current_mood_repository.add(current_mood)

        # ✅ 4. Генерируем аватар с UUID в имени
        avatar_filename = f"{agent_uuid}.png"  # ← UUID вместо имени
        avatar_url = f"/avatars/{avatar_filename}"
        avatar_full_path = self.AVATARS_DIR / avatar_filename
        
        # Генерируем и сохраняем
        self.image_generator.generate(avatar_url).save(str(avatar_full_path))

        # 5. Создаем агента с заранее сгенерированным UUID
        agent = Agent(
            id=agent_uuid,  # ✅ Передаём UUID явно
            name=new_agent.name,
            personality_id=personality.id,
            current_mood_id=current_mood.id,
            current_plan=new_agent.plans,
            avatar_url=avatar_url,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        try:
            agent = await self.agent_repository.add(agent)
            await self.session.commit()
            await self.session.refresh(agent)

            return AgentFullInfo(
                id=str(agent.id),  # ✅ UUID в строковом формате
                name=agent.name,
                avatar_url=agent.avatar_url,
                mood={"category": new_agent.mood, "valence": 0.5},
                current_plan=new_agent.plans,
                created_at=agent.created_at.isoformat() + "Z"
            )
            
        except IntegrityError as e:
            await self.session.rollback()
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            
            if 'agent_name_key' in error_msg or 'name' in error_msg:
                # ✅ Удаляем аватар при ошибке (чтобы не было мусора)
                if avatar_full_path.exists():
                    avatar_full_path.unlink()
                raise ValueError(f"Agent with name '{new_agent.name}' already exists")
            else:
                raise ValueError(f"Database integrity error: {error_msg}")
                
        except SQLAlchemyError as e:
            await self.session.rollback()
            # ✅ Удаляем аватар при ошибке
            if avatar_full_path.exists():
                avatar_full_path.unlink()
            raise ValueError(f"Database error during agent creation: {str(e)}")

    async def send_message_to_agent(
    self,
    agent_id: str,
    user_message: UserMessageToAgent
) -> dict:
        """Пользователь отправляет сообщение агенту"""
        # 1. Получаем агента
        agent = await self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise ValueError(f"Агент {agent_id} не найден")
        
        # 2. Формируем промпт с учетом личности и настроения
        system_prompt = await self._build_system_prompt(agent)
        
        # 3. Отправляем в LLM
        from src.llm.interfaces import LLMMessage
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_message.content)
        ]
        
        llm_response = await self.llm_service.generate_response(messages)
        
        # 4. ✅ Формируем полную структуру сообщения
        message_data = {
            "message_id": str(uuid.uuid4()),
            "sender": "user",
            "sender_id": "user",
            "receiver_id": agent_id,
            "content": user_message.content,
            "agent_response": llm_response.content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 5. Уведомляем клиентов через WebSocket
        await self.event_service.notify_new_message(message_data)
        
        # 6. Обновляем настроение агента на основе сообщения
        await self._update_agent_mood(agent_id, user_message.content)
        
        return {
            "agent_id": agent_id,
            "user_message": user_message.content,
            "agent_response": llm_response.content,
            "status": "delivered"
        }

    async def _build_system_prompt(self, agent: Agent) -> str:
        """Построить системный промпт на основе личности агента"""
        # TODO: загрузить personality из БД
        prompt = f"""Ты — {agent.name}, автономный агент в виртуальном мире.

Твоя личность:
- Характер: добрый, любопытный, эмпатичный
- Настроение: текущее состояние

Ты общаешься с пользователем в реальном времени.
Отвечай естественно, учитывая своё настроение и личность.
"""
        return prompt

    async def _update_agent_mood(self, agent_id: str, message_content: str):
        """Обновить настроение агента на основе сообщения"""
        # 1. Анализ тональности через LLM
        sentiment = await self.llm_service.analyze_sentiment(message_content)
        
        # 2. Обновить настроение в БД
        # TODO: обновить current_mood
        
        # 3. Уведомить клиентов об изменении
        await self.event_service.notify_agent_mood_change(
            agent_id=agent_id,
            old_mood="neutral",
            new_mood="happy" if sentiment.get("positive", 0) > 0.5 else "neutral",
            trigger="user_message"
        )

    def _encode_image_to_base64(self, avatar_url: str) -> str:
        """✅ Читает файл и возвращает Base64 строку"""
        if not avatar_url:
            return self._get_default_avatar_base64()
        
        try:
            # Извлекаем имя файла из пути (например, "/avatars/uuid.png" -> "uuid.png")
            filename = avatar_url.split("/")[-1]
            file_path = self.AVATARS_DIR / filename
            
            if not file_path.exists():
                return self._get_default_avatar_base64()
            
            with open(file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            
            # Возвращаем в формате Data URI для удобного использования на фронтенде
            return f"data:image/png;base64,{encoded_string}"
            
        except Exception as e:
            print(f"⚠️ Error encoding image {avatar_url}: {e}")
            return self._get_default_avatar_base64()
    
    def _get_default_avatar_base64(self) -> str:
        """Возвращает дефолтную заглушку (серый круг) в Base64"""
        # Минимальный PNG 1x1 пиксель (серый)
        default_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        return f"data:image/png;base64,{default_png}"

    async def get_all_agents(self, limit: int = 20, active_only: bool = True) -> AgentList:
        try:
            agents = await self.agent_repository.get_all(limit=limit, active_only=active_only)
            
            # Считаем количество
            from sqlalchemy import select, func
            count_query = select(func.count(Agent.id))
            if active_only:
                count_query = count_query.where(Agent.is_active == True)
            count_result = await self.session.execute(count_query)
            total_count = count_result.scalar() or 0
            
            agents_overview = []
            for agent in agents:
                # Загружаем настроение
                if agent.current_mood_id:
                    mood_result = await self.session.execute(
                        select(CurrentMood).where(CurrentMood.id == agent.current_mood_id)
                    )
                    mood_obj = mood_result.scalar_one_or_none()
                    
                    if mood_obj:
                        mood_data = AgentCurrentMood(
                            joy=mood_obj.joy or 0.3,
                            sadness=mood_obj.sadness or 0.1,
                            anger=mood_obj.anger or 0.1,
                            fear=mood_obj.fear or 0.1,
                            color=mood_obj.color or "#4A90E2"
                        )
                    else:
                        mood_data = self._default_mood()
                else:
                    mood_data = self._default_mood()
                
                # ✅ Кодируем аватар в Base64
                avatar_base64 = self._encode_image_to_base64(agent.avatar_url)
                
                overview = AgentOverview(
                    id=agent.id,
                    name=agent.name,
                    avatar=avatar_base64,  # ✅ Отправляем Base64 вместо пути
                    mood=mood_data,
                    is_active=agent.is_active,
                    last_activity=agent.updated_at or datetime.utcnow()
                )
                agents_overview.append(overview)
            
            return AgentList(
                agents=agents_overview,
                total_count=total_count,
                active_count=sum(1 for a in agents_overview if a.is_active)
            )
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise ValueError(f"Database error: {str(e)}")
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Unexpected error: {str(e)}")
    
    def _default_mood(self) -> AgentCurrentMood:
        """Вспомогательный метод для дефолтного настроения"""
        return AgentCurrentMood(
            joy=0.3,
            sadness=0.1,
            anger=0.1,
            fear=0.1,
            color="#4A90E2"
        )
