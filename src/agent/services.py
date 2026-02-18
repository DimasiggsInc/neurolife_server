import base64
import uuid
from pathlib import Path
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.agent.interfaces import AgentRepositoryPort, AgentServicePort, ImageGeneratorPort
from src.agent.schemas import AgentCreate, AgentFullInfo, AgentList, AgentOverview
from src.chat.schemas import AgentChatList, ChatOverview
from src.current_mood.schemas import AgentCurrentMood
from src.agent.models import Agent

from src.speech_style.models import SpeechStyle
from src.speech_style.repositories import SpeechStyleRepository

from src.personality.models import Personality
from src.personality.repositories import PersonalityRepository

from src.current_mood.models import CurrentMood
from src.current_mood.repositories import CurrentMoodRepository

from src.message.schemas import UserMessageToAgent

from src.agent.utils import generate_color

from src.chat.repositories import ChatRepository



class AgentService(AgentServicePort):
    AVATARS_DIR = Path("/server/avatars")

    def __init__(
        self,
        session: AsyncSession,
        image_generator: ImageGeneratorPort,
        agent_repository: AgentRepositoryPort,
        speech_style_repository: SpeechStyleRepository,
        personality_repository: PersonalityRepository,
        current_mood_repository: CurrentMoodRepository,
        chat_repository: ChatRepository
    ):
        self.session = session
        self.image_generator = image_generator
        self.agent_repository = agent_repository
        self.speech_style_repository = speech_style_repository
        self.personality_repository = personality_repository
        self.current_mood_repository = current_mood_repository
        self.chat_repository = chat_repository
        
        # ✅ Создаем директорию при инициализации
        self.AVATARS_DIR.mkdir(parents=True, exist_ok=True)

    async def create_agent(self, new_agent: AgentCreate) -> AgentFullInfo:
        # ✅ 0. Генерируем UUID заранее
        agent_id = uuid.uuid4()

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
            background=new_agent.background or "background",
            knowledge=0.7,
            safety=0.6,
            freedom=0.5,
            extraversion=0.6
        )
        personality = await self.personality_repository.add(personality)

        try:
            # 3. Создаем настроение (запись в БД)
            current_mood = CurrentMood(
                joy=1.0 if new_agent.mood == "joy" else 0.0,
                sadness=1.0 if new_agent.mood == "sadness" else 0.0,
                anger=1.0 if new_agent.mood == "anger" else 0.0,
                fear=1.0 if new_agent.mood == "fear" else 0.0,
                updated_at=datetime.utcnow()
            )
            current_mood = await self.current_mood_repository.add(current_mood)

            # 4. Валидация данных для ответа (внутри try, чтобы сработала очистка при ошибке)
            rgb_color = generate_color(current_mood.sadness, current_mood.joy, current_mood.anger, current_mood.fear)

            mood = AgentCurrentMood(
                joy=current_mood.joy,
                sadness=current_mood.sadness,
                anger=current_mood.anger,
                fear=current_mood.fear,
                color=str(rgb_color), 
            )

            # ✅ 5. Генерируем аватар
            avatar_filename = f"{agent_id}.png"
            avatar_url = f"/avatars/{avatar_filename}"
            avatar_full_path = self.AVATARS_DIR / avatar_filename
            
            self.image_generator.generate(avatar_url).save(str(avatar_full_path))

            # 6. Создаем агента
            agent = Agent(
                id=agent_id,
                name=new_agent.name,
                ai_model=new_agent.ai_model,
                personality_id=personality.id,
                current_mood_id=current_mood.id,
                current_plan=new_agent.plans,
                avatar_url=avatar_url,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            agent = await self.agent_repository.add(agent)
            await self.session.commit()
            await self.session.refresh(agent)
            avatar_base64 = self._encode_image_to_base64(agent.avatar_url)
            return AgentFullInfo(
                id=agent.id,
                name=agent.name,
                avatar=avatar_base64,
                mood=mood,
                created_at=agent.created_at.isoformat(),
                is_active=agent.is_active,
                last_activity=agent.updated_at.isoformat(),
                background=personality.background,
                model=agent.ai_model,
                plan=agent.current_plan,
            )

        except Exception as e:
            await self.session.rollback()
            # Удаляем аватар при любой ошибке внутри try
            if 'avatar_full_path' in locals() and avatar_full_path.exists():
                avatar_full_path.unlink()
            raise e

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

    async def get_agent_by_id(self, agent_id: str) -> AgentFullInfo:
        """✅ Получить полную информацию об агенте по ID"""
        try:
            # 1. Валидируем UUID
            agent_uuid = agent_id
            
            # 2. Получаем агента
            agent = await self.agent_repository.get_by_id(agent_uuid)
            if not agent:
                raise ValueError(f"Agent with id '{agent_id}' not found")

            personality = await self.personality_repository.get_by_id(agent.personality_id)
            
            # 3. Загружаем настроение
            mood_data = self._default_mood()
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
            
            # 4. Кодируем аватар в Base64
            avatar_base64 = self._encode_image_to_base64(agent.avatar_url)
            
            # 5. ✅ Формируем ответ с ПРАВИЛЬНЫМИ полями
            return AgentFullInfo(
                id=agent.id,
                name=agent.name,
                avatar=avatar_base64,              # ✅ avatar (не avatar_url)
                mood=mood_data,                    # ✅ Объект AgentCurrentMood
                is_active=agent.is_active,         # ✅ Требуется
                last_activity=agent.updated_at or datetime.utcnow(),  # ✅ Требуется
                background=personality.background,  # TODO: Получать по 
                model=agent.ai_model,                     # ✅ Требуется (заглушка или из БД)
                plan=agent.current_plan or "",     # ✅ plan (не current_plan)
                created_at=agent.created_at.isoformat() + "Z" if agent.created_at else ""
            )
            
        except ValueError as e:
            error_msg = str(e)
            if "badly formed hexadecimal UUID" in error_msg or "invalid literal" in error_msg:
                raise ValueError(f"Invalid agent id format: '{agent_id}'")
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise ValueError(f"Database error: {str(e)}")
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Unexpected error: {str(e)}")
            
    async def delete_agent(self, agent_id: uuid.UUID) -> bool:
        # TODO удалить связи с агентом
        """Метод для удаления"""
        agent = await self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise ValueError("Agent not found")

        if agent.avatar_url:
            filename = agent.avatar_url.split("/")[-1]
            avatar_path = self.AVATARS_DIR / filename
            if avatar_path.exists():
                avatar_path.unlink()

        deleted = await self.agent_repository.delete(agent_id)
        if not deleted:
            raise ValueError("Failed to delete agent")

        return True
    
    def _default_mood(self) -> AgentCurrentMood:
        """Вспомогательный метод для дефолтного настроения"""
        return AgentCurrentMood(
            joy=0.3,
            sadness=0.1,
            anger=0.1,
            fear=0.1,
            color="#4A90E2"
        )


    async def get_all_agent_chats(
        self, 
        agent_id: str, 
        limit: int = 50
    ) -> AgentChatList:
        """
        Получить все активные чаты для конкретного агента
        
        Соответствует требованию хакатона:
        - 3.a Наблюдать за их жизнью в реальном времени
        - 7. Инспектор агента (при клике показываем чаты)
        """
        try:
            # 1. Валидируем UUID агента
            agent_uuid = uuid.UUID(agent_id)
            
            # 2. Проверяем существование агента
            agent = await self.agent_repository.get_by_id(agent_uuid)
            if not agent:
                raise ValueError(f"Агент с id '{agent_id}' не найден")
            
            # 3. Получаем все активные чаты агента из БД
            chats = await self.chat_repository.get_all_active_chats_for_agent(
                agent_id=agent_uuid, 
                limit=limit
            )
            
            # 4. Формируем ответ с дополнительной информацией
            chats_overview = []
            for chat in chats:
                # Получаем последнее сообщение для превью
                last_message = await self.chat_repository.get_last_message_for_chat(chat.id)
                last_message_preview = last_message.content[:100] if last_message else None
                
                # Получаем количество непрочитанных
                unread_count = await self.chat_repository.get_unread_count_for_agent(
                    chat.id, 
                    agent_uuid
                )
                
                # Получаем количество участников
                participants_count = await self.chat_repository.get_participants_count(chat.id)
                
                chat_overview = ChatOverview(
                    id=chat.id,
                    name=chat.name,
                    type=chat.type,
                    is_active=chat.is_active,
                    created_at=chat.created_at,
                    updated_at=chat.updated_at,
                    last_message_preview=last_message_preview,
                    unread_count=unread_count,
                    participants_count=participants_count
                )
                chats_overview.append(chat_overview)
            
            return AgentChatList(
                chats=chats_overview,
                total_count=len(chats_overview),
                agent_id=agent_uuid
            )
            
        except ValueError as e:
            error_msg = str(e)
            if "badly formed hexadecimal UUID" in error_msg or "invalid literal" in error_msg:
                raise ValueError(f"Неверный формат id агента: '{agent_id}'")
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise ValueError(f"Ошибка базы данных: {str(e)}")
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Неожиданная ошибка: {str(e)}")