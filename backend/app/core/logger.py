"""
Logging configuration using Loguru.
Ensures structured, thread-safe, and asynchronous logging.
"""
import sys
import os
from loguru import logger
from app.core.config import settings
from app.core.constants import LOG_FORMAT, LOG_ROTATION, LOG_RETENTION

def setup_logging():
    """
    Initializes Loguru with standard out and file sinks.
    """
    logger.remove()  # Remove default handler
    
    # Ensure log directory exists
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    
    # Console output
    logger.add(
        sys.stdout,
        format=LOG_FORMAT,
        level=settings.LOG_LEVEL,
        colorize=True,
        enqueue=True,
    )
    
    # File output (rotating)
    logger.add(
        f"{settings.LOG_DIR}/vizage_{{time:YYYY-MM-DD}}.log",
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        format=LOG_FORMAT,
        level=settings.LOG_LEVEL,
        enqueue=True,
    )
    
    logger.info(f"Logging initialized at level {settings.LOG_LEVEL}")

def get_logger(name: str):
    """
    Returns a loguru logger bound with the module name.
    """
    return logger.bind(name=name)
