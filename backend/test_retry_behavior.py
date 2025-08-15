from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from openai.types.chat import ChatCompletion

from core.answer_and_reflect.exceptions import (
    RetryException,
)
from core.answer_and_reflect.respond_score import RespondAndScore
from core.answer_and_reflect.types import Query, Reflection, ReflectionExtract
from core.config import MAX_RETRIES


@pytest.fixture
def mock_openai_client():
    return AsyncMock()


@pytest.fixture
def respond_score(mock_openai_client):
    with patch("core.answer_and_reflect.respond_score.yaml.safe_load") as mock_yaml:
        mock_yaml.return_value = {
            "respond_score": {
                "system_prompt": "Test system prompt",
                "concise_addition": "Test concise addition",
                "user_message_template": "Query: {query}, Answer: {answer}",
                "reason_codes": {
                    "completeness": {
                        "A": "Complete",
                        "B": "Incomplete",
                        "C": "Partial",
                    },
                    "accuracy": {
                        "A": "Accurate",
                        "B": "Inaccurate",
                        "C": "Mostly accurate",
                    },
                    "reasoning": {
                        "A": "Good reasoning",
                        "B": "Poor reasoning",
                        "C": "Fair reasoning",
                    },
                },
            }
        }
        with patch("builtins.open", MagicMock()):
            return RespondAndScore(mock_openai_client)


@pytest.mark.asyncio
async def test_answer_retries_on_internal_server_error(
    respond_score, mock_openai_client
):
    from openai import InternalServerError

    mock_response = Mock()
    mock_openai_client.chat.completions.create.side_effect = [
        InternalServerError("Internal server error", response=mock_response, body={}),
        MagicMock(
            spec=ChatCompletion,
            choices=[MagicMock(message=MagicMock(content="Test answer"))],
        ),
    ]

    query = Query(query="Test question")
    result = await respond_score.answer(query)

    assert mock_openai_client.chat.completions.create.call_count == 2
    assert result.choices[0].message.content == "Test answer"


@pytest.mark.asyncio
async def test_answer_retries_on_generic_exception(respond_score, mock_openai_client):
    mock_openai_client.chat.completions.create.side_effect = [
        Exception("Generic error"),
        MagicMock(
            spec=ChatCompletion,
            choices=[MagicMock(message=MagicMock(content="Test answer"))],
        ),
    ]

    query = Query(query="Test question")
    result = await respond_score.answer(query)

    assert mock_openai_client.chat.completions.create.call_count == 2
    assert result.choices[0].message.content == "Test answer"


@pytest.mark.asyncio
async def test_answer_fails_after_max_retries(respond_score, mock_openai_client):
    from openai import InternalServerError

    mock_response = Mock()
    mock_openai_client.chat.completions.create.side_effect = InternalServerError(
        "Internal server error", response=mock_response, body={}
    )

    query = Query(query="Test question")

    with pytest.raises(RetryException):
        await respond_score.answer(query)

    assert mock_openai_client.chat.completions.create.call_count == MAX_RETRIES


@pytest.mark.asyncio
async def test_self_reflect_retries_on_no_letter_grades_found(
    respond_score, mock_openai_client
):
    mock_response = MagicMock(spec=ChatCompletion)
    mock_response.choices = [MagicMock(message=MagicMock(content=None))]

    good_response = MagicMock(spec=ChatCompletion)
    good_response.choices = [MagicMock(message=MagicMock(content="ABC"))]

    mock_openai_client.chat.completions.create.side_effect = [
        mock_response,  # First attempt: returns None content
        good_response,  # Second attempt: returns valid grades
    ]

    query = Query(query="Test question")
    original_answer = MagicMock(spec=ChatCompletion)
    original_answer.choices = [MagicMock(message=MagicMock(content="Test answer"))]

    result = await respond_score.self_reflect_concisely(query, original_answer)

    assert mock_openai_client.chat.completions.create.call_count == 2
    assert result.completeness.rating == "A"
    assert result.accuracy.rating == "B"
    assert result.reasoning.rating == "C"


