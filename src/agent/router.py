from fastapi import APIRouter, Depends, HTTPException, Query, status

from uuid import UUID, uuid4
from datetime import datetime

from src.agent.services import AgentService
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
async def list_agents(
    limit: int = Query(20, ge=1, le=100, description="Лимит записей"),
    active_only: bool = Query(True, description="Только активные агенты"),
    service: AgentService = Depends(get_agent_service)
):
    try:
        agents_list = await service.get_all_agents(limit=limit, active_only=active_only)
        return agents_list
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")



@router.post("/", response_model=AgentFullInfo)
async def create_agent(
    create_agent_scheme: AgentCreate,
    service: AgentServicePort = Depends(get_agent_service)
) -> AgentFullInfo:
    print(create_agent_scheme)

    a = await service.create_agent(create_agent_scheme)

    return AgentFullInfo(id=uuid4())

