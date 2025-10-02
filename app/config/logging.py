"""
Centralized logging configuration for the application.
"""
import sys
import os
from loguru import logger

from app.config.config import config, root_dir


def setup_logging():
    """
    Set up the logger for the entire application.
    """
    logger.remove()
    log_level = config.log_level.upper()

    def format_record(record):
        # Get relative path
        file_path = record["file"].path
        relative_path = os.path.relpath(file_path, root_dir)
        record["file"].path = f"./{relative_path}"

        # Ensure message doesn't contain full root_dir path
        record["message"] = record["message"].replace(root_dir, ".")

        _format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        if record["exception"]:
            _format += "\n{exception}"

        return _format + "\n"

    logger.add(sys.stdout, level=log_level, format=format_record, colorize=True)
    logger.info(f"Logger initialized with level: {log_level}")