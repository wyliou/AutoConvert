"""Logging setup for AutoConvert.

Provides dual-output logging:
- Console: INFO level, [LEVEL] message format, UTF-8
- File: DEBUG level, [HH:MM] [LEVEL] message format, UTF-8 with BOM
"""

import logging
import sys
import warnings
from pathlib import Path


class ConsoleFormatter(logging.Formatter):
    """Formatter for console output: [LEVEL] message."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console.

        Args:
            record (logging.LogRecord): The log record.

        Returns:
            str: Formatted message.
        """
        return f"[{record.levelname}] {record.getMessage()}"


class FileFormatter(logging.Formatter):
    """Formatter for file output: [HH:MM] [LEVEL] message."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for file.

        Args:
            record (logging.LogRecord): The log record.

        Returns:
            str: Formatted message with timestamp.
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M")
        return f"[{timestamp}] [{record.levelname}] {record.getMessage()}"


def setup_logging(log_file_path: Path | None = None) -> logging.Logger:
    """Set up dual-output logging.

    Args:
        log_file_path (Path | None): Path to log file. If None, defaults to process_log.txt.

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Suppress third-party library warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

    # Set UTF-8 encoding for stdout/stderr
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
        except AttributeError:
            pass

    if sys.stderr.encoding != "utf-8":
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
        except AttributeError:
            pass

    logger = logging.getLogger("autoconvert")
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler - INFO level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ConsoleFormatter())
    logger.addHandler(console_handler)

    # File handler - DEBUG level
    if log_file_path is None:
        log_file_path = Path("process_log.txt")

    # Write with UTF-8 BOM
    file_handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8-sig")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(FileFormatter())
    logger.addHandler(file_handler)

    return logger


def get_logger() -> logging.Logger:
    """Get the autoconvert logger.

    Returns:
        logging.Logger: The logger instance.
    """
    return logging.getLogger("autoconvert")
