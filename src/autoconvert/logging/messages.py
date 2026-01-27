"""Standardized log message helpers for PRD-compliant output format."""

from pathlib import Path
from typing import Literal

from autoconvert.logging.logger import get_logger


def log_startup(
    version: str,
    input_folder: Path,
    output_folder: Path,
    currency_count: int,
    country_count: int,
    file_count: int,
) -> None:
    """Log startup banner and configuration info.

    Args:
        version (str): Application version.
        input_folder (Path): Input data folder path.
        output_folder (Path): Output folder path.
        currency_count (int): Number of currency rules loaded.
        country_count (int): Number of country rules loaded.
        file_count (int): Number of files to process.
    """
    logger = get_logger()
    logger.info("=================================================================")
    logger.info(f"                     AutoConvert v{version}")
    logger.info("=================================================================")
    logger.info(f"Input folder:  {input_folder}")
    logger.info(f"Output folder: {output_folder}")
    logger.info("All regex patterns validated and compiled successfully")
    logger.info(f"Loaded {currency_count} currency rules, {country_count} country rules")
    logger.info(f"Found {file_count} xlsx file(s) to process")


def log_file_progress(n: int, total: int, filename: str) -> None:
    """Log file processing start.

    Args:
        n (int): Current file number (1-based).
        total (int): Total number of files.
        filename (str): Name of file being processed.
    """
    logger = get_logger()
    logger.info("-----------------------------------------------------------------")
    logger.info(f"[{n}/{total}] Processing: {filename} ...")


def log_inv_no_extracted(method: str, label: str, inv_no: str, cell_ref: str) -> None:
    """Log invoice number extraction.

    Args:
        method (str): Extraction method description.
        label (str): Label that was found.
        inv_no (str): Extracted invoice number.
        cell_ref (str): Cell reference where found.
    """
    logger = get_logger()
    logger.info(f"Inv_No extracted ({method} of '{label}'): {inv_no} at '{cell_ref}'")


def log_extraction(component: str, count: int, start_row: int, end_row: int) -> None:
    """Log data extraction results.

    Args:
        component (str): Component name (e.g., "Invoice sheet", "Packing sheet").
        count (int): Number of items extracted.
        start_row (int): First data row (1-based).
        end_row (int): Last data row (1-based).
    """
    logger = get_logger()
    logger.info(f"{component} extracted {count} items (rows {start_row}-{end_row})")


def log_packing_totals(
    row: int, nw: str, gw: str, packets: int | None = None
) -> None:
    """Log packing totals extraction.

    Args:
        row (int): Total row number (1-based).
        nw (str): Total net weight as string (preserves precision).
        gw (str): Total gross weight as string (preserves precision).
        packets (int | None): Total packets, if found.
    """
    logger = get_logger()
    packets_str = str(packets) if packets is not None else "N/A"
    logger.info(f"Packing total row at row {row}, NW= {nw}, GW= {gw}, Packets= {packets_str}")


def log_weight_allocation(
    message: str, precision: int | None = None, target: str | None = None
) -> None:
    """Log weight allocation step.

    Args:
        message (str): Message to log.
        precision (int | None): Precision value, if applicable.
        target (str | None): Target value, if applicable.
    """
    logger = get_logger()
    logger.info(message)


def log_output_written(output_path: Path) -> None:
    """Log successful output file creation.

    Args:
        output_path (Path): Path to the output file.
    """
    logger = get_logger()
    logger.info(f"Output successfully written to: {output_path.name}")


def log_status(status: Literal["SUCCESS", "ATTENTION", "FAILED"]) -> None:
    """Log final processing status with emoji.

    Args:
        status (Literal["SUCCESS", "ATTENTION", "FAILED"]): Processing status.
    """
    logger = get_logger()
    if status == "SUCCESS":
        logger.info("\u2705 SUCCESS")
    elif status == "ATTENTION":
        logger.warning("\u26a0\ufe0f ATTENTION")
    else:
        logger.error("\u274c FAILED")


def log_error_code(code: str, message: str) -> None:
    """Log error with code prefix.

    Args:
        code (str): Error code (e.g., ERR_020).
        message (str): Error message.
    """
    logger = get_logger()
    logger.error(f"[{code}] {message}")


def log_warning_code(code: str, message: str) -> None:
    """Log warning with code prefix.

    Args:
        code (str): Warning code (e.g., ATT_002).
        message (str): Warning message.
    """
    logger = get_logger()
    logger.warning(f"[{code}] {message}")


def log_batch_summary(
    total: int,
    success: int,
    attention: int,
    failed: int,
    processing_time: float,
    log_file_path: Path,
) -> None:
    """Log batch processing summary.

    Args:
        total (int): Total files processed.
        success (int): Success count.
        attention (int): Attention count.
        failed (int): Failed count.
        processing_time (float): Total time in seconds.
        log_file_path (Path): Path to log file.
    """
    logger = get_logger()
    logger.info("===========================================================================")
    logger.info("                    BATCH PROCESSING SUMMARY")
    logger.info("===========================================================================")
    logger.info(f"Total files:        {total}")
    logger.info(f"Successful:         {success}")
    logger.info(f"Attention:          {attention}")
    logger.info(f"Failed:             {failed}")
    logger.info(f"Processing time:    {processing_time:.2f} seconds")
    logger.info(f"Log file:           {log_file_path}")
    logger.info("===========================================================================")


def log_failed_files(failed_files: dict[str, list[str]]) -> None:
    """Log failed files section.

    Args:
        failed_files (dict[str, list[str]]): Dict mapping filename to error messages.
    """
    if not failed_files:
        return

    logger = get_logger()
    logger.error("FAILED FILES:")
    logger.error("--------------------------------------------------------------------------")
    for filename, errors in failed_files.items():
        logger.error(f"* {filename}")
        for error in errors:
            logger.error(f"    {error}")
    logger.error("--------------------------------------------------------------------------")


def log_attention_files(attention_files: dict[str, list[str]]) -> None:
    """Log attention files section.

    Args:
        attention_files (dict[str, list[str]]): Dict mapping filename to warning messages.
    """
    if not attention_files:
        return

    logger = get_logger()
    logger.warning("FILES NEEDING ATTENTION:")
    logger.warning("------------------------------------------------------------------------")
    for filename, warnings in attention_files.items():
        logger.warning(f"* {filename}")
        for warning in warnings:
            logger.warning(f"    {warning}")
    logger.warning("------------------------------------------------------------------------")


def log_debug(message: str) -> None:
    """Log debug message.

    Args:
        message (str): Debug message.
    """
    logger = get_logger()
    logger.debug(message)


def log_info(message: str) -> None:
    """Log info message.

    Args:
        message (str): Info message.
    """
    logger = get_logger()
    logger.info(message)
