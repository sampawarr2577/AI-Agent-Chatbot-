# logger.py

from loguru import logger
import sys
from pathlib import Path

# Remove default handlers
logger.remove()

# Console log format with file name and line number
CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level:<8}</level> | "
    "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
    "({file.name}) - <level>{message}</level>"
)

# File log format with file path and line number
FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | "
    "{module}:{function}:{line} ({file.path}) - {message}"
)

# Ensure the log directory exists
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Add a stdout handler
logger.add(
    sys.stdout,
    format=CONSOLE_FORMAT,
    level="DEBUG",
    colorize=True,
    backtrace=True,    # Capture full stack trace
    diagnose=True,     # Show local variables in tracebacks
)

# Add a rolling file handler
logger.add(
    log_dir / "app.log",
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    level="DEBUG",
    format=FILE_FORMAT,
    backtrace=True,
    diagnose=True,
)

__all__ = ["logger"]
