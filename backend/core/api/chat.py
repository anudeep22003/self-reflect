from typing import Annotated

from fastapi import APIRouter, Depends
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from pydantic import BaseModel

from core.intelligence import get_async_openai_client
from core.respond_score import Query, RespondAndScore
from core.types import ScoredReflection

router = APIRouter(prefix="/chat")


class ChatWithScoreResponse(BaseModel):
    base_response: ChatCompletion
    reflection_response: ScoredReflection


@router.post("/chat_with_score")
async def chat_with_score(
    user_query: Query,
    async_openai_client: Annotated[AsyncOpenAI, Depends(get_async_openai_client)],
) -> ChatWithScoreResponse:
    worker = RespondAndScore(async_openai_client)
    base_response, reflection_response = await worker.answer_and_self_reflect(
        user_query
    )
    return ChatWithScoreResponse(
        base_response=base_response, reflection_response=reflection_response
    )
