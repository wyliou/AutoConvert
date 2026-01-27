"""Standardized error and warning codes for AutoConvert.

Error Code Range Reservations:
- 001-009: Configuration/startup errors
- 010-019: File-level errors (lock, corrupt, missing sheets/headers)
- 020-029: Column mapping errors
- 030-039: Data extraction errors
- 040-049: Weight allocation errors
- 050-059: Output errors (template, write)
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    """Error codes that cause FAILED status."""

    # Startup errors (001-009) - Exit code 2, halt before processing
    CONFIG_NOT_FOUND = "ERR_001"
    INVALID_REGEX = "ERR_002"
    DUPLICATE_LOOKUP = "ERR_003"
    MALFORMED_CONFIG = "ERR_004"
    TEMPLATE_INVALID = "ERR_005"

    # File-level errors (010-019)
    FILE_LOCKED = "ERR_010"
    FILE_CORRUPTED = "ERR_011"
    INVOICE_SHEET_NOT_FOUND = "ERR_012"
    PACKING_SHEET_NOT_FOUND = "ERR_013"
    HEADER_ROW_NOT_FOUND = "ERR_014"

    # Column mapping errors (020-029)
    REQUIRED_COLUMN_MISSING = "ERR_020"
    INVOICE_NUMBER_NOT_FOUND = "ERR_021"

    # Data extraction errors (030-039)
    EMPTY_REQUIRED_FIELD = "ERR_030"
    INVALID_NUMERIC = "ERR_031"
    TOTAL_ROW_NOT_FOUND = "ERR_032"
    INVALID_TOTAL_NW = "ERR_033"
    INVALID_TOTAL_GW = "ERR_034"

    # Weight allocation errors (040-049)
    PART_NOT_IN_PACKING = "ERR_040"
    WEIGHT_ALLOCATION_MISMATCH = "ERR_041"
    PACKING_PART_ZERO_NW = "ERR_042"
    PACKING_PART_NOT_IN_INVOICE = "ERR_043"
    WEIGHT_ROUNDS_TO_ZERO = "ERR_044"
    ZERO_QUANTITY_FOR_PART = "ERR_045"
    DIFFERENT_PARTS_SHARE_MERGED_WEIGHT = "ERR_046"
    AGGREGATE_DISAGREE_TOTAL = "ERR_047"

    # Output errors (050-059)
    TEMPLATE_LOAD_FAILED = "ERR_051"
    OUTPUT_WRITE_FAILED = "ERR_052"


class WarningCode(StrEnum):
    """Warning codes that cause ATTENTION status (output still generated)."""

    MISSING_TOTAL_PACKETS = "ATT_002"
    UNSTANDARDIZED_CURRENCY = "ATT_003"
    UNSTANDARDIZED_COO = "ATT_004"


class ConfigError(Exception):
    """Raised for configuration errors that should halt startup."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        """Initialize with error code and message.

        Args:
            code (ErrorCode): The error code.
            message (str): Descriptive error message.
        """
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")
