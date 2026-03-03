"""Structured logging setup using structlog JSON output."""

import logging

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """Configure application logging with JSON rendering."""
    resolved_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(level=resolved_level, format="%(message)s")

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
