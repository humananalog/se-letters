"""Logging utilities for the SE Letters project."""

import logging
import sys
from pathlib import Path
from typing import Optional

from loguru import logger as loguru_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.
    
    Args:
        name: Logger name (usually __name__).
        
    Returns:
        Logger instance.
    """
    return logging.getLogger(name)


def setup_logging(
    log_file: Optional[Path] = None,
    log_level: str = "INFO",
    verbose: bool = False,
) -> None:
    """Setup logging configuration.
    
    Args:
        log_file: Path to log file. If None, uses default.
        log_level: Logging level.
        verbose: Enable verbose logging.
    """
    # Remove default loguru handler
    loguru_logger.remove()
    
    # Set level based on verbose flag
    if verbose:
        level = "DEBUG"
    else:
        level = log_level.upper()
    
    # Console handler
    format_str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    loguru_logger.add(
        sys.stderr,
        level=level,
        format=format_str,
        colorize=True,
    )
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        loguru_logger.add(
            log_file,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | "
                   "{level: <8} | "
                   "{name}:{function}:{line} - "
                   "{message}",
            rotation="10 MB",
            retention="1 week",
            compression="gz",
        )
    
    # Configure standard logging to use loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = loguru_logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            
            loguru_logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    # Set up intercept handler for standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Silence some noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING) 