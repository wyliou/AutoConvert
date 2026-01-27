"""Weight allocation algorithm.

Allocates packing weights to invoice items proportionally based on quantity.
Follows FR29-FR35 requirements.
"""

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from autoconvert.core.errors import ErrorCode
from autoconvert.core.models import InvoiceItem, PackingItem, PackingTotals, ValidationResult
from autoconvert.logging.messages import log_info, log_warning_code


def allocate_weights(
    invoice_items: list[InvoiceItem],
    packing_items: list[PackingItem],
    packing_totals: PackingTotals,
    validation: ValidationResult,
) -> bool:
    """Allocate weights from packing to invoice items.

    Algorithm:
    1. Aggregate packing weights by part_no
    2. Pre-allocation validation (sum vs total_nw)
    3. Determine precision and round weights
    4. Allocate proportionally to invoice items by quantity

    Args:
        invoice_items (list[InvoiceItem]): Invoice items to receive weights.
        packing_items (list[PackingItem]): Packing items with weights.
        packing_totals (PackingTotals): Total values from packing sheet.
        validation (ValidationResult): For recording errors.

    Returns:
        bool: True if allocation successful, False otherwise.
    """
    total_nw = packing_totals.total_nw

    # Step 1: Aggregate packing weights by part_no
    packing_weights = _aggregate_packing_weights(packing_items)

    # Validate all parts have weight
    for part_no, weight in packing_weights.items():
        if weight <= 0:
            validation.add_error(
                ErrorCode.PACKING_PART_ZERO_NW,
                f"Part '{part_no}' has qty but packing weight=0",
            )
            return False

    # Build invoice part list
    invoice_parts = set(item.part_no for item in invoice_items)
    packing_parts = set(packing_weights.keys())

    # Check for parts in invoice but not in packing
    missing_in_packing = invoice_parts - packing_parts
    if missing_in_packing:
        for part in list(missing_in_packing)[:5]:  # Limit to first 5
            validation.add_error(
                ErrorCode.PART_NOT_IN_PACKING,
                f"Part '{part}' in invoice but not in packing",
            )
        return False

    # Check for parts in packing but not in invoice
    missing_in_invoice = packing_parts - invoice_parts
    if missing_in_invoice:
        for part in list(missing_in_invoice)[:5]:
            validation.add_error(
                ErrorCode.PACKING_PART_NOT_IN_INVOICE,
                f"Part '{part}' in packing sheet not found in invoice",
            )
        return False

    # Step 2: Pre-allocation validation (ERR_047)
    packing_sum = sum(packing_weights.values())
    diff = abs(packing_sum - float(total_nw))

    if diff > 0.1:
        validation.add_error(
            ErrorCode.AGGREGATE_DISAGREE_TOTAL,
            f"Packing weights sum ({packing_sum:.2f}) disagrees with total_nw ({total_nw}), "
            f"difference: {diff:.2f}",
        )
        return False

    # Step 3: Precision detection and rounding
    base_precision = packing_totals.nw_precision
    base_precision = max(min(base_precision, 5), 2)  # Clamp to 2-5

    # Convert to Decimal for precise arithmetic
    decimal_weights = {k: Decimal(str(v)) for k, v in packing_weights.items()}

    # Try to find precision that matches total_nw
    packing_precision, rounded_weights = _determine_precision(
        decimal_weights, total_nw, base_precision
    )

    log_info(f"Trying precision: {packing_precision}")

    # Round and verify
    rounded_sum = sum(rounded_weights.values())
    log_info(f"Expecting rounded part sum: {rounded_sum}, Target: {total_nw}")

    if rounded_sum == total_nw:
        log_info(f"Perfect match at {packing_precision} decimals")
    else:
        # Adjust last part to match total
        log_info(f"Can't find perfect match at {base_precision + 1} decimals, but use it with part adjustment")
        log_info("Adjusting last part weight to match total_nw")
        rounded_weights = _adjust_last_part(rounded_weights, total_nw)

    # Step 4: Allocate to invoice items
    success = _allocate_to_invoice(
        invoice_items, rounded_weights, packing_precision, validation
    )

    if success:
        log_info(f"Weight allocation complete: {total_nw}")

    return success


