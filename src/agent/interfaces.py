from typing import Protocol
from PIL import Image

from src.agent.schemas import AgentCreate, AgentFullInfo
from typing import Optional, List
from src.agent.models import Agent



class AgentRepositoryPort(Protocol):
    """Интерфейс репозитория агентов"""
    async def add(self, agent: Agent) -> Agent: ...
    async def get_by_id(self, agent_id: int) -> Optional[Agent]: ...
    async def get_all(self, active_only: bool = True, limit: int = 20) -> List[Agent]: ...
    async def delete(self, agent_id: int) -> bool: ...
    async def update(self, agent: Agent) -> Agent: ...


class AgentServicePort(Protocol):
    async def create_agent(self, new_agent: AgentCreate) -> AgentFullInfo: ...  # TODO


class ImageGeneratorPort(Protocol):
    size: int
    grid_size: int
    def generate(self, text: str) -> Image.Image: ...

