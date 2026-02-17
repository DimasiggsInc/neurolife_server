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


if __name__ == "__main__":
    import uvicorn

    server_port = settings.PORT
    uvicorn.run("app:app", host="0.0.0.0", port=server_port, reload=True)
