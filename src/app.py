from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Request

from src.config import settings

from src.agent.router import router as agents_router
from src.websocket.router import router as websocket_router

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


from src.simulation.services import SimulationService
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession


from src.agent.interfaces import AgentRepositoryPort

from src.database import get_session

from src.event.services import EventService

from src.agent.dependencies import get_agent_repository


async def get_simulation_service(
    db: AsyncSession = Depends(get_session),
    agent_repository: AgentRepositoryPort = Depends(get_agent_repository)
) -> AgentRepositoryPort:
    return SimulationService(
        session=db,
        agent_repository=agent_repository,
        event_service=EventService(db)
    )


@app.post("/simulation/start")
async def start_simulation(simulation_service: SimulationService = Depends(get_simulation_service)):
    if simulation_service:
        await simulation_service.start()
        return {"status": "started", "interval": simulation_service.interval_seconds}
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
        return {"status": "updated", "interval": simulation_service.interval_seconds}
    return {"error": "Service not initialized"}




if __name__ == "__main__":
    import uvicorn

    server_port = settings.PORT
    uvicorn.run("app:app", host="0.0.0.0", port=server_port, reload=True)
