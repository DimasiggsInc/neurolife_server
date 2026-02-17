import uuid
from pathlib import Path
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.interfaces import AgentRepositoryPort, AgentServicePort, ImageGeneratorPort
from src.agent.schemas import AgentCreate, AgentFullInfo
from src.agent.models import Agent

from src.speech_style.models import SpeechStyle
from src.speech_style.repositories import SpeechStyleRepository

from src.personality.models import Personality
from src.personality.repositories import PersonalityRepository

from src.current_mood.models import CurrentMood
from src.current_mood.repositories import CurrentMoodRepository


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