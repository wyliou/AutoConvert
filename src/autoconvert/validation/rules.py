"""Validation rules for invoice and packing data."""

import math

from autoconvert.core.errors import ErrorCode
from autoconvert.core.models import InvoiceItem, PackingItem, ValidationResult


# Required fields for invoice items
REQUIRED_INVOICE_FIELDS = [
    "part_no",
    "po_no",
    "qty",
    "price",
    "amount",
    "currency",
    "coo",
    "brand",
    "brand_type",
    "model",
]


def validate_required_fields(
    items: list[InvoiceItem],
    validation: ValidationResult,
) -> bool:
    """Validate all required fields are non-empty.

    Args:
        items (list[InvoiceItem]): Invoice items to validate.
        validation (ValidationResult): For recording errors.

    Returns:
        bool: True if all valid, False if any errors.
    """
    has_errors = False

    for item in items:
        for field in REQUIRED_INVOICE_FIELDS:
            value = getattr(item, field, None)

            # String fields: check for empty
            if field in ["part_no", "po_no", "currency", "coo", "brand", "brand_type", "model"]:
                if _is_empty_string(value):
                    validation.add_error(
                        ErrorCode.EMPTY_REQUIRED_FIELD,
                        f"Empty required field: {field} at row {item.row}",
                    )
                    has_errors = True

            # Numeric fields: check for NaN/Inf (zeros are allowed for validation purposes)
            elif field in ["qty", "price", "amount"]:
                if isinstance(value, float):
                    if math.isnan(value) or math.isinf(value):
                        validation.add_error(
                            ErrorCode.INVALID_NUMERIC,
                            f"Invalid numeric value: {field} at row {item.row}",
                        )
                        has_errors = True

    return not has_errors


def validate_invoice_items(
    items: list[InvoiceItem],
    validation: ValidationResult,
) -> bool:
    """Validate invoice items data integrity.

    Includes:
    - Required field validation
    - Numeric value validation

    Args:
        items (list[InvoiceItem]): Invoice items to validate.
        validation (ValidationResult): For recording errors.

    Returns:
        bool: True if all valid, False if any errors.
    """
    return validate_required_fields(items, validation)


def _is_empty_string(value: object) -> bool:
    """Check if value is empty (None, empty string, or whitespace only).

    Args:
        value: Value to check.

    Returns:
        bool: True if empty.
    """
    if value is None:
        return True

    if isinstance(value, str):
        return len(value.strip()) == 0

    return False
