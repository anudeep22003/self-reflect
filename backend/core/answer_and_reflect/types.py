from typing import Any, Dict, Literal

from pydantic import BaseModel, Field


class Query(BaseModel):
    query: str


class Reflection(BaseModel):
    rating: Literal["A", "B", "C"]
    reason: str = Field(description="The reason for the rating")


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
    def from_letter_grades(
        cls, letter_grades: list[Literal["A", "B", "C"]], prompts: Dict[str, Any]
    ) -> "ReflectionExtract":
        """Create ReflectionExtract from letter grades and prompts configuration."""
        completeness_rating = letter_grades[0]
        accuracy_rating = letter_grades[1]
        reasoning_rating = letter_grades[2]

        def get_reason_code(
            reflection_type: str, letter_grade: Literal["A", "B", "C"]
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

        return cls(
            completeness=Reflection(
                rating=completeness_rating,
                reason=get_reason_code("completeness", completeness_rating),
            ),
            accuracy=Reflection(
                rating=accuracy_rating,
                reason=get_reason_code("accuracy", accuracy_rating),
            ),
            reasoning=Reflection(
                rating=reasoning_rating,
                reason=get_reason_code("reasoning", reasoning_rating),
            ),
        )


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

        return cls(
            completeness=base_extract.completeness,
            accuracy=base_extract.accuracy,
            reasoning=base_extract.reasoning,
            numerical_score=numerical_score,
        )

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

        return cls(
            completeness=reflection_extract.completeness,
            accuracy=reflection_extract.accuracy,
            reasoning=reflection_extract.reasoning,
            numerical_score=numerical_score,
        )
