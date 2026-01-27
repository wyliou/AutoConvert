"""Single file processing pipeline."""

from pathlib import Path

from openpyxl import Workbook

from autoconvert.allocation.weight import allocate_weights
from autoconvert.core.models import ProcessingResult, ValidationResult
from autoconvert.extraction.invoice import extract_inv_no_from_header, extract_invoice_items
from autoconvert.extraction.packing import extract_packing_items
from autoconvert.extraction.total_detector import detect_total_row
from autoconvert.extraction.total_extractor import extract_packing_totals
from autoconvert.ingestion.workbook import open_workbook
from autoconvert.logging.messages import log_status
from autoconvert.output.template import populate_template
from autoconvert.output.writer import write_output
from autoconvert.parsing.column_mapper import map_columns_with_subheader
from autoconvert.parsing.header_finder import find_header_row
from autoconvert.parsing.merged_cells import MergeTracker, unmerge_all
from autoconvert.parsing.sheet_detector import detect_sheets
from autoconvert.setup.config import Config
from autoconvert.transformation.transform import transform_items
from autoconvert.validation.classifier import classify_status
from autoconvert.validation.rules import validate_required_fields


def process_file(file_path: Path, config: Config) -> ProcessingResult:
    """Process a single vendor Excel file.

    Runs the full processing pipeline:
    1. Open workbook
    2. Detect sheets
    3. Map columns
    4. Extract invoice and packing data
    5. Transform data
    6. Allocate weights
    7. Validate
    8. Generate output

    Args:
        file_path (Path): Path to input Excel file.
        config (Config): Application configuration.

    Returns:
        ProcessingResult: Processing result with status and output.
    """
    result = ProcessingResult()
    validation = ValidationResult()

    # Step 1: Open workbook
    workbook = open_workbook(file_path, validation)
    if workbook is None:
        result.status = "FAILED"
        result.errors = validation.errors
        log_status(result.status)
        return result

    try:
        # Step 2: Detect sheets
        sheet_info = detect_sheets(workbook, config.registry, validation)
        if sheet_info is None:
            result.status = "FAILED"
            result.errors = validation.errors
            log_status(result.status)
            return result

        invoice_sheet = workbook[sheet_info.invoice_sheet_name]
        packing_sheet = workbook[sheet_info.packing_sheet_name]

        # Step 3a: Process invoice sheet
        # Create merge tracker and unmerge
        invoice_tracker = MergeTracker.from_sheet(invoice_sheet)
        unmerge_all(invoice_sheet)

        # Find header row
        invoice_header = find_header_row(invoice_sheet)
        if invoice_header is None:
            validation.add_error(
                "ERR_014",
                f"Header row not found in invoice sheet (searched rows 7-30)",
            )
            result.status = "FAILED"
            result.errors = validation.errors
            log_status(result.status)
            return result

        # Map columns
        invoice_column_map = map_columns_with_subheader(
            invoice_sheet, invoice_header, config.registry, "invoice", validation
        )
        if invoice_column_map is None:
            result.status = "FAILED"
            result.errors = validation.errors
            log_status(result.status)
            return result

        # Step 3b: Process packing sheet
        packing_tracker = MergeTracker.from_sheet(packing_sheet)
        unmerge_all(packing_sheet)

        packing_header = find_header_row(packing_sheet)
        if packing_header is None:
            validation.add_error(
                "ERR_014",
                f"Header row not found in packing sheet (searched rows 7-30)",
            )
            result.status = "FAILED"
            result.errors = validation.errors
            log_status(result.status)
            return result

        packing_column_map = map_columns_with_subheader(
            packing_sheet, packing_header, config.registry, "packing", validation
        )
        if packing_column_map is None:
            result.status = "FAILED"
            result.errors = validation.errors
            log_status(result.status)
            return result

        # Step 4a: Extract invoice number from header area
        header_inv_no, _, _ = extract_inv_no_from_header(invoice_sheet, config.registry)

        # Step 4b: Extract invoice items
        invoice_items = extract_invoice_items(
            invoice_sheet, invoice_column_map, invoice_tracker, config.registry, validation
        )

        if not invoice_items:
            validation.add_error("ERR_030", "No invoice items extracted")
            result.status = "FAILED"
            result.errors = validation.errors
            log_status(result.status)
            return result

        # Step 4c: Extract packing items
        packing_items = extract_packing_items(
            packing_sheet, packing_column_map, packing_tracker, validation
        )

        if not packing_items:
            validation.add_error("ERR_030", "No packing items extracted")
            result.status = "FAILED"
            result.errors = validation.errors
            log_status(result.status)
            return result

        # Step 4d: Detect total row and extract totals
        last_data_row = packing_items[-1].row if packing_items else packing_header + 1
        total_row = detect_total_row(
            packing_sheet, packing_column_map, last_data_row, packing_tracker
        )

        if total_row is None:
            validation.add_error("ERR_032", "Total row not found in packing sheet")
            result.status = "FAILED"
            result.errors = validation.errors
            log_status(result.status)
            return result

        packing_totals = extract_packing_totals(
            packing_sheet, packing_column_map, total_row, validation
        )

        if packing_totals is None:
            result.status = "FAILED"
            result.errors = validation.errors
            result.warnings = validation.warnings
            log_status(result.status)
            return result

        # Step 5: Transform data
        transform_items(
            invoice_items,
            header_inv_no,
            config.currency_rules,
            config.country_rules,
            validation,
        )

        # Step 6: Validate required fields
        if not validate_required_fields(invoice_items, validation):
            result.status = "FAILED"
            result.errors = validation.errors
            result.warnings = validation.warnings
            log_status(result.status)
            return result

        # Step 7: Allocate weights
        if not allocate_weights(invoice_items, packing_items, packing_totals, validation):
            result.status = "FAILED"
            result.errors = validation.errors
            result.warnings = validation.warnings
            log_status(result.status)
            return result

        # Step 8: Classify status and generate output if appropriate
        result.status = classify_status(validation)
        result.errors = validation.errors
        result.warnings = validation.warnings
        result.invoice_items = invoice_items
        result.packing_items = packing_items
        result.packing_totals = packing_totals

        # Generate output for SUCCESS and ATTENTION
        if result.status in ("SUCCESS", "ATTENTION"):
            output_wb = populate_template(
                config.template_path, invoice_items, packing_totals
            )
            input_name = file_path.stem
            output_path = write_output(
                output_wb, config.output_folder, input_name, validation
            )

            if output_path is None:
                result.status = "FAILED"
                result.errors = validation.errors
            else:
                result.output_path = output_path

        log_status(result.status)
        return result

    finally:
        workbook.close()
