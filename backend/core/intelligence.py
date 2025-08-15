from typing import AsyncGenerator

from fastapi import HTTPException
from openai import AsyncOpenAI


async def get_async_openai_client() -> AsyncGenerator[AsyncOpenAI, None]:
    try:
        async_openai_client = AsyncOpenAI()
        yield async_openai_client
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"{e.with_traceback}")
