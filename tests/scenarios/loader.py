"""Load scenario YAML files from data/scenarios/ directory."""

from pathlib import Path
from typing import Any

import yaml


SCENARIOS_DIR = Path(__file__).resolve().parents[2] / "data" / "scenarios"


def load_scenario(file_path: Path) -> dict[str, Any]:
    """Load a single scenario YAML file and return as dict."""
    with open(file_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_all_scenarios(
    directory: Path = SCENARIOS_DIR,
    category: str | None = None,
    codes: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Load all scenario YAML files from directory.

    Args:
        directory: Path to scenarios folder.
        category: Filter by category (stay, restaurant, transfer, etc.).
        codes: Filter by scenario codes (["S001", "S009"]).

    Returns:
        List of scenario dicts sorted by code.
    """
    scenarios: list[dict[str, Any]] = []

    for yaml_file in sorted(directory.glob("S*.yaml")):
        scenario = load_scenario(yaml_file)
        if scenario is None:
            continue

        if category and scenario.get("category") != category:
            continue

        if codes and scenario.get("code") not in codes:
            continue

        scenarios.append(scenario)

    return scenarios


def scenario_to_runner_format(scenario: dict[str, Any]) -> dict[str, Any]:
    """Convert YAML scenario format to runner-compatible dict.

    YAML format uses 'user' key, runner expects 'steps' with specific keys.
    This function bridges the two formats.
    """
    steps: list[dict[str, Any]] = []

    for step in scenario.get("steps", []):
        runner_step: dict[str, Any] = {
            "user": step["user"],
        }

        if "expect_intent" in step:
            runner_step["expect_intent"] = step["expect_intent"]
        if "expect_state" in step:
            runner_step["expect_state"] = step["expect_state"]
        if "expect_tool_calls" in step:
            runner_step["expect_tool_calls"] = step["expect_tool_calls"]
        if "expect_reply_contains" in step:
            runner_step["expect_reply_contains"] = step["expect_reply_contains"]
        if "expect_reply_must_not" in step:
            runner_step["expect_reply_must_not"] = step["expect_reply_must_not"]
        if "expect_risk_flags" in step:
            runner_step["expect_risk_flags"] = step["expect_risk_flags"]

        steps.append(runner_step)

    return {
        "code": scenario.get("code", ""),
        "name": scenario.get("name", ""),
        "steps": steps,
    }
