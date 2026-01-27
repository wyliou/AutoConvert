"""Header row detection in Excel sheets."""

import re

from openpyxl.worksheet.worksheet import Worksheet

from autoconvert.logging.messages import log_debug

# Header keywords that indicate a valid header row
HEADER_KEYWORDS = {
    # English
    "qty",
    "n.w.",
    "g.w.",
    "part no",
    "amount",
    "price",
    "quantity",
    "weight",
    "country",
    "origin",
    "brand",
    "model",
    "description",
    "unit",
    "currency",
    "coo",
    # Chinese
    "品牌",
    "料号",
    "数量",
    "单价",
    "金额",
    "净重",
    "毛重",
    "原产",
}

# Metadata labels that indicate this is NOT a header row
METADATA_LABELS = {
    "tel:",
    "fax:",
    "cust id:",
    "contact:",
    "address:",
}


def find_header_row(
    sheet: Worksheet,
    min_row: int = 7,
    max_row: int = 30,
    min_columns: int = 13,
    min_valid_headers: int = 7,
) -> int | None:
    """Find the header row in a worksheet.

    Uses multiple heuristics:
    1. Count non-empty cells in first N columns
    2. Filter out "Unnamed" placeholder cells
    3. Filter out metadata rows (Tel:, Fax:, etc.)
    4. Prioritize rows with recognized header keywords
    5. Deprioritize rows with data-like values (numbers, alphanumeric codes)

    Args:
        sheet (Worksheet): The worksheet to search.
        min_row (int): Start searching from this row (default 7).
        max_row (int): Stop searching at this row (default 30).
        min_columns (int): Number of columns to scan (default 13).
        min_valid_headers (int): Minimum valid headers required (default 7).

    Returns:
        int | None: 1-based row number of header row, or None if not found.
    """
    best_row: int | None = None
    best_score = 0

    for row_num in range(min_row, max_row + 1):
        valid_count = 0
        keyword_count = 0
        data_value_count = 0
        is_metadata_row = False

        for col_num in range(1, min_columns + 1):
            cell = sheet.cell(row=row_num, column=col_num)
            value = cell.value

            if value is None:
                continue

            str_value = str(value).strip()

            if not str_value:
                continue

            # Filter out "Unnamed" placeholders (from pandas)
            if str_value.startswith("Unnamed"):
                continue

            # Check for metadata labels
            lower_value = str_value.lower()
            if any(label in lower_value for label in METADATA_LABELS):
                is_metadata_row = True
                break

            # Check if this looks like data (not a header)
            if _is_data_value(str_value):
                data_value_count += 1
            else:
                valid_count += 1

            # Check for header keywords
            if any(kw in lower_value for kw in HEADER_KEYWORDS):
                keyword_count += 1

        if is_metadata_row:
            continue

        # Deprioritize rows with 3+ data-like values
        if data_value_count >= 3:
            continue

        # Calculate score: prioritize keyword matches
        score = valid_count + (keyword_count * 2)

        if valid_count >= min_valid_headers and score > best_score:
            best_score = score
            best_row = row_num

    return best_row


def _is_data_value(value: str) -> bool:
    """Check if a value looks like data rather than a header.

    Args:
        value (str): String value to check.

    Returns:
        bool: True if this looks like a data value.
    """
    # Pure numbers (int or decimal)
    if re.match(r"^-?\d+\.?\d*$", value):
        return True

    # Alphanumeric codes (like part numbers: SG24701, ABC-123)
    if re.match(r"^[A-Z]{1,4}\d{4,}$", value, re.IGNORECASE):
        return True

    # Date patterns
    if re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}", value):
        return True

    return False
