"""Unit tests for response review request validation."""

import pytest
from pydantic import ValidationError

from velox.models.response_review import (
    ResponseReviewClassification,
    ResponseReviewClassifyRequest,
    ResponseReviewErrorType,
)


def test_correct_classification_forces_five_star_rating() -> None:
    payload = ResponseReviewClassifyRequest(
        classification=ResponseReviewClassification.CORRECT,
        rating=2,
        gold_standard="Bu alan doğru kararda yok sayılır.",
    )

    assert payload.rating == 5
    assert payload.gold_standard is None


def test_incorrect_classification_requires_reference_answer() -> None:
    with pytest.raises(ValidationError):
        ResponseReviewClassifyRequest(
            classification=ResponseReviewClassification.INCORRECT,
            error_type=ResponseReviewErrorType.WRONG_INFO,
        )


def test_problematic_classification_requires_error_type() -> None:
    with pytest.raises(ValidationError):
        ResponseReviewClassifyRequest(
            classification=ResponseReviewClassification.NEEDS_REVISION,
            gold_standard="Misafire daha kısa ve kaynaklı yanıt verilmelidir.",
        )