@pytest.mark.asyncio
async def test_self_reflect_retries_on_wrong_letter_grades_length(
    respond_score, mock_openai_client
):
    short_response = MagicMock(spec=ChatCompletion)
    short_response.choices = [MagicMock(message=MagicMock(content="AB"))]

    good_response = MagicMock(spec=ChatCompletion)
    good_response.choices = [MagicMock(message=MagicMock(content="ABC"))]

    mock_openai_client.chat.completions.create.side_effect = [
        short_response,  # First attempt: too short
        good_response,  # Second attempt: correct length
    ]

    query = Query(query="Test question")
    original_answer = MagicMock(spec=ChatCompletion)
    original_answer.choices = [MagicMock(message=MagicMock(content="Test answer"))]

    result = await respond_score.self_reflect_concisely(query, original_answer)

    assert mock_openai_client.chat.completions.create.call_count == 2
    assert result.completeness.rating == "A"
    assert result.accuracy.rating == "B"
    assert result.reasoning.rating == "C"


@pytest.mark.asyncio
async def test_self_reflect_retries_on_invalid_letter_grade(
    respond_score, mock_openai_client
):
    invalid_d_response = MagicMock(spec=ChatCompletion)
    invalid_d_response.choices = [MagicMock(message=MagicMock(content="ABD"))]

    good_response = MagicMock(spec=ChatCompletion)
    good_response.choices = [MagicMock(message=MagicMock(content="ABC"))]

    mock_openai_client.chat.completions.create.side_effect = [
        invalid_d_response,  # First attempt: contains 'D'
        good_response,  # Second attempt: valid grades
    ]

    query = Query(query="Test question")
    original_answer = MagicMock(spec=ChatCompletion)
    original_answer.choices = [MagicMock(message=MagicMock(content="Test answer"))]

    result = await respond_score.self_reflect_concisely(query, original_answer)

    assert mock_openai_client.chat.completions.create.call_count == 2
    assert result.completeness.rating == "A"
    assert result.accuracy.rating == "B"
    assert result.reasoning.rating == "C"


@pytest.mark.asyncio
async def test_self_reflect_fails_after_max_retries_on_invalid_grades(
    respond_score, mock_openai_client
):
    invalid_response = MagicMock(spec=ChatCompletion)
    invalid_response.choices = [MagicMock(message=MagicMock(content="XYZ"))]

    mock_openai_client.chat.completions.create.return_value = invalid_response

    query = Query(query="Test question")
    original_answer = MagicMock(spec=ChatCompletion)
    original_answer.choices = [MagicMock(message=MagicMock(content="Test answer"))]

    with pytest.raises(RetryException):
        await respond_score.self_reflect_concisely(query, original_answer)

    assert mock_openai_client.chat.completions.create.call_count == MAX_RETRIES


@pytest.mark.asyncio
async def test_self_reflect_with_reasoning_retries_on_none_response(
    respond_score, mock_openai_client
):
    with patch("core.answer_and_reflect.respond_score.instructor") as mock_instructor:
        mock_instructor_client = AsyncMock()
        mock_instructor.from_openai.return_value = mock_instructor_client

        mock_reflection_extract = ReflectionExtract(
            completeness=Reflection(rating="A", reason="Complete"),
            accuracy=Reflection(rating="B", reason="Inaccurate"),
            reasoning=Reflection(rating="C", reason="Fair reasoning"),
        )

        mock_instructor_client.chat.completions.create.side_effect = [
            None,
            mock_reflection_extract,
        ]

        query = Query(query="Test question")
        original_answer = MagicMock(spec=ChatCompletion)
        original_answer.choices = [MagicMock(message=MagicMock(content="Test answer"))]

        result = await respond_score.self_reflect_with_reasoning(query, original_answer)

        assert mock_instructor_client.chat.completions.create.call_count == 2
        assert result.completeness.rating == "A"
        assert result.accuracy.rating == "B"
        assert result.reasoning.rating == "C"


@pytest.mark.asyncio
async def test_self_reflect_retries_on_api_exception(respond_score, mock_openai_client):
    good_response = MagicMock(spec=ChatCompletion)
    good_response.choices = [MagicMock(message=MagicMock(content="ABC"))]

    mock_openai_client.chat.completions.create.side_effect = [
        Exception("API error"),
        good_response,
    ]

    query = Query(query="Test question")
    original_answer = MagicMock(spec=ChatCompletion)
    original_answer.choices = [MagicMock(message=MagicMock(content="Test answer"))]

    result = await respond_score.self_reflect_concisely(query, original_answer)

    assert mock_openai_client.chat.completions.create.call_count == 2
    assert result.completeness.rating == "A"
    assert result.accuracy.rating == "B"
    assert result.reasoning.rating == "C"
