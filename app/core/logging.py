import logging
import sys
from typing import Optional
from config.settings import get_settings


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration"""
    settings = get_settings()

    level = log_level or settings.log_level

    # Create logger
    logger = logging.getLogger("ai_ride_booking")
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Create formatter
    formatter = logging.Formatter(settings.log_format)
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Prevent duplicate logs
    logger.propagate = False

    return logger


def get_logger(name: str = "ai_ride_booking") -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)