import os
from dotenv import load_dotenv
from typing import List


load_dotenv(override=True)


class Settings:
    """Настройки для всего проекта."""

    APP_VERSION: str = "0.0.1"
    PORT: int = int(os.getenv("PORT", 8000))

    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "postgres")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_NAME: str = os.getenv("POSTGRES_NAME", "neurolife_db")

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/neurolife_db",
    )

    # CORS настройки
    BACKEND_CORS_ORIGINS: List[str] = ["*"]


    FREEQWEN_BASE_URL =  os.getenv("FREEQWEN_BASE_URL", "http://host.docker.internal:3264/api")
    FREEQWEN_MODEL =  os.getenv("FREEQWEN_MODEL", "qwen3.5-plus")
    FREEQWEN_TIMEOUT = float(os.getenv("FREEQWEN_TIMEOUT", "60"))


settings = Settings()
