"""Unit tests for deterministic media response policy."""

from velox.core.media_response_policy import build_media_policy_response
from velox.models.media import VisionAnalysisResult


def test_payment_proof_policy_routes_to_handoff() -> None:
    """Payment proof image should force human handoff."""
    analysis = VisionAnalysisResult(
        intent="payment_proof_photo",
        confidence=0.91,
        summary="payment receipt",
        detected_text="payment completed",
        risk_flags=[],
        requires_handoff=True,
    )

    response = build_media_policy_response(language="tr", analysis=analysis)
    assert response.internal_json.state == "HANDOFF"
    assert response.internal_json.intent == "payment_inquiry"
    assert "PAYMENT_CONFUSION" in response.internal_json.risk_flags


def test_room_issue_policy_routes_to_ops_handoff() -> None:
    """Room issue image should create complaint handoff."""
    analysis = VisionAnalysisResult(
        intent="room_issue_photo",
        confidence=0.87,
        summary="water leak near sink",
        detected_text="",
        risk_flags=[],
        requires_handoff=True,
    )

    response = build_media_policy_response(language="en", analysis=analysis)
    assert response.internal_json.state == "HANDOFF"
    assert response.internal_json.intent == "complaint"
    assert "ANGRY_COMPLAINT" in response.internal_json.risk_flags


def test_low_confidence_general_photo_asks_clarification() -> None:
    """Low-confidence general image should ask one clarification question."""
    analysis = VisionAnalysisResult(
        intent="general_photo_info",
        confidence=0.45,
        summary="",
        detected_text="",
        risk_flags=[],
        requires_handoff=False,
    )

    response = build_media_policy_response(language="tr", analysis=analysis)
    assert response.internal_json.state == "NEEDS_VERIFICATION"
    assert response.internal_json.required_questions == ["image_context"]


def test_price_check_photo_routes_to_live_quote_verification() -> None:
    """Price-check screenshots should ask for live quote verification details."""
    analysis = VisionAnalysisResult(
        intent="general_photo_info",
        confidence=0.86,
        summary="hotel booking page with room prices in EUR",
        detected_text="EUR 784",
        risk_flags=[],
        requires_handoff=False,
    )

    response = build_media_policy_response(
        language="tr",
        analysis=analysis,
        user_text="Bu fiyatlar dogru mu?",
    )
    assert response.internal_json.intent == "stay_quote"
    assert response.internal_json.state == "NEEDS_VERIFICATION"
    assert response.internal_json.required_questions == ["checkin_date", "checkout_date", "adults"]
    assert "canli fiyati hemen kontrol edebilirim" in response.user_message


def test_general_meta_summary_is_not_echoed_back() -> None:
    """Meta summaries from vision model should not be echoed to the guest."""
    analysis = VisionAnalysisResult(
        intent="general_photo_info",
        confidence=0.7,
        summary="The guest is inquiring about the accuracy of the displayed prices.",
        detected_text="",
        risk_flags=[],
        requires_handoff=False,
    )

    response = build_media_policy_response(language="tr", analysis=analysis)
    assert "The guest is inquiring" not in response.user_message
