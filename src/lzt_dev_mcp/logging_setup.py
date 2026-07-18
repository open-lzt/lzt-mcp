"""structlog setup for the MCP server.

Logs go to stderr — in stdio transport mode stdout carries the MCP protocol and must stay clean.
Pretty coloured console by default; set ``LZT_LOG_JSON=1`` for JSON lines.
"""

from __future__ import annotations

import logging
import os
import sys

import structlog


def configure_logging() -> None:
    json_mode = os.environ.get("LZT_LOG_JSON", "").lower() in {"1", "true", "yes"}
    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if json_mode
        else structlog.dev.ConsoleRenderer(colors=True)
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=True),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )
