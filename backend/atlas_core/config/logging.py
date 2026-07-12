"""Structured logging configuration.

Atlas uses ``structlog`` so every log line carries structured context (agent
ids, tick numbers, districts) that stays greppable in development and becomes
machine-parseable JSON in production. Call :func:`configure_logging` once at
process startup; obtain loggers everywhere else with :func:`get_logger`.
"""

from __future__ import annotations

import logging
import sys

import structlog

from atlas_core.config.settings import get_settings

_configured = False


def configure_logging(level: str | None = None, *, json_output: bool | None = None) -> None:
    """Configure the standard library and structlog pipelines.

    Idempotent: repeated calls (e.g. from multiple entrypoints or test setup)
    reconfigure cleanly rather than stacking handlers.

    Args:
        level: Log level name; defaults to ``settings.log_level``.
        json_output: Emit JSON when ``True``, human-readable console output when
            ``False``; defaults to ``settings.log_json``.
    """
    global _configured
    settings = get_settings()
    level = (level or settings.log_level).upper()
    json_output = settings.log_json if json_output is None else json_output

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level, logging.INFO),
        force=True,
    )

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if json_output
        else structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level, logging.INFO)),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    _configured = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger, configuring logging on first use."""
    if not _configured:
        configure_logging()
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger
