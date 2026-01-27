"""Diagnostic mode runner for troubleshooting pattern matching."""

from pathlib import Path

from autoconvert.core.models import ValidationResult
from autoconvert.ingestion.workbook import open_workbook
from autoconvert.logging.logger import get_logger
from autoconvert.parsing.column_mapper import normalize_header
from autoconvert.parsing.header_finder import find_header_row
from autoconvert.parsing.merged_cells import MergeTracker, unmerge_all
from autoconvert.parsing.sheet_detector import detect_sheets
from autoconvert.setup.config import Config


def run_diagnostic(file_path: Path, config: Config) -> int:
    """Run diagnostic mode on a single file.

    Shows detailed pattern matching information including:
    - Sheet detection results
    - Column mapping results (matched and unmatched)
    - Suggestions for adding patterns

    Args:
        file_path (Path): Path to Excel file to diagnose.
        config (Config): Application configuration.

    Returns:
        int: Exit code (0 = success).
    """
    logger = get_logger()
    registry = config.registry

    print("=" * 75)
    print(f"                    DIAGNOSTIC MODE - {file_path.name}")
    print("=" * 75)
    print()

    validation = ValidationResult()

    # Open workbook
    workbook = open_workbook(file_path, validation)
    if workbook is None:
        print(f"[ERROR] Cannot open file: {file_path}")
        for code, msg in validation.errors:
            print(f"  [{code}] {msg}")
        return 0

    try:
        # Sheet detection
        print("[SHEET DETECTION]")
        sheet_names = workbook.sheetnames
        print(f"  Available sheets: {sheet_names}")

        sheet_info = detect_sheets(workbook, registry, validation)
        if sheet_info:
            print(
                f'  Invoice sheet: "{sheet_info.invoice_sheet_name}" '
                f'matched pattern: "{sheet_info.invoice_pattern_matched}"'
            )
            print(
                f'  Packing sheet: "{sheet_info.packing_sheet_name}" '
                f'matched pattern: "{sheet_info.packing_pattern_matched}"'
            )
        else:
            print("  Invoice sheet: NOT FOUND")
            print("  Packing sheet: NOT FOUND")
            print()
            return 0

        print()

        # Column mapping - Invoice
        invoice_sheet = workbook[sheet_info.invoice_sheet_name]
        invoice_tracker = MergeTracker.from_sheet(invoice_sheet)
        unmerge_all(invoice_sheet)

        invoice_header = find_header_row(invoice_sheet)

        print("[COLUMN MAPPING - Invoice Sheet]")
        if invoice_header:
            print(f"  Header row detected at: Row {invoice_header}")
            _diagnose_columns(
                invoice_sheet,
                invoice_header,
                registry.invoice_columns,
                "invoice",
            )
        else:
            print("  Header row: NOT FOUND (searched rows 7-30)")

        print()

        # Column mapping - Packing
        packing_sheet = workbook[sheet_info.packing_sheet_name]
        MergeTracker.from_sheet(packing_sheet)  # Capture before unmerge
        unmerge_all(packing_sheet)

        packing_header = find_header_row(packing_sheet)

        print("[COLUMN MAPPING - Packing Sheet]")
        if packing_header:
            print(f"  Header row detected at: Row {packing_header}")
            _diagnose_columns(
                packing_sheet,
                packing_header,
                registry.packing_columns,
                "packing",
            )
        else:
            print("  Header row: NOT FOUND (searched rows 7-30)")

        print()

    finally:
        workbook.close()

    return 0


def _diagnose_columns(sheet, header_row: int, column_patterns: dict, sheet_type: str) -> None:
    """Diagnose column mapping for a sheet.

    Args:
        sheet: The worksheet.
        header_row (int): Header row number.
        column_patterns (dict): Column patterns from registry.
        sheet_type (str): "invoice" or "packing".
    """
    # Read headers
    headers = []
    max_col = min(sheet.max_column or 20, 20)

    for col in range(1, max_col + 1):
        cell = sheet.cell(row=header_row, column=col)
        headers.append((col, normalize_header(cell.value)))

    # Try to match each field
    matched = {}
    unmatched_required = []
    suggestions = []

    for field_name, field_pattern in column_patterns.items():
        found = False
        required_str = "(required)" if field_pattern.required else "(optional)"

        for pattern in field_pattern.patterns:
            for col, header in headers:
                if header and pattern.search(header):
                    col_letter = _col_letter(col)
                    print(
                        f'    {field_name:12} (Col {col_letter}) matched: "{pattern.pattern}" {required_str}'
                    )
                    matched[field_name] = col
                    found = True
                    break
            if found:
                break

        if not found:
            print(f"    {field_name:12} (Col ?) NOT MATCHED {required_str}")
            tried = [f'"{p.pattern}"' for p in field_pattern.patterns[:3]]
            print(f"      Tried patterns: [{', '.join(tried)}]")

            if field_pattern.required:
                unmatched_required.append(field_name)

                # Try to find potential matches
                for col, header in headers:
                    if header and col not in matched.values():
                        # Simple heuristic: check if field name is in header
                        if field_name.replace("_", " ") in header.lower():
                            suggestions.append(
                                (field_name, header, f'(?i){header.replace(" ", ".*")}')
                            )

    # Print suggestions
    if suggestions:
        print()
        print("[SUGGESTED ADDITIONS]")
        for field_name, header, pattern in suggestions:
            print(f"  Add to field_patterns.yaml > {sheet_type}_columns > {field_name} > patterns:")
            print(f'    - "{pattern}"  # Found in header: "{header}"')


def _col_letter(col: int) -> str:
    """Convert 1-based column number to letter."""
    result = ""
    while col > 0:
        col, remainder = divmod(col - 1, 26)
        result = chr(65 + remainder) + result
    return result
