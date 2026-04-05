"""Unit tests for the lightweight metrics registry."""

from velox.utils.metrics import (
    increment_counter,
    record_intent_domain_guard,
    record_prompt_truncation,
    record_structured_output_fallback,
    render_metrics,
    reset_metrics,
)


def setup_function() -> None:
    """Reset global metrics state before each test."""
    reset_metrics()


def test_render_metrics_outputs_prometheus_counter_series() -> None:
    """Counters should render with HELP/TYPE lines and normalized labels."""
    increment_counter(
        "velox_test_counter_total",
        "Synthetic counter for tests.",
        labels={"status": "ok", "component": "unit"},
    )

    output = render_metrics()

    assert "# HELP velox_test_counter_total Synthetic counter for tests." in output
    assert "# TYPE velox_test_counter_total counter" in output
    assert 'velox_test_counter_total{component="unit",status="ok"} 1.0' in output


def test_runtime_metric_helpers_increment_expected_series() -> None:
    """Convenience helpers should populate the expected runtime counters."""
    record_prompt_truncation("system_prompt")
    record_structured_output_fallback("missing_internal_json")
    record_intent_domain_guard(
        "stay_followup_without_restaurant_tools",
        "restaurant_booking_create",
        "stay_availability",
    )

    output = render_metrics()

    assert 'velox_llm_prompt_truncations_total{component="system_prompt"} 1.0' in output
    assert (
        'velox_llm_structured_output_fallback_total{reason="missing_internal_json"} 1.0'
        in output
    )
    assert (
        'velox_llm_intent_domain_guard_total{from_intent="restaurant_booking_create",'
        'reason="stay_followup_without_restaurant_tools",to_intent="stay_availability"} 1.0'
        in output
    )
