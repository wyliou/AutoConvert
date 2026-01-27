"""Sheet detection using regex patterns."""

from openpyxl import Workbook

from autoconvert.core.errors import ErrorCode
from autoconvert.core.models import SheetInfo, ValidationResult
from autoconvert.setup.registry import PatternRegistry


def detect_sheets(
    workbook: Workbook,
    registry: PatternRegistry,
    validation: ValidationResult,
) -> SheetInfo | None:
    """Detect invoice and packing sheets in workbook.

    Args:
        workbook (Workbook): The Excel workbook.
        registry (PatternRegistry): Compiled pattern registry.
        validation (ValidationResult): Validation result to record errors.

    Returns:
        SheetInfo | None: Sheet info if both found, None if either missing.
    """
    invoice_sheet_name: str | None = None
    packing_sheet_name: str | None = None
    invoice_pattern_matched: str | None = None
    packing_pattern_matched: str | None = None

    # Get sheet names and strip whitespace
    sheet_names = [(name, name.strip()) for name in workbook.sheetnames]

    # Find invoice sheet
    for original_name, stripped_name in sheet_names:
        for pattern in registry.invoice_sheet_patterns:
            if pattern.search(stripped_name):
                invoice_sheet_name = original_name
                invoice_pattern_matched = pattern.pattern
                break
        if invoice_sheet_name:
            break

    # Find packing sheet
    for original_name, stripped_name in sheet_names:
        for pattern in registry.packing_sheet_patterns:
            if pattern.search(stripped_name):
                # Don't match the same sheet as invoice
                if original_name != invoice_sheet_name:
                    packing_sheet_name = original_name
                    packing_pattern_matched = pattern.pattern
                    break
        if packing_sheet_name:
            break

    # Report errors for missing sheets
    if invoice_sheet_name is None:
        validation.add_error(
            ErrorCode.INVOICE_SHEET_NOT_FOUND,
            f"Invoice sheet not found. Available sheets: {[n for n, _ in sheet_names]}",
        )

    if packing_sheet_name is None:
        validation.add_error(
            ErrorCode.PACKING_SHEET_NOT_FOUND,
            f"Packing sheet not found. Available sheets: {[n for n, _ in sheet_names]}",
        )

    if invoice_sheet_name is None or packing_sheet_name is None:
        return None

    return SheetInfo(
        invoice_sheet_name=invoice_sheet_name,
        packing_sheet_name=packing_sheet_name,
        invoice_pattern_matched=invoice_pattern_matched,
        packing_pattern_matched=packing_pattern_matched,
    )
