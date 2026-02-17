from sqlalchemy.ext.asyncio import AsyncSession
from src.agent.models import Agent
from src.agent.interfaces import AgentRepositoryPort

class AgentRepository(AgentRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, agent: Agent) -> Agent:
        self.session.add(agent)
        await self.session.flush()
        return agent
