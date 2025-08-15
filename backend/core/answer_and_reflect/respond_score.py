import logging
from typing import Any, Dict, Literal, cast

import instructor
import openai
import yaml  # type: ignore
from fastapi import HTTPException
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from core.config import MAX_RETRIES

from .exceptions import (
    InvalidLetterGrade,
    LetterGradesNotThreeCharactersLong,
    NoLetterGradesFound,
    RetryException,
)
from .types import Query, ReflectionExtract, ScoredReflection


class RespondAndScore:
    def __init__(
        self,
        async_openai_client: AsyncOpenAI,
        model: str = "gpt-4o-mini",
        prompts_file: str = "core/answer_and_reflect/prompts.yaml",
    ) -> None:
        self.async_client = async_openai_client
        self.prompts = self._load_prompts(prompts_file)
        self.model = model
        self.prompts_file = prompts_file
        self.logger = logging.getLogger(__name__)

    def _load_prompts(self, prompts_file: str) -> Dict[str, Any]:
        """Load prompts from the centralized YAML file."""
        try:
            with open(prompts_file, "r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompts file not found at {prompts_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing prompts YAML: {e}")

    @property
    def system_prompt(self) -> str:
        return self.prompts["respond_score"]["system_prompt"]

    @property
    def concise_addition(self) -> str:
        return self.prompts["respond_score"]["concise_addition"]

    @property
    def user_message_template(self) -> str:
        return self.prompts["respond_score"]["user_message_template"]

    async def answer_and_self_reflect(
        self, user_query: Query
    ) -> tuple[ChatCompletion, ScoredReflection]:
        answer = await self.answer(user_query)
        self_reflection = await self.self_reflect_concisely(user_query, answer)
        return answer, self_reflection

    async def answer_and_self_reflect_with_reasoning(
        self, user_query: Query
    ) -> tuple[ChatCompletion, ScoredReflection]:
        answer = await self.answer(user_query)
        self_reflection = await self.self_reflect_with_reasoning(user_query, answer)
        return answer, self_reflection

    @retry(
        retry=retry_if_exception_type(RetryException),
        stop=stop_after_attempt(MAX_RETRIES),
        reraise=True,
    )
    async def answer(self, user_query: Query) -> ChatCompletion:
        self.logger.info("Answering the question")
        try:
            response = await self.async_client.chat.completions.create(
                messages=[{"role": "user", "content": user_query.query}],
                model=self.model,
            )
            return response
        except openai.APIConnectionError as e:
            raise HTTPException(status_code=500, detail=f"API connection error: {e}")
        except openai.AuthenticationError as e:
            raise HTTPException(status_code=401, detail=f"Authentication error: {e}")
        except openai.RateLimitError as e:
            raise HTTPException(status_code=429, detail=f"Rate limit exceeded: {e}")
        except openai.BadRequestError as e:
            raise HTTPException(status_code=400, detail=f"Bad request: {e}")
        except openai.NotFoundError as e:
            raise HTTPException(status_code=404, detail=f"Not found: {e}")
        except openai.PermissionDeniedError as e:
            raise HTTPException(status_code=403, detail=f"Permission denied: {e}")
        except openai.InternalServerError:
            raise RetryException()
        except Exception:
            raise RetryException()

    @retry(
        retry=retry_if_exception_type(RetryException),
        stop=stop_after_attempt(MAX_RETRIES),
        reraise=True,
    )
    async def self_reflect_concisely(
        self, query: Query, original_answer: ChatCompletion
    ) -> ScoredReflection:
        self.logger.info("Self-reflecting")
        concise_system_prompt = self.system_prompt
        concise_system_prompt += self.concise_addition
        self.logger.debug(f"System prompt: {concise_system_prompt}")
        user_message = self.user_message_template.format(
            query=query.query, answer=original_answer.choices[0].message.content
        )
        self.logger.debug(f"User message: {user_message}")
        try:
            response = await self.async_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": concise_system_prompt},
                    {"role": "user", "content": user_message},
                ],
                model=self.model,
            )
            self.logger.debug(f"API response: {response}")
            letter_grades = self.check_veracity_of_concise_reflection(response)
        except NoLetterGradesFound:
            raise RetryException()
        except LetterGradesNotThreeCharactersLong:
            raise RetryException()
        except InvalidLetterGrade:
            raise RetryException()
        except Exception:
            raise RetryException()

        return ScoredReflection.from_letter_grades(letter_grades, self.prompts)

    def check_veracity_of_concise_reflection(
        self, reflection: ChatCompletion
    ) -> list[Literal["A", "B", "C"]]:
        acceptable_grades = ["A", "B", "C"]

        letter_grades = reflection.choices[0].message.content

        if letter_grades is None:
            raise NoLetterGradesFound()

        if len(letter_grades) != 3:
            raise LetterGradesNotThreeCharactersLong()

        for letter in letter_grades:
            if letter not in acceptable_grades:
                raise InvalidLetterGrade()

        return cast(list[Literal["A", "B", "C"]], letter_grades)

    @retry(
        retry=retry_if_exception_type(RetryException),
        stop=stop_after_attempt(MAX_RETRIES),
        reraise=True,
    )
    async def self_reflect_with_reasoning(
        self, query: Query, original_answer: ChatCompletion
    ) -> ScoredReflection:
        self.logger.info("Self-reflecting with reasoning")
        instructor_client = instructor.from_openai(self.async_client)

        user_message = self.user_message_template.format(
            query=query.query, answer=original_answer.choices[0].message.content
        )
        reflection_extract = await instructor_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_model=ReflectionExtract,
        )

        if reflection_extract is None:
            raise RetryException()

        return ScoredReflection.from_reflection_extract(reflection_extract)
