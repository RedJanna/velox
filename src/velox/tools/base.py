"""Base abstractions and dispatcher for tool execution."""

from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class BaseTool(ABC):
    """Base class for all tool implementations."""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool with keyword arguments."""

    @staticmethod
    def validate_required(kwargs: dict[str, Any], required: list[str]) -> None:
        """Raise ValueError if required fields are absent or None."""
        missing = [key for key in required if key not in kwargs or kwargs[key] is None]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")


class ToolDispatcher:
    """Map tool names to implementations and execute safely."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, name: str, tool: BaseTool) -> None:
        """Register a tool implementation."""
        self._tools[name] = tool

    def registered_names(self) -> list[str]:
        """Get sorted registered tool names."""
        return sorted(self._tools.keys())

    async def dispatch(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Run a tool and return structured result/error dict."""
        tool = self._tools.get(name)
        if tool is None:
            return {"error": f"Unknown tool: {name}"}

        try:
            return await tool.execute(**kwargs)
        except Exception as error:
            logger.warning("tool_dispatch_failed", tool=name, error_type=type(error).__name__)
            return {"error": str(error), "tool": name}
