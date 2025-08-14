from loguru import logger
import sys
from pathlib import Path

logger.remove()

# Console logging
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
    level="DEBUG",  
    colorize=True
)

# File logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logger.add(
    log_dir / "app.log",
    rotation="10 MB",      
    retention="10 days",    
    compression="zip",      
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# Export logger so other modules can use it
__all__ = ["logger"]
