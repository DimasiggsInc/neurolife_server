from fastapi import APIRouter


from src.llm.schemas import LLMModelList # , LLMModelFullInfo, LLMModelOverview, LLMModelCreate


router = APIRouter(
    prefix="/models",
    tags=["LLM Models"],
)


@router.get("/", response_model=LLMModelList)
async def get_llm_models() -> LLMModelList:
    return LLMModelList(models=["QWEN-3 MAX", "QWEN-3 TURBO", "QWEN-3 CHAT"])  # TODO: Реализовать получение списка моделей из базы данных или внешнего API
