"""Unit tests for reception scope classifier."""

from velox.core.scope_classifier import ScopeDecision, classify_reception_scope


def test_scope_classifier_marks_hotel_request_as_in_scope() -> None:
    result = classify_reception_scope("15-18 Temmuz icin oda rezervasyonu yapmak istiyorum.")
    assert result.decision == ScopeDecision.IN_SCOPE
    assert result.reason == "hotel_domain_match"


def test_scope_classifier_marks_nearby_need_as_near_scope() -> None:
    result = classify_reception_scope("Otele yakin eczane var mi?")
    assert result.decision == ScopeDecision.NEAR_SCOPE
    assert result.reason == "guest_convenience_match"


def test_scope_classifier_marks_non_reception_topic_as_out_of_scope() -> None:
    result = classify_reception_scope("Python ile regex optimizasyonu nasil yapilir?")
    assert result.decision == ScopeDecision.OUT_OF_SCOPE
    assert result.reason == "non_reception_domain"
