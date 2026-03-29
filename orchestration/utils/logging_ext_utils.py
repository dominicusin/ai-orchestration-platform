"""Logging extended utilities"""

import logging


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get configured logger"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


def setup_file_handler(logger: logging.Logger, filename: str, level: int = logging.INFO):
    """Add file handler to logger"""
    handler = logging.FileHandler(filename)
    handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_exception(logger: logging.Logger, e: Exception, message: str = "Error occurred"):
    """Log exception with traceback"""
    logger.exception(f"{message}: {e}")
