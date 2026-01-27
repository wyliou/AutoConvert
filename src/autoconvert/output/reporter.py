"""Batch summary reporting."""

from collections import defaultdict
from pathlib import Path

from autoconvert.core.models import BatchSummary
from autoconvert.logging.messages import (
    log_attention_files,
    log_batch_summary,
    log_failed_files,
)


def report_batch_summary(summary: BatchSummary, log_file_path: Path) -> None:
    """Report batch processing summary to console and log.

    Args:
        summary (BatchSummary): Batch processing summary.
        log_file_path (Path): Path to log file for display.
    """
    # Log main summary
    log_batch_summary(
        total=summary.total_files,
        success=summary.success_count,
        attention=summary.attention_count,
        failed=summary.failed_count,
        processing_time=summary.processing_time,
        log_file_path=log_file_path,
    )

    # Log failed files (condensed by error code)
    if summary.failed_files:
        condensed_failed = _condense_errors(summary.failed_files)
        log_failed_files(condensed_failed)

    # Log attention files
    if summary.attention_files:
        log_attention_files(summary.attention_files)


def _condense_errors(failed_files: dict[str, list[str]]) -> dict[str, list[str]]:
    """Condense multiple same-code errors to single line with count.

    Args:
        failed_files (dict[str, list[str]]): Raw error messages per file.

    Returns:
        dict[str, list[str]]: Condensed error messages.
    """
    result: dict[str, list[str]] = {}

    for filename, errors in failed_files.items():
        # Count occurrences of each error code
        code_counts: dict[str, int] = defaultdict(int)
        code_messages: dict[str, str] = {}

        for error in errors:
            # Extract error code (first [ERR_xxx] or [ATT_xxx])
            if error.startswith("["):
                bracket_end = error.find("]")
                if bracket_end > 0:
                    code = error[1:bracket_end]
                    code_counts[code] += 1
                    # Keep first message as representative
                    if code not in code_messages:
                        code_messages[code] = error

        # Build condensed list
        condensed = []
        for code, count in code_counts.items():
            msg = code_messages[code]
            if count > 1:
                # Append occurrence count
                condensed.append(f"{msg} ({count} occurrences)")
            else:
                condensed.append(msg)

        result[filename] = condensed

    return result
