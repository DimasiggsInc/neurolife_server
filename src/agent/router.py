from fastapi import APIRouter, Depends, HTTPException, status

from uuid import UUID, uuid4
from datetime import datetime

from src.agent.schemas import AgentList, AgentFullInfo, AgentOverview
from src.current_mood.schemas import AgentCurrentMood


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
        saddness=0.5,
        anger=0.5,
        fear=0.5,
        color='#ffffff'
    )

    a = AgentOverview(
        id = uuid4(),
        name = "",
        avatar = "",
        mood = mood,
        is_active=True,
        last_activity=datetime.now()
    ) 

    return AgentList(agents=[a, a], total_count=2, active_count=2)





# @router.post(
#     "/register",
#     response_model=UserAuthenticationResponse,
#     status_code=status.HTTP_201_CREATED,
# )
# async def register(
#     user: UserAuthenticationRequest,
#     auth_service: AuthServicePort = Depends(get_auth_service)
# ):
#     try:
#         result = await auth_service.register(user)

#         return UserAuthenticationResponse(token=result.token, refresh_token=result.refresh_token)

#     except UserAlreadyExistsError:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="User with this nickname already exists",
#         )
