"""Logging module - dual console/file logging."""

from autoconvert.logging.logger import setup_logging
from autoconvert.logging.messages import (
    log_batch_summary,
    log_error_code,
    log_extraction,
    log_file_progress,
    log_packing_totals,
    log_startup,
    log_status,
    log_warning_code,
)

__all__ = [
    "setup_logging",
    "log_batch_summary",
    "log_error_code",
    "log_extraction",
    "log_file_progress",
    "log_packing_totals",
    "log_startup",
    "log_status",
    "log_warning_code",
]
