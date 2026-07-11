"""
Logging Configuration Module
Provides centralized, consistent logging across the application.
Implements SRP by separating logging setup from logger creation.
"""
import logging
import os
import sys
from pathlib import Path

# Ensure backend directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try relative import first (when imported as module)
    from . import config
except ImportError:
    # Fall back to absolute import (when run as main)
    import config

from constants import LOG_DIR, LOG_FILE_PATH, LOG_FORMAT, LOG_LEVEL_DEFAULT, LOGGER_NAME


def _create_logger(name: str) -> logging.Logger:
    """
    Create and configure a logger instance
    
    Args:
        name: Logger name (typically module name)
        
    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    return logger


def _ensure_log_directory_exists() -> None:
    """Create logs directory if it doesn't exist"""
    log_dir = Path(LOG_FILE_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)


def _create_file_handler() -> logging.FileHandler:
    """Create file handler for logging to file"""
    file_handler = logging.FileHandler(LOG_FILE_PATH)
    file_handler.setLevel(getattr(logging, LOG_LEVEL_DEFAULT))
    return file_handler


def _create_console_handler() -> logging.StreamHandler:
    """Create console handler for logging to stdout"""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL_DEFAULT))
    return console_handler


def _create_formatter() -> logging.Formatter:
    """Create log formatter"""
    return logging.Formatter(LOG_FORMAT)


def _add_handlers_to_logger(logger: logging.Logger, handlers: list) -> None:
    """
    Add multiple handlers to logger
    
    Args:
        logger: Target logger instance
        handlers: List of handlers to add
    """
    for handler in handlers:
        logger.addHandler(handler)


def setup_logging() -> logging.Logger:
    """
    Initialize and configure logging for the application
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Ensure log directory exists
    _ensure_log_directory_exists()
    
    # Create logger
    logger = _create_logger(LOGGER_NAME)
    logger.setLevel(getattr(logging, LOG_LEVEL_DEFAULT))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create handlers
    file_handler = _create_file_handler()
    console_handler = _create_console_handler()
    
    # Create formatter and apply to handlers
    formatter = _create_formatter()
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    _add_handlers_to_logger(logger, [file_handler, console_handler])
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Name of the logger (typically __name__)
    
    Returns:
        logging.Logger: Logger instance
    """
    logger = _create_logger(f"{LOGGER_NAME}.{name}")
    if not logger.handlers:
        setup_logging()
    return logger


# Initialize default logger
logger = setup_logging()


def log_info(message: str, *args, **kwargs) -> None:
    """Log info level message"""
    logger.info(message, *args, **kwargs)


def log_warning(message: str, *args, **kwargs) -> None:
    """Log warning level message"""
    logger.warning(message, *args, **kwargs)


def log_error(message: str, *args, **kwargs) -> None:
    """Log error level message"""
    logger.error(message, *args, **kwargs)


def log_debug(message: str, *args, **kwargs) -> None:
    """Log debug level message"""
    logger.debug(message, *args, **kwargs)


def log_critical(message: str, *args, **kwargs) -> None:
    """Log critical level message"""
    logger.critical(message, *args, **kwargs)
