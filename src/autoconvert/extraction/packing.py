"""Packing sheet data extraction."""

import re

from openpyxl.worksheet.worksheet import Worksheet

from autoconvert.core.models import ColumnMap, PackingItem, ValidationResult
from autoconvert.logging.messages import log_debug, log_extraction
from autoconvert.parsing.merged_cells import MergeTracker

# Stop keywords for data extraction
STOP_KEYWORDS = {"total", "合计", "总计", "小计"}

# Keywords to filter out from packing data
PALLET_KEYWORDS = {"plt.", "plt ", "pallet"}

# Unit suffixes to strip from numeric values
UNIT_SUFFIXES = re.compile(r"(KGS?|PCS|EA|件|个)$", re.IGNORECASE)


def extract_packing_items(
    sheet: Worksheet,
    column_map: ColumnMap,
    tracker: MergeTracker,
    validation: ValidationResult,
) -> list[PackingItem]:
    """Extract packing line items from sheet.

    Args:
        sheet (Worksheet): The packing sheet.
        column_map (ColumnMap): Column mapping (0-based indices).
        tracker (MergeTracker): Merge tracker for handling merged cells.
        validation (ValidationResult): For recording errors.

    Returns:
        list[PackingItem]: Extracted packing items.
    """
    items: list[PackingItem] = []
    header_row = column_map.header_row
    start_row = header_row + (2 if column_map.has_subheader else 1)

    cols = column_map.columns
    max_row = sheet.max_row or 1000
    first_data_found = False

    for row_num in range(start_row, max_row + 1):
        # Check stop conditions FIRST (before blank row check per FR19)
        if _is_stop_row(sheet, row_num, cols, tracker):
            log_debug(f"Packing stop condition at row {row_num}")
            break

        # Check if row is blank
        if _is_blank_row(sheet, row_num, cols, tracker):
            if not first_data_found:
                continue  # Skip leading blank rows
            else:
                break  # Stop at trailing blank rows after data found

        # Extract row data
        item = _extract_row(sheet, row_num, cols, tracker)

        # Skip rows with pallet keywords in part_no
        if item.part_no:
            part_lower = item.part_no.lower()
            if any(kw in part_lower for kw in PALLET_KEYWORDS):
                continue

        # Skip header continuation
        if item.part_no and "part no" in item.part_no.lower():
            continue

        # Skip rows where part_no is empty (required for matching)
        if not item.part_no:
            # Check if this could be implicit total row
            if item.nw > 0 and item.gw > 0:
                # Check if part_no column was part of a merge
                if "part_no" in cols:
                    part_col = cols["part_no"] + 1
                    if tracker.is_merged(row_num, part_col):
                        # This is a continuation row, not total row
                        pass
                    else:
                        # Implicit total row
                        log_debug(f"Implicit total row detected at row {row_num}")
                        break
            continue

        # Skip rows with no weight data
        if item.qty == 0 and item.nw == 0:
            continue

        items.append(item)
        first_data_found = True

    # Log extraction results
    if items:
        log_extraction(
            "Packing sheet",
            len(items),
            items[0].row,
            items[-1].row,
        )

    return items


def _extract_row(
    sheet: Worksheet,
    row_num: int,
    cols: dict[str, int],
    tracker: MergeTracker,
) -> PackingItem:
    """Extract a single packing item from a row.

    Args:
        sheet (Worksheet): The worksheet.
        row_num (int): 1-based row number.
        cols (dict[str, int]): Column mapping (0-based indices).
        tracker (MergeTracker): Merge tracker.

    Returns:
        PackingItem: Extracted item.
    """
    item = PackingItem(row=row_num)

    # Extract part_no (string field)
    if "part_no" in cols:
        item.part_no = _get_string_value(sheet, row_num, cols["part_no"] + 1, tracker)

    # Extract qty
    if "qty" in cols:
        item.qty = _get_numeric_value(sheet, row_num, cols["qty"] + 1)

    # Extract nw - only count if first row of merge (FR20)
    if "nw" in cols:
        nw_col = cols["nw"] + 1
        if tracker.is_first_row_of_merge(row_num, nw_col):
            item.nw = _get_numeric_value(sheet, row_num, nw_col, precision=5)
        else:
            item.nw = 0.0  # Prevent double-counting

    # Extract gw
    if "gw" in cols:
        gw_col = cols["gw"] + 1
        if tracker.is_first_row_of_merge(row_num, gw_col):
            item.gw = _get_numeric_value(sheet, row_num, gw_col, precision=5)
        else:
            item.gw = 0.0

    # Extract pack (optional)
    if "pack" in cols:
        item.pack = _get_numeric_value(sheet, row_num, cols["pack"] + 1)

    return item


