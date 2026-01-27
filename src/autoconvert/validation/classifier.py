"""Status classification based on validation results."""

from typing import Literal

from autoconvert.core.models import ValidationResult


def classify_status(validation: ValidationResult) -> Literal["SUCCESS", "ATTENTION", "FAILED"]:
    """Classify processing status based on errors and warnings.

    Rules:
    - Any ERR_xxx code -> FAILED
    - Any ATT_xxx code (without errors) -> ATTENTION
    - No errors or warnings -> SUCCESS

    Args:
        validation (ValidationResult): Validation results.

    Returns:
        Literal["SUCCESS", "ATTENTION", "FAILED"]: Processing status.
    """
    if validation.has_errors():
        return "FAILED"

    if validation.has_warnings():
        return "ATTENTION"

    return "SUCCESS"
