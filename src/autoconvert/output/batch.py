"""Batch processing orchestration."""

import time
from pathlib import Path

from autoconvert.core.models import BatchSummary
from autoconvert.ingestion.discovery import discover_files
from autoconvert.logging.messages import log_file_progress, log_startup
from autoconvert.output.file_processor import process_file
from autoconvert.output.reporter import report_batch_summary
from autoconvert.setup.config import Config


def process_batch(config: Config) -> BatchSummary:
    """Process all Excel files in data folder.

    Args:
        config (Config): Application configuration.

    Returns:
        BatchSummary: Summary of batch processing results.
    """
    summary = BatchSummary()
    start_time = time.time()

    # Discover files
    files = discover_files(config.data_folder)
    summary.total_files = len(files)

    # Log startup
    log_startup(
        version="1.0.0",
        input_folder=config.data_folder.absolute(),
        output_folder=config.output_folder.absolute(),
        currency_count=len(config.currency_rules),
        country_count=len(config.country_rules),
        file_count=len(files),
    )

    # Process each file
    for idx, file_path in enumerate(files, start=1):
        log_file_progress(idx, len(files), file_path.name)

        result = process_file(file_path, config)

        # Update summary
        if result.status == "SUCCESS":
            summary.success_count += 1
        elif result.status == "ATTENTION":
            summary.attention_count += 1
            summary.attention_files[file_path.name] = [
                f"[{code}] {msg}" for code, msg in result.warnings
            ]
        else:  # FAILED
            summary.failed_count += 1
            summary.failed_files[file_path.name] = [
                f"[{code}] {msg}" for code, msg in result.errors
            ]

    # Calculate processing time
    summary.processing_time = time.time() - start_time

    # Report summary
    log_file_path = Path("process_log.txt").absolute()
    report_batch_summary(summary, log_file_path)

    return summary
