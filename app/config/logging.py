"""
Centralized logging configuration for the application.
"""
import sys
import os
from loguru import logger
from datetime import datetime

from app.config.config import config, root_dir


def setup_logging():
    """
    Set up the logger for the entire application with enhanced features.
    - Console output with colors
    - File rotation (daily, with retention)
    - Error-specific log files
    - JSON format for production
    """
    logger.remove()
    log_level = config.log_level.upper()
    log_dir = os.path.join(root_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

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

    # Console output (colorized)
    logger.add(sys.stdout, level=log_level, format=format_record, colorize=True)

    # General log file (rotation daily, keep 30 days)
    logger.add(
        os.path.join(log_dir, "app_{time:YYYY-MM-DD}.log"),
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="00:00",  # 매일 자정에 rotation
        retention="30 days",  # 30일간 보관
        compression="zip",  # 압축 보관
        encoding="utf-8",
    )

    # Error-only log file (rotation 100MB, keep 10 files)
    logger.add(
        os.path.join(log_dir, "errors.log"),
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        rotation="100 MB",
        retention=10,
        compression="zip",
        encoding="utf-8",
    )

    # JSON format for production analysis
    logger.add(
        os.path.join(log_dir, "app_json_{time:YYYY-MM-DD}.log"),
        level=log_level,
        format="{message}",
        rotation="00:00",
        retention="7 days",
        compression="zip",
        serialize=True,  # JSON 형식으로 직렬화
        encoding="utf-8",
    )

    logger.info(f"Logger initialized with level: {log_level}")
    logger.info(f"Log directory: {log_dir}")