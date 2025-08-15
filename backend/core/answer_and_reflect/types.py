from typing import Any, Dict, Literal

from pydantic import BaseModel, Field


class Query(BaseModel):
    query: str


class Reflection(BaseModel):
    rating: Literal["A", "B", "C"] = Field(
        description="The rating for the reflection, with A being the most confident, B being the least confident, and C being the middle confidence."
    )
    reason: str = Field(
        description="Detailed reasoning for the rating, try to come up with underlying assumptions and recreate the process that led to the rating. Use chain of thought if necessary."
    )


class ReflectionExtract(BaseModel):
    """Base class for structured reflection extraction without numeric scoring."""

    completeness: Reflection = Field(
        description="How confident are you that your answer addresses the user's question completely?"
    )
    accuracy: Reflection = Field(
        description="How certain are you that the factual claims in your answer are accurate?"
    )
    reasoning: Reflection = Field(
        description="How confident are you in the logical reasoning of your answer?"
    )

    @classmethod
    def _get_reason_code(
        cls,
        prompts: Dict[str, Any],
        reflection_type: str,
        letter_grade: Literal["A", "B", "C"],
    ) -> str:
        """Get the reason code for a specific reflection type and rating from the prompts configuration."""
        try:
            return prompts["respond_score"]["reason_codes"][reflection_type][
                letter_grade
            ]
        except KeyError:
            raise ValueError(
                f"Invalid reflection type '{reflection_type}' or rating '{letter_grade}'"
            )

    @classmethod
    def _create_reflections_from_grades(
        cls, letter_grades: list[Literal["A", "B", "C"]], prompts: Dict[str, Any]
    ) -> tuple[Reflection, Reflection, Reflection]:
        """Create the three reflection objects from letter grades."""
        completeness_rating, accuracy_rating, reasoning_rating = letter_grades

        return (
            Reflection(
                rating=completeness_rating,
                reason=cls._get_reason_code(
                    prompts, "completeness", completeness_rating
                ),
            ),
            Reflection(
                rating=accuracy_rating,
                reason=cls._get_reason_code(prompts, "accuracy", accuracy_rating),
            ),
            Reflection(
                rating=reasoning_rating,
                reason=cls._get_reason_code(prompts, "reasoning", reasoning_rating),
            ),
        )

    @classmethod
    def from_letter_grades(
        cls, letter_grades: list[Literal["A", "B", "C"]], prompts: Dict[str, Any]
    ) -> "ReflectionExtract":
        """Create ReflectionExtract from letter grades and prompts configuration."""
        completeness, accuracy, reasoning = cls._create_reflections_from_grades(
            letter_grades, prompts
        )
        return cls(completeness=completeness, accuracy=accuracy, reasoning=reasoning)


class ScoredReflection(ReflectionExtract):
    """Reflection with calculated numeric score for evaluation purposes."""

    numerical_score: float = Field(
        description="Calculated numeric score from letter grades"
    )

    @classmethod
    def calculate_numerical_score(
        cls, letter_grades: list[Literal["A", "B", "C"]]
    ) -> float:
        """Calculate numerical score from letter grades.

        A = 1.0, B = 0.0, C = 0.5
        Returns average rounded to 2 decimal places.
        """
        grade_values = {"A": 1.0, "B": 0.0, "C": 0.5}
        return round(
            sum(grade_values[grade] for grade in letter_grades) / 3,
            2,
        )

    @classmethod
    def from_letter_grades(
        cls, letter_grades: list[Literal["A", "B", "C"]], prompts: Dict[str, Any]
    ) -> "ScoredReflection":
        """Create ScoredReflection from letter grades and prompts configuration."""
        base_extract = ReflectionExtract.from_letter_grades(letter_grades, prompts)
        numerical_score = cls.calculate_numerical_score(letter_grades)
        return cls(**base_extract.model_dump(), numerical_score=numerical_score)

    @classmethod
    def from_reflection_extract(
        cls, reflection_extract: ReflectionExtract
    ) -> "ScoredReflection":
        """Create ScoredReflection from ReflectionExtract."""
        letter_grades = [
            reflection_extract.completeness.rating,
            reflection_extract.accuracy.rating,
            reflection_extract.reasoning.rating,
        ]
        numerical_score = cls.calculate_numerical_score(letter_grades)
        return cls(**reflection_extract.model_dump(), numerical_score=numerical_score)
