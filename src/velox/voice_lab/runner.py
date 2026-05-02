"""Deterministic Voice Lab runner for pre-live phone assistant checks."""

import re
import unicodedata
from collections.abc import Sequence
from difflib import SequenceMatcher
from time import perf_counter

from velox.config.constants import RiskFlag
from velox.models.hotel_profile import FAQEntry, FAQStatus, HotelProfile
from velox.voice_lab.models import (
    VoiceLabAction,
    VoiceLabResult,
    VoiceLabRunRequest,
    VoiceLabRunResult,
    VoiceLabScenario,
    VoiceLabSource,
)
from velox.voice_lab.scenarios import get_voice_lab_scenarios

_CHAR_NORMALIZATION_TABLE = str.maketrans({"ı": "i", "ß": "ss"})
_CARD_PATTERN = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\s().-]?){10,15}(?!\d)")


class VoiceLabRunner:
    """Run Voice Lab text scenarios against HOTEL_PROFILE-backed rules."""

    def __init__(
        self,
        profile: HotelProfile,
        scenarios: Sequence[VoiceLabScenario] | None = None,
    ) -> None:
        self._profile = profile
        self._scenarios = tuple(scenarios or get_voice_lab_scenarios())

    def run(self, request: VoiceLabRunRequest) -> VoiceLabRunResult:
        """Run one text transcript through the deterministic Voice Lab pipeline."""
        if request.hotel_id != self._profile.hotel_id:
            raise ValueError("request.hotel_id does not match runner profile")

        started = perf_counter()
        redacted_transcript = _redact_sensitive(request.transcript)
        normalized_text = _normalize_text(redacted_transcript)

        pii_result = self._maybe_block_sensitive_input(
            redacted_transcript=redacted_transcript,
            normalized_text=normalized_text,
            language=request.language,
            started=started,
        )
        if pii_result is not None:
            return pii_result

        scenario, match_score = self._match_scenario(normalized_text, request.scenario_id)
        if scenario is None:
            return self._unknown_result(
                redacted_transcript=redacted_transcript,
                normalized_text=normalized_text,
                language=request.language,
                started=started,
            )

        if scenario.expected_action == VoiceLabAction.TOOL_REQUIRED:
            result = self._tool_required_result(scenario, request, redacted_transcript, normalized_text, match_score)
        elif scenario.expected_action == VoiceLabAction.HANDOFF:
            result = self._handoff_result(scenario, request, redacted_transcript, normalized_text, match_score)
        else:
            result = self._profile_answer_result(scenario, request, redacted_transcript, normalized_text, match_score)

        result.latency_ms = _latency_payload(started)
        result.violations = self._evaluate_result(scenario, result)
        result.result = VoiceLabResult.FAIL if result.violations else VoiceLabResult.PASS
        return result

    def run_text(
        self,
        transcript: str,
        *,
        language: str = "tr",
        scenario_id: str | None = None,
    ) -> VoiceLabRunResult:
        """Convenience wrapper for a single transcript."""
        return self.run(
            VoiceLabRunRequest(
                hotel_id=self._profile.hotel_id,
                transcript=transcript,
                language=language,
                scenario_id=scenario_id,
            )
        )

    def run_matrix(self, *, language: str = "tr") -> list[VoiceLabRunResult]:
        """Run all scenarios with their sample inputs."""
        return [
            self.run_text(
                scenario.sample_input,
                language=language,
                scenario_id=scenario.scenario_id,
            )
            for scenario in self._scenarios
        ]

    def _match_scenario(
        self,
        normalized_text: str,
        scenario_id: str | None,
    ) -> tuple[VoiceLabScenario | None, float]:
        if scenario_id is not None:
            for scenario in self._scenarios:
                if scenario.scenario_id == scenario_id:
                    return scenario, 1.0
            return None, 0.0

        best_scenario: VoiceLabScenario | None = None
        best_score = 0.0
        for scenario in self._scenarios:
            candidates = (scenario.sample_input, *scenario.aliases)
            score = max(_similarity(normalized_text, _normalize_text(candidate)) for candidate in candidates)
            if score > best_score:
                best_score = score
                best_scenario = scenario

        if best_score < 0.55:
            return None, best_score
        return best_scenario, round(best_score, 3)

    def _profile_answer_result(
        self,
        scenario: VoiceLabScenario,
        request: VoiceLabRunRequest,
        redacted_transcript: str,
        normalized_text: str,
        match_score: float,
    ) -> VoiceLabRunResult:
        response_text, source_detail = self._build_profile_answer(scenario, request.language)
        return VoiceLabRunResult(
            hotel_id=self._profile.hotel_id,
            scenario_id=scenario.scenario_id,
            input_transcript=redacted_transcript,
            normalized_text=normalized_text,
            language_detected=request.language.casefold(),
            intent=scenario.expected_intent,
            source_type=VoiceLabSource.HOTEL_PROFILE if response_text else VoiceLabSource.UNKNOWN,
            source_detail=source_detail,
            action=scenario.expected_action,
            tool_required=False,
            tool_called=False,
            tool_name=None,
            handoff_required=False,
            risk_flags=[],
            response_text=response_text or _fallback_handoff_response(),
            result=VoiceLabResult.PASS,
            match_score=match_score,
        )

    def _tool_required_result(
        self,
        scenario: VoiceLabScenario,
        request: VoiceLabRunRequest,
        redacted_transcript: str,
        normalized_text: str,
        match_score: float,
    ) -> VoiceLabRunResult:
        return VoiceLabRunResult(
            hotel_id=self._profile.hotel_id,
            scenario_id=scenario.scenario_id,
            input_transcript=redacted_transcript,
            normalized_text=normalized_text,
            language_detected=request.language.casefold(),
            intent=scenario.expected_intent,
            source_type=VoiceLabSource.TOOL,
            source_detail=scenario.required_tool or "tool",
            action=VoiceLabAction.TOOL_REQUIRED,
            tool_required=True,
            tool_called=False,
            tool_name=scenario.required_tool,
            handoff_required=False,
            risk_flags=[],
            response_text=(
                "Bu bilgi icin resmi rezervasyon sisteminden kontrol saglamam gerekiyor. "
                "Tarih, kisi sayisi ve talebinizi netlestirerek kontrol edelim."
            ),
            result=VoiceLabResult.PASS,
            match_score=match_score,
        )

    def _handoff_result(
        self,
        scenario: VoiceLabScenario,
        request: VoiceLabRunRequest,
        redacted_transcript: str,
        normalized_text: str,
        match_score: float,
    ) -> VoiceLabRunResult:
        return VoiceLabRunResult(
            hotel_id=self._profile.hotel_id,
            scenario_id=scenario.scenario_id,
            input_transcript=redacted_transcript,
            normalized_text=normalized_text,
            language_detected=request.language.casefold(),
            intent=scenario.expected_intent,
            source_type=VoiceLabSource.HANDOFF,
            source_detail="human_handoff",
            action=VoiceLabAction.HANDOFF,
            tool_required=False,
            tool_called=False,
            tool_name=None,
            handoff_required=True,
            risk_flags=list(scenario.risk_flags),
            response_text=(
                "Bu konuda kesin bilgi vermemem gerekiyor. Sizi ilgili ekibe aktariyorum; "
                "ekibimiz talebinizi kontrol ederek yardimci olacak."
            ),
            result=VoiceLabResult.PASS,
            match_score=match_score,
        )

    def _maybe_block_sensitive_input(
        self,
        *,
        redacted_transcript: str,
        normalized_text: str,
        language: str,
        started: float,
    ) -> VoiceLabRunResult | None:
        has_card_data = "[REDACTED_CARD]" in redacted_transcript
        has_payment_secret = "cvv" in normalized_text or "otp" in normalized_text
        if not has_card_data and not has_payment_secret:
            return None

        return VoiceLabRunResult(
            hotel_id=self._profile.hotel_id,
            scenario_id=None,
            input_transcript=redacted_transcript,
            normalized_text=normalized_text,
            language_detected=language.casefold(),
            intent="sensitive_payment_data",
            source_type=VoiceLabSource.HANDOFF,
            source_detail="security_privacy",
            action=VoiceLabAction.HANDOFF,
            tool_required=False,
            tool_called=False,
            tool_name=None,
            handoff_required=True,
            risk_flags=[RiskFlag.PII_OVERREQUEST.value, RiskFlag.PAYMENT_CONFUSION.value],
            response_text=(
                "Kart, CVV veya tek kullanimlik sifre bilgisi alamam. Guvenliginiz icin "
                "bu bilgiyi paylasmayin; sizi ilgili ekibe aktariyorum."
            ),
            result=VoiceLabResult.BLOCKED,
            match_score=0.0,
            latency_ms=_latency_payload(started),
        )

    def _unknown_result(
        self,
        *,
        redacted_transcript: str,
        normalized_text: str,
        language: str,
        started: float,
    ) -> VoiceLabRunResult:
        return VoiceLabRunResult(
            hotel_id=self._profile.hotel_id,
            scenario_id=None,
            input_transcript=redacted_transcript,
            normalized_text=normalized_text,
            language_detected=language.casefold(),
            intent="unknown",
            source_type=VoiceLabSource.UNKNOWN,
            source_detail="scenario_match",
            action=VoiceLabAction.CLARIFY,
            tool_required=False,
            tool_called=False,
            tool_name=None,
            handoff_required=False,
            risk_flags=[],
            response_text="Sizi tam olarak anlayamadim. Talebinizi bir kez daha kisaca paylasabilir misiniz?",
            result=VoiceLabResult.BLOCKED,
            match_score=0.0,
            latency_ms=_latency_payload(started),
            violations=["No matching Voice Lab scenario found."],
        )

    def _build_profile_answer(self, scenario: VoiceLabScenario, language: str) -> tuple[str, str]:
        topic = scenario.topic
        if topic == "transfer_routes":
            return self._format_transfer_routes(), "HOTEL_PROFILE.transfer_routes"
        if topic == "board_types":
            return self._format_board_types(scenario), "HOTEL_PROFILE.board_types"
        if topic == "payment_methods":
            return self._format_payment_methods(language), "HOTEL_PROFILE.payment"
        if topic is None:
            return "", "HOTEL_PROFILE"

        faq_entry = self._faq_entry_by_topic(topic)
        if faq_entry is None:
            return "", f"HOTEL_PROFILE.faq_data.{topic}"
        return _faq_answer(faq_entry, language), f"HOTEL_PROFILE.faq_data.{topic}"

    def _faq_entry_by_topic(self, topic: str) -> FAQEntry | None:
        for entry in self._profile.faq_data:
            if entry.topic == topic and entry.status == FAQStatus.ACTIVE:
                return entry
        return None

    def _format_transfer_routes(self) -> str:
        incoming_routes = [
            route
            for route in self._profile.transfer_routes
            if route.route_code.endswith("_AIRPORT_TO_HOTEL")
        ]
        routes = incoming_routes or self._profile.transfer_routes
        if not routes:
            return _fallback_handoff_response()

        currency = self._profile.currency_base
        parts = []
        for route in routes:
            price = int(route.price_eur) if route.price_eur.is_integer() else route.price_eur
            parts.append(
                f"{route.from_location}: tek yon {price} {currency}, max {route.max_pax} kisi, "
                f"yaklasik {route.duration_min} dk"
            )
        return "Havalimani transferi mevcuttur. " + "; ".join(parts) + "."

    def _format_board_types(self, scenario: VoiceLabScenario) -> str:
        if not self._profile.board_types:
            return _fallback_handoff_response()

        board = self._profile.board_types[0]
        board_name = board.name.tr or board.name.en
        breakfast_hours = ""
        if board.model_extra is not None:
            breakfast_hours = str(board.model_extra.get("breakfast_hours", "") or "")

        prefix = ""
        if "her sey" in _normalize_text(scenario.sample_input):
            prefix = "Her sey dahil konseptimiz bulunmuyor. "

        detail = f"Konseptimiz {board_name} ({board.code})"
        if breakfast_hours:
            detail += f"; kahvalti saatleri {breakfast_hours}"
        return prefix + detail + "."

    def _format_payment_methods(self, language: str) -> str:
        reply_key = "reply_tr" if language.casefold() == "tr" else "reply_en"
        reply = str(self._profile.payment.get(reply_key, "") or "")
        if reply:
            return reply

        methods = ", ".join(str(method) for method in self._profile.payment.get("methods", []))
        if not methods:
            return _fallback_handoff_response()
        return f"Odeme yontemleri: {methods}. Detay icin ilgili ekibimiz yardimci olur."

    def _evaluate_result(self, scenario: VoiceLabScenario, result: VoiceLabRunResult) -> list[str]:
        violations: list[str] = []
        if result.intent != scenario.expected_intent:
            violations.append(f"intent mismatch: expected={scenario.expected_intent} actual={result.intent}")
        if result.source_type != scenario.expected_source:
            violations.append(f"source mismatch: expected={scenario.expected_source} actual={result.source_type}")
        if result.action != scenario.expected_action:
            violations.append(f"action mismatch: expected={scenario.expected_action} actual={result.action}")
        if scenario.required_tool and result.tool_name != scenario.required_tool:
            violations.append(f"tool mismatch: expected={scenario.required_tool} actual={result.tool_name}")
        for risk_flag in scenario.risk_flags:
            if risk_flag not in result.risk_flags:
                violations.append(f"missing risk flag: {risk_flag}")

        normalized_response = _normalize_text(result.response_text)
        for term in scenario.acceptance_terms:
            if _normalize_text(term) not in normalized_response:
                violations.append(f"missing acceptance term: {term}")
        for term in scenario.forbidden_terms:
            if _normalize_text(term) in normalized_response:
                violations.append(f"forbidden term present: {term}")
        return violations


def _faq_answer(entry: FAQEntry, language: str) -> str:
    if language.casefold() == "tr":
        return entry.answer_tr
    return entry.answer_en or entry.answer_tr


def _fallback_handoff_response() -> str:
    return "Bu bilgi icin sizi ilgili ekibe yonlendiriyorum."


def _redact_sensitive(value: str) -> str:
    redacted = _EMAIL_PATTERN.sub("[REDACTED_EMAIL]", value)
    redacted = _CARD_PATTERN.sub("[REDACTED_CARD]", redacted)
    return _PHONE_PATTERN.sub("[REDACTED_PHONE]", redacted)


def _normalize_text(value: str) -> str:
    folded = value.casefold().translate(_CHAR_NORMALIZATION_TABLE).strip()
    decomposed = unicodedata.normalize("NFKD", folded)
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(stripped.split())


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(a=left, b=right).ratio()


def _latency_payload(started: float) -> dict[str, int]:
    total_ms = max(0, round((perf_counter() - started) * 1000))
    return {
        "stt": 0,
        "llm_tool": total_ms,
        "qc": 0,
        "tts": 0,
        "total": total_ms,
    }
