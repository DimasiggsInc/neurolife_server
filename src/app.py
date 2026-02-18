from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings

from src.agent.router import router as agents_router
from src.chat.router import router as chat_router
from src.chat_participant.router import router as chats_participants_router
from src.llm.router import router as models_router
# from src.websocket.router import router as websocket_router
from q import app as websocket_router

from src.simulation.services import SimulationService

from sqlalchemy.ext.asyncio import AsyncSession


from src.agent.interfaces import AgentRepositoryPort, AgentServicePort
from src.agent.dependencies import get_agent_service

from src.database import get_session

from src.agent.dependencies import get_agent_repository

from src.llm.services import LLMService

from src.websocket.manager import manager

from src.message.dependencies import get_message_repository
from src.message.interfaces import MessageRepositoryPort

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # settings.ALLOWED_ORIGINS
    allow_credentials=True,  # settings.ALLOW_CREDENTIALS
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def root():
    """Эндпоинт для проверки состояния сервера."""
    return {"status": "ok", "version": settings.APP_VERSION}


app.include_router(websocket_router)
app.include_router(agents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(chats_participants_router, prefix="/api/v1")
app.include_router(models_router, prefix="/api/v1")



async def get_simulation_service(
    db: AsyncSession = Depends(get_session),
    agent_repository: AgentRepositoryPort = Depends(get_agent_repository),
    agent_service: AgentServicePort = Depends(get_agent_service),
    message_repository: MessageRepositoryPort = Depends(get_message_repository)
) -> SimulationService:
    return SimulationService(
        agent_repo = agent_repository,
        agent_service = agent_service,
        message_repo = message_repository,
        # vector_repo = vector_repo,
        llm_service = LLMService(),
        ws_manager = manager,
    )


@app.post("/simulation/start")
async def start_simulation(simulation_service: SimulationService = Depends(get_simulation_service)):
    if simulation_service:
        await simulation_service.run_simulation_tick()
        return {"status": "started", "interval": 1}
    return {"error": "Service not initialized"}


@app.post("/simulation/stop")
async def stop_simulation(simulation_service: SimulationService = Depends(get_simulation_service)):
    if simulation_service:
        await simulation_service.stop()
        return {"status": "stopped"}
    return {"error": "Service not initialized"}


@app.put("/simulation/interval")
async def set_simulation_interval(seconds: int, simulation_service: SimulationService = Depends(get_simulation_service)):
    if simulation_service:
        simulation_service.set_interval(seconds)
        return {"status": "updated", "interval": 1}
    return {"error": "Service not initialized"}




if __name__ == "__main__":
    import uvicorn

    server_port = settings.PORT
    uvicorn.run("app:app", host="0.0.0.0", port=server_port, reload=True)
