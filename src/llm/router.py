from fastapi import APIRouter, Depends, HTTPException, status

from uuid import UUID, uuid4
from datetime import datetime

from src.agent.schemas import AgentList, AgentFullInfo, AgentOverview, AgentCreate
from src.current_mood.schemas import AgentCurrentMood

from src.agent.dependencies import get_agent_service

from src.agent.interfaces import AgentServicePort


router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


@router.get("/{agent_id}", response_model=AgentFullInfo)
async def get_agent_info(agent_id: UUID) -> AgentFullInfo:
    return AgentFullInfo(id=agent_id)


@router.get("/", response_model=AgentList)
async def get_agents_overview() -> AgentList:
    mood = AgentCurrentMood(
        joy = 0.5,
        sadness=0.5,
        anger=0.5,
        fear=0.5,
        color='#ffffff'
    )

    a = AgentOverview(
        id = uuid4(),
        name = "Эдик",
        avatar = "Base64",
        mood = mood,
        is_active=True,
        last_activity=datetime.now()
    ) 

    return AgentList(agents=[a, a, a, a, a], total_count=2, active_count=2)



@router.post("/", response_model=AgentFullInfo)
async def create_agent(
    create_agent_scheme: AgentCreate,
    service: AgentServicePort = Depends(get_agent_service)
) -> AgentFullInfo:
    print(create_agent_scheme)

    a = await service.create_agent(create_agent_scheme)

    return AgentFullInfo(id=uuid4())

