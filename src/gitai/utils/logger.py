"""Logging configuration for GitAI."""

import logging
import sys
from typing import Any


def setup_logger(name: str, level: str = "WARNING") -> logging.Logger:
    """Setup structured logger for GitAI components.

    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Configure root gitai logger with handler
    root_logger = logging.getLogger("gitai")
    if not root_logger.handlers:
        root_logger.setLevel(getattr(logging, level.upper()))

        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    return logger


def log_with_context(
    logger: logging.Logger, level: str, message: str, **context: Any
) -> None:
    """Log message with structured context.

    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        **context: Additional context data
    """
    # Convert context to extra dict for structured logging
    extra_context = {f"ctx_{k}": v for k, v in context.items()}

    log_func = getattr(logger, level.lower())
    log_func(message, extra=extra_context)
