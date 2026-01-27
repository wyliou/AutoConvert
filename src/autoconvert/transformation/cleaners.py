"""Data cleaning utilities for PO numbers, invoice numbers, etc."""

import re


def clean_po_number(value: str) -> str:
    """Clean PO number by removing suffix after first '-' or '/'.

    Examples:
        2250600556-2.1 -> 2250600556
        PO12345/1 -> PO12345

    Args:
        value (str): Raw PO number.

    Returns:
        str: Cleaned PO number.
    """
    if not value:
        return ""

    # Remove suffix starting from first '-' or '/'
    for delimiter in ["-", "/"]:
        if delimiter in value:
            value = value.split(delimiter)[0]
            break

    return value.strip()


def clean_invoice_number(value: str) -> str:
    """Clean invoice number by removing common prefixes.

    Removes: INV#, NO., INV., etc.

    Args:
        value (str): Raw invoice number.

    Returns:
        str: Cleaned invoice number.
    """
    if not value:
        return ""

    # Remove common prefixes
    patterns = [
        r"^INV\.?\s*#?\s*",  # INV#, INV., INV
        r"^NO\.?\s*",  # NO., NO
        r"^INVOICE\s*#?\s*",  # INVOICE#, INVOICE
    ]

    result = value.strip()

    for pattern in patterns:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)

    return result.strip()


def strip_whitespace(value: str | None) -> str:
    """Strip leading/trailing whitespace from value.

    Args:
        value (str | None): Value to strip.

    Returns:
        str: Stripped string, empty if None.
    """
    if value is None:
        return ""
    return str(value).strip()