def _aggregate_packing_weights(packing_items: list[PackingItem]) -> dict[str, float]:
    """Aggregate packing weights by part_no.

    Args:
        packing_items (list[PackingItem]): Packing items.

    Returns:
        dict[str, float]: Part number to total weight mapping.
    """
    weights: dict[str, float] = defaultdict(float)

    for item in packing_items:
        if item.part_no and item.nw > 0:
            weights[item.part_no] += item.nw

    return dict(weights)


def _determine_precision(
    weights: dict[str, Decimal],
    total_nw: Decimal,
    base_precision: int,
) -> tuple[int, dict[str, Decimal]]:
    """Determine optimal precision for weight rounding.

    Tries base precision (N), then N+1. Returns first that matches total_nw,
    or N+1 if neither matches.

    Args:
        weights (dict[str, Decimal]): Part weights.
        total_nw (Decimal): Target total.
        base_precision (int): Base precision from total_nw.

    Returns:
        tuple[int, dict[str, Decimal]]: (precision, rounded weights).
    """
    for try_precision in [base_precision, base_precision + 1]:
        rounded = _round_weights(weights, try_precision)

        # Check for zeros
        if any(w == 0 for w in rounded.values()):
            continue

        # Check if sum matches
        if sum(rounded.values()) == total_nw:
            return try_precision, rounded

    # Default to base_precision + 1
    return base_precision + 1, _round_weights(weights, base_precision + 1)


def _round_weights(
    weights: dict[str, Decimal],
    precision: int,
) -> dict[str, Decimal]:
    """Round all weights to specified precision.

    Args:
        weights (dict[str, Decimal]): Weights to round.
        precision (int): Decimal precision.

    Returns:
        dict[str, Decimal]: Rounded weights.
    """
    quantizer = Decimal(10) ** -precision

    return {
        k: v.quantize(quantizer, rounding=ROUND_HALF_UP)
        for k, v in weights.items()
    }


def _adjust_last_part(
    weights: dict[str, Decimal],
    total_nw: Decimal,
) -> dict[str, Decimal]:
    """Adjust last part's weight to make sum equal total_nw.

    Args:
        weights (dict[str, Decimal]): Rounded weights.
        total_nw (Decimal): Target total.

    Returns:
        dict[str, Decimal]: Adjusted weights.
    """
    parts = list(weights.keys())
    if not parts:
        return weights

    current_sum = sum(weights.values())
    diff = total_nw - current_sum

    # Adjust last part
    last_part = parts[-1]
    weights[last_part] = weights[last_part] + diff

    return weights


def _allocate_to_invoice(
    invoice_items: list[InvoiceItem],
    part_weights: dict[str, Decimal],
    packing_precision: int,
    validation: ValidationResult,
) -> bool:
    """Allocate weights to invoice items proportionally.

    For each part:
    - Calculate total quantity across all invoice items
    - Allocate weight proportionally: item_weight = total_weight * (item_qty / total_qty)
    - Round to line precision (packing_precision + 1)
    - Assign remainder to last item

    Args:
        invoice_items (list[InvoiceItem]): Invoice items.
        part_weights (dict[str, Decimal]): Rounded weights per part.
        packing_precision (int): Packing precision.
        validation (ValidationResult): For recording errors.

    Returns:
        bool: True if successful.
    """
    line_precision = packing_precision + 1
    quantizer = Decimal(10) ** -line_precision

    # Group invoice items by part_no
    items_by_part: dict[str, list[InvoiceItem]] = defaultdict(list)
    for item in invoice_items:
        items_by_part[item.part_no].append(item)

    for part_no, part_items in items_by_part.items():
        total_weight = part_weights.get(part_no)
        if total_weight is None:
            continue

        # Calculate total quantity
        total_qty = sum(Decimal(str(item.qty)) for item in part_items)

        if total_qty == 0:
            validation.add_error(
                ErrorCode.ZERO_QUANTITY_FOR_PART,
                f"Total quantity for part '{part_no}' is zero",
            )
            return False

        # Allocate proportionally
        allocated_sum = Decimal("0")

        for i, item in enumerate(part_items):
            if i == len(part_items) - 1:
                # Last item gets remainder
                item_weight = total_weight - allocated_sum
            else:
                # Proportional allocation
                ratio = Decimal(str(item.qty)) / total_qty
                item_weight = (total_weight * ratio).quantize(
                    quantizer, rounding=ROUND_HALF_UP
                )
                allocated_sum += item_weight

            item.weight = float(item_weight)

    return True
