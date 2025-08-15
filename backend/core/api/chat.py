from typing import Annotated

from fastapi import APIRouter, Depends
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from pydantic import BaseModel

from core.answer_and_reflect.respond_score import RespondAndScore
from core.answer_and_reflect.types import Query, ScoredReflection
from core.config import MODEL
from core.intelligence import get_async_openai_client

router = APIRouter(prefix="/chat")


class ChatWithScoreResponse(BaseModel):
    base_response: ChatCompletion
    reflection_response: ScoredReflection


@router.post("/chat_with_score")
async def chat_with_score(
    user_query: Query,
    async_openai_client: Annotated[AsyncOpenAI, Depends(get_async_openai_client)],
) -> ChatWithScoreResponse:
    """
    Chat with the model and get a score for the response. This endpoint is optimized for:
    - Speed (minimize tokens)
    - Cost (maximize kv cache hits)
    - Static reasoning (reasoning is generated from the yaml file)
    - Error handling (errors manually checked and handled)
    """
    worker = RespondAndScore(async_openai_client=async_openai_client, model=MODEL)
    base_response, reflection_response = await worker.answer_and_self_reflect(
        user_query
    )
    return ChatWithScoreResponse(
        base_response=base_response, reflection_response=reflection_response
    )


@router.post("/chat_with_score_reflect_and_reason")
async def chat_with_score_reflect_and_reason(
    user_query: Query,
    async_openai_client: Annotated[AsyncOpenAI, Depends(get_async_openai_client)],
) -> ChatWithScoreResponse:
    """
    Chat with the model and get a score for the response. This endpoint is optimized for:
    - Reasoning (more detailed reasoning, and reasoning is supplied by the AI)
    - Error handling (errors checked by AI and retried)
    - Takes more time because more tokens are generated

    Here we are using insructor to do scructured extraction so the reasoning is supplied by the AI.
    """
    worker = RespondAndScore(async_openai_client=async_openai_client, model=MODEL)
    (
        base_response,
        reflection_response,
    ) = await worker.answer_and_self_reflect_with_reasoning(user_query)
    return ChatWithScoreResponse(
        base_response=base_response, reflection_response=reflection_response
    )
