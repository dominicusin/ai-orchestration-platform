"""Logging utilities"""

import logging
import sys
from datetime import datetime


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str) -> logging.Logger:
    """Get logger"""
    return logging.getLogger(name)


class StructuredLogger:
    """Structured logging"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log(self, level: str, message: str, **kwargs):
        msg = f"{message} | {kwargs}" if kwargs else message
        getattr(self.logger, level.lower())(msg)


class LogFormat:
    """Log format helper"""
    @staticmethod
    def format(msg: str) -> str:
        return f"[{datetime.now().isoformat()}] {msg}"