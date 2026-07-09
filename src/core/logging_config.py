"""
Structured logging setup using structlog.

Instead of plain print() or unstructured text logs, every log line becomes
JSON with consistent fields (timestamp, level, request_id, etc.) that log
aggregators like Datadog, CloudWatch, or Grafana Loki can parse and search.
"""

import logging
import sys

import structlog


def setup_logging(*, json_logs: bool = True) -> None:
    """
    Configure structlog + stdlib logging once at application startup.

    Args:
        json_logs: True in production (machine-readable JSON).
                   False in development (colored, human-readable console output).
    """
    # Shared processors run on every log event before rendering.
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,  # picks up request_id bound per-request
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_logs:
        # Production: one JSON object per line — easy to ship to log pipelines.
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        # Development: pretty colors in your terminal.
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Quiet noisy third-party loggers so your app logs stay readable.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
