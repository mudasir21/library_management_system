"""Logging Configuration Module.

Configures Python's standard logging module to record application actions,
service audit events, and persistence operations to both file and console
(satisfying Section 3.2).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path


def setup_logging(
    log_file_path: str = "library.log",
    level: int = logging.INFO,
    console_output: bool = True,
) -> logging.Logger:
    """Initialize application logging configuration.

    Args:
        log_file_path: Target path for the application log file.
        level: Minimum logging level (default: logging.INFO).
        console_output: Whether to stream logs to stdout/stderr.

    Returns:
        Configured root/base logger for the library package.
    """
    log_dir = Path(log_file_path).parent
    if log_dir and not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger("library")
    root_logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if root_logger.handlers:
        return root_logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler writes to log file
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    root_logger.info("LOGGING_INITIALIZED | Target file: %s", log_file_path)
    return root_logger
