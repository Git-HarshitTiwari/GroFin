"""
Logging configuration for GroFin.

This module owns logging setup for the entire application.
It writes readable logs to the terminal and detailed logs to a file.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler


APP_NAME = "GroFin"
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "grofin.log"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    file_level: int = logging.INFO,
    console_level: int = logging.WARNING,
) -> logging.Logger:
    """
    Configure and return the root GroFin logger.

    The function is safe to call multiple times because it clears old handlers
    before attaching fresh console and file handlers.
    """

    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger(APP_NAME)
    logger.setLevel(min(file_level, console_level))
    logger.propagate = False
    logger.handlers.clear()

    console_handler = RichHandler(
        rich_tracebacks=True,
        show_time=False,
        show_path=False,
        markup=True,
    )
    console_handler.setLevel(console_level)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.debug("GroFin logging configured successfully.")
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger under the GroFin logger namespace.
    """

    return logging.getLogger(f"{APP_NAME}.{name}")