def _get_string_value(
    sheet: Worksheet,
    row: int,
    col: int,
    tracker: MergeTracker,
) -> str:
    """Get string value from cell, handling merged cells.

    Args:
        sheet (Worksheet): The worksheet.
        row (int): 1-based row number.
        col (int): 1-based column number.
        tracker (MergeTracker): Merge tracker.

    Returns:
        str: String value, empty string if None.
    """
    # Check if cell was part of a merge and get origin value
    origin = tracker.get_origin(row, col)
    if origin is not None:
        cell = sheet.cell(row=origin[0], column=origin[1])
    else:
        cell = sheet.cell(row=row, column=col)

    value = cell.value
    if value is None:
        return ""

    return str(value).strip()


def _get_numeric_value(
    sheet: Worksheet,
    row: int,
    col: int,
    precision: int | None = None,
) -> float:
    """Get numeric value from cell with optional precision.

    Args:
        sheet (Worksheet): The worksheet.
        row (int): 1-based row number.
        col (int): 1-based column number.
        precision (int | None): Decimal precision to round to.

    Returns:
        float: Numeric value, 0.0 if not numeric.
    """
    cell = sheet.cell(row=row, column=col)
    value = cell.value

    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        num = float(value)
    else:
        # Try to parse string
        str_val = str(value).strip()
        # Strip unit suffixes
        str_val = UNIT_SUFFIXES.sub("", str_val).strip()
        # Remove commas
        str_val = str_val.replace(",", "")

        try:
            num = float(str_val)
        except (ValueError, TypeError):
            return 0.0

    # Apply precision if specified
    if precision is not None:
        factor = 10**precision
        num = round(num * factor + 1e-9) / factor

    return num


def _is_stop_row(
    sheet: Worksheet,
    row_num: int,
    cols: dict[str, int],
    tracker: MergeTracker,
) -> bool:
    """Check if row contains stop keywords or is implicit total.

    Args:
        sheet (Worksheet): The worksheet.
        row_num (int): 1-based row number.
        cols (dict[str, int]): Column mapping.
        tracker (MergeTracker): Merge tracker.

    Returns:
        bool: True if stop condition detected.
    """
    # Check first 10 columns for stop keywords
    for col in range(1, 11):
        cell = sheet.cell(row=row_num, column=col)
        value = cell.value

        if value is None:
            continue

        str_val = str(value).strip().lower()

        for kw in STOP_KEYWORDS:
            if kw in str_val:
                return True

    return False


def _is_blank_row(
    sheet: Worksheet,
    row_num: int,
    cols: dict[str, int],
    tracker: MergeTracker,
) -> bool:
    """Check if row is blank (all key columns empty).

    Args:
        sheet (Worksheet): The worksheet.
        row_num (int): 1-based row number.
        cols (dict[str, int]): Column mapping.
        tracker (MergeTracker): Merge tracker.

    Returns:
        bool: True if row is blank.
    """
    key_fields = ["part_no", "qty", "nw", "gw"]

    for field in key_fields:
        if field in cols:
            col = cols[field] + 1

            # Check origin for merged cells
            origin = tracker.get_origin(row_num, col)
            if origin is not None:
                cell = sheet.cell(row=origin[0], column=origin[1])
            else:
                cell = sheet.cell(row=row_num, column=col)

            if cell.value is not None and str(cell.value).strip():
                return False

    return True
