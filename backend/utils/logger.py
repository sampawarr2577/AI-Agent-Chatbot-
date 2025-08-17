# logger.py
from loguru import logger
import sys
from pathlib import Path

logger.remove()

CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
    "({file.path}) - <level>{message}</level>"
)

FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
    "{module}:{function}:{line} ({file.path}) - {message}"
)

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logger.add(
    sys.stdout,
    format=CONSOLE_FORMAT,
    level="DEBUG",
    colorize=True,
    backtrace=True,   # important
    diagnose=True,    # shows local variables in traceback
)

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
