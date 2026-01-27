"""Convert legacy .xls files to openpyxl workbook format."""

from pathlib import Path

import xlrd
from openpyxl import Workbook
from openpyxl.cell.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet


def convert_xls_to_workbook(file_path: Path) -> Workbook:
    """Convert .xls file to openpyxl Workbook in-memory.

    Args:
        file_path (Path): Path to .xls file.

    Returns:
        Workbook: openpyxl Workbook with data from .xls file.

    Raises:
        Exception: If conversion fails.
    """
    # Open xls file with xlrd
    xls_book = xlrd.open_workbook(file_path, formatting_info=False)

    # Create new openpyxl workbook
    wb = Workbook()

    # Remove default sheet
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]

    # Copy each sheet
    for sheet_idx, xls_sheet in enumerate(xls_book.sheets()):
        # Create new sheet with same name
        if sheet_idx == 0:
            ws = wb.create_sheet(title=xls_sheet.name, index=0)
        else:
            ws = wb.create_sheet(title=xls_sheet.name)

        # Copy cell values
        for row_idx in range(xls_sheet.nrows):
            for col_idx in range(xls_sheet.ncols):
                cell_value = xls_sheet.cell_value(row_idx, col_idx)
                cell_type = xls_sheet.cell_type(row_idx, col_idx)

                # Handle date values
                if cell_type == xlrd.XL_CELL_DATE:
                    try:
                        date_tuple = xlrd.xldate_as_tuple(cell_value, xls_book.datemode)
                        from datetime import datetime

                        cell_value = datetime(*date_tuple)
                    except Exception:
                        pass  # Keep original value if conversion fails

                # openpyxl uses 1-based indices
                ws.cell(row=row_idx + 1, column=col_idx + 1, value=cell_value)

        # Copy merged cell ranges
        for crange in xls_sheet.merged_cells:
            # xlrd returns (row_lo, row_hi, col_lo, col_hi) in 0-based indices
            row_lo, row_hi, col_lo, col_hi = crange
            # openpyxl uses 1-based indices
            ws.merge_cells(
                start_row=row_lo + 1,
                start_column=col_lo + 1,
                end_row=row_hi,  # xlrd's row_hi is already exclusive, so it's the 1-based end row
                end_column=col_hi,  # xlrd's col_hi is already exclusive
            )

    return wb
