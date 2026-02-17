from fastapi import APIRouter, Depends, HTTPException, status

from uuid import UUID, uuid4
from datetime import datetime

from src.llm.schemas import LLMModelList # , LLMModelFullInfo, LLMModelOverview, LLMModelCreate
from src.agent.dependencies import get_agent_service


router = APIRouter(
    prefix="/models",
    tags=["LLM Models"],
)


@router.get("/", response_model=LLMModelList)
async def get_llm_models() -> LLMModelList:
    return LLMModelList(models=["QWEN-3 MAX", "QWEN-3 TURBO", "QWEN-3 CHAT"])  # TODO: Реализовать получение списка моделей из базы данных или внешнего API
