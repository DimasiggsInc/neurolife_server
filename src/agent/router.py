from fastapi import APIRouter, Depends, HTTPException, Query, status

from uuid import UUID

from src.agent.services import AgentService
from src.agent.schemas import AgentList, AgentFullInfo, AgentCreate

from src.agent.dependencies import get_agent_service

from src.agent.interfaces import AgentServicePort


router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


@router.get("/{agent_id}", response_model=AgentFullInfo)
async def get_agent_info(
    agent_id: UUID,
    service: AgentService = Depends(get_agent_service)
) -> AgentFullInfo:
    created_agent = await service.get_agent_by_id(agent_id)

    return created_agent


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
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")



@router.post("/", response_model=AgentFullInfo)
async def create_agent(
    create_agent_scheme: AgentCreate,
    service: AgentService = Depends(get_agent_service)
) -> AgentFullInfo:
    print(create_agent_scheme)

    a = await service.create_agent(create_agent_scheme)  # TODO

    return a



@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    service: AgentServicePort = Depends(get_agent_service),
):
    try:
        await service.delete_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))