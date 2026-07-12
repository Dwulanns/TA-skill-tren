"""
Logging Configuration Module
Provides centralized, consistent logging across the application.
Compatible with local development and Vercel Serverless.
"""

import logging
import os
import sys
from pathlib import Path

# Ensure backend directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from . import config
except ImportError:
    import config

from constants import (
    LOG_FILE_PATH,
    LOG_FORMAT,
    LOG_LEVEL_DEFAULT,
    LOGGER_NAME,
)

# Detect Vercel environment
IS_VERCEL = os.getenv("VERCEL") == "1"


def _create_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def _ensure_log_directory_exists() -> None:
    """Create logs directory only for local development."""
    if IS_VERCEL:
        return

    log_dir = Path(LOG_FILE_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)


def _create_file_handler():
    """Create file handler (disabled on Vercel)."""
    if IS_VERCEL:
        return None

    handler = logging.FileHandler(LOG_FILE_PATH)
    handler.setLevel(getattr(logging, LOG_LEVEL_DEFAULT))
    return handler


def _create_console_handler():
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, LOG_LEVEL_DEFAULT))
    return handler


def _create_formatter():
    return logging.Formatter(LOG_FORMAT)


def setup_logging() -> logging.Logger:

    logger = _create_logger(LOGGER_NAME)
    logger.setLevel(getattr(logging, LOG_LEVEL_DEFAULT))

    if logger.handlers:
        logger.handlers.clear()

    formatter = _create_formatter()

    console_handler = _create_console_handler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if not IS_VERCEL:
        _ensure_log_directory_exists()

        file_handler = _create_file_handler()
        if file_handler:
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"{LOGGER_NAME}.{name}")

    if not logger.handlers:
        logger.handlers.clear()

        formatter = _create_formatter()

        console_handler = _create_console_handler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if not IS_VERCEL:
            _ensure_log_directory_exists()

            file_handler = _create_file_handler()
            if file_handler:
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

        logger.setLevel(getattr(logging, LOG_LEVEL_DEFAULT))

    return logger


logger = setup_logging()


def log_info(message: str, *args, **kwargs):
    logger.info(message, *args, **kwargs)


def log_warning(message: str, *args, **kwargs):
    logger.warning(message, *args, **kwargs)


def log_error(message: str, *args, **kwargs):
    logger.error(message, *args, **kwargs)


def log_debug(message: str, *args, **kwargs):
    logger.debug(message, *args, **kwargs)


def log_critical(message: str, *args, **kwargs):
    logger.critical(message, *args, **kwargs)