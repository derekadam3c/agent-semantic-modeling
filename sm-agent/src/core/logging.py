"""Logging configuration."""

import logging
import sys
from typing import Optional

from rich.logging import RichHandler
from .config import settings


def setup_logging(level: Optional[str] = None) -> None:
    """Configure logging with Rich handler."""
    log_level = level or settings.log_level
    
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)]
    )
    
    # Azure SDK logging
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
        logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
