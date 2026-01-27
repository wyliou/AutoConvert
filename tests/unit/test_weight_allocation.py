"""Unit tests for allocation/weight.py."""

from decimal import Decimal

import pytest

from autoconvert.allocation.weight import (
    _adjust_last_part,
    _aggregate_packing_weights,
    _round_weights,
    allocate_weights,
)
from autoconvert.core.models import ValidationResult


class TestAggregatePackingWeights:
    """Tests for _aggregate_packing_weights."""

    def test_aggregates_by_part_no(self, make_packing_item):
        """Test weights are aggregated by part number."""
        items = [
            make_packing_item(part_no="A", nw=5.0),
            make_packing_item(part_no="A", nw=3.0),
            make_packing_item(part_no="B", nw=2.0),
        ]

        result = _aggregate_packing_weights(items)

        assert result["A"] == 8.0
        assert result["B"] == 2.0

    def test_skips_zero_weights(self, make_packing_item):
        """Test items with zero weight are skipped."""
        items = [
            make_packing_item(part_no="A", nw=5.0),
            make_packing_item(part_no="A", nw=0.0),
        ]

        result = _aggregate_packing_weights(items)

        assert result["A"] == 5.0

    def test_skips_empty_part_no(self, make_packing_item):
        """Test items with empty part_no are skipped."""
        items = [
            make_packing_item(part_no="A", nw=5.0),
            make_packing_item(part_no="", nw=3.0),
        ]

        result = _aggregate_packing_weights(items)

        assert "A" in result
        assert "" not in result

    def test_empty_list_returns_empty_dict(self):
        """Test empty input returns empty dict."""
        result = _aggregate_packing_weights([])
        assert result == {}

    def test_single_item(self, make_packing_item):
        """Test single item aggregation."""
        items = [make_packing_item(part_no="X", nw=10.5)]

        result = _aggregate_packing_weights(items)

        assert result == {"X": 10.5}


class TestRoundWeights:
    """Tests for _round_weights."""

    def test_rounds_to_specified_precision(self):
        """Test rounding to specified decimal places."""
        weights = {"A": Decimal("1.2345"), "B": Decimal("2.5555")}

        result = _round_weights(weights, precision=2)

        assert result["A"] == Decimal("1.23")
        assert result["B"] == Decimal("2.56")  # ROUND_HALF_UP

    def test_preserves_exact_values(self):
        """Test exact values are preserved."""
        weights = {"A": Decimal("1.50")}

        result = _round_weights(weights, precision=2)

        assert result["A"] == Decimal("1.50")

    def test_high_precision(self):
        """Test rounding to high precision."""
        weights = {"A": Decimal("1.123456789")}

        result = _round_weights(weights, precision=5)

        assert result["A"] == Decimal("1.12346")

    def test_empty_dict(self):
        """Test empty dict returns empty."""
        result = _round_weights({}, precision=2)
        assert result == {}


class TestAdjustLastPart:
    """Tests for _adjust_last_part."""

    def test_adjusts_last_part_to_match_total(self):
        """Test last part is adjusted to match total."""
        weights = {"A": Decimal("5.00"), "B": Decimal("3.00")}
        total = Decimal("8.10")

        result = _adjust_last_part(weights, total)

        # B should be adjusted from 3.00 to 3.10
        assert result["B"] == Decimal("3.10")
        assert sum(result.values()) == total

    def test_negative_adjustment(self):
        """Test negative adjustment when sum exceeds total."""
        weights = {"A": Decimal("5.00"), "B": Decimal("3.50")}
        total = Decimal("8.00")

        result = _adjust_last_part(weights, total)

        assert result["B"] == Decimal("3.00")
        assert sum(result.values()) == total

    def test_empty_dict_returns_empty(self):
        """Test empty input returns empty."""
        result = _adjust_last_part({}, Decimal("10"))
        assert result == {}

    def test_single_item(self):
        """Test single item gets full adjustment."""
        weights = {"A": Decimal("5.00")}
        total = Decimal("5.50")

        result = _adjust_last_part(weights, total)

        assert result["A"] == Decimal("5.50")


class TestAllocateWeights:
    """Tests for the main allocate_weights function."""

    def test_successful_allocation_single_part(
        self, make_invoice_item, make_packing_item, make_packing_totals
    ):
        """Test successful weight allocation for single part."""
        invoice_items = [
            make_invoice_item(part_no="A", qty=100),
            make_invoice_item(part_no="A", qty=50),
        ]
        packing_items = [
            make_packing_item(part_no="A", qty=150, nw=15.0),
        ]
        packing_totals = make_packing_totals(total_nw=Decimal("15.00"))
        validation = ValidationResult()

        success = allocate_weights(
            invoice_items, packing_items, packing_totals, validation
        )

        assert success
        assert not validation.has_errors()
        # Total allocated weight should equal total_nw
        total_allocated = sum(item.weight for item in invoice_items)
        assert abs(total_allocated - 15.0) < 0.01

    def test_proportional_allocation(
        self, make_invoice_item, make_packing_item, make_packing_totals
    ):
        """Test weights are allocated proportionally by quantity."""
        # 100 qty + 50 qty = 150 total qty
        # 100/150 = 2/3 of weight, 50/150 = 1/3 of weight
        invoice_items = [
            make_invoice_item(part_no="A", qty=100),
            make_invoice_item(part_no="A", qty=50),
        ]
        packing_items = [
            make_packing_item(part_no="A", qty=150, nw=15.0),
        ]
        packing_totals = make_packing_totals(total_nw=Decimal("15.00"))
        validation = ValidationResult()

        allocate_weights(invoice_items, packing_items, packing_totals, validation)

        # First item should get ~10.0 (2/3 of 15)
        # Second item should get ~5.0 (1/3 of 15)
        assert invoice_items[0].weight == pytest.approx(10.0, abs=0.1)
        assert invoice_items[1].weight == pytest.approx(5.0, abs=0.1)

    def test_multiple_parts(
        self, make_invoice_item, make_packing_item, make_packing_totals
    ):
        """Test allocation with multiple parts."""
        invoice_items = [
            make_invoice_item(part_no="A", qty=100),
            make_invoice_item(part_no="B", qty=200),
        ]
        packing_items = [
            make_packing_item(part_no="A", nw=5.0),
            make_packing_item(part_no="B", nw=10.0),
        ]
        packing_totals = make_packing_totals(total_nw=Decimal("15.00"))
        validation = ValidationResult()

        success = allocate_weights(
            invoice_items, packing_items, packing_totals, validation
        )

        assert success
        assert invoice_items[0].weight == pytest.approx(5.0, abs=0.1)
        assert invoice_items[1].weight == pytest.approx(10.0, abs=0.1)

    def test_part_not_in_packing_error(
        self, make_invoice_item, make_packing_item, make_packing_totals
    ):
        """Test error when invoice part not in packing."""
        invoice_items = [make_invoice_item(part_no="A")]
        packing_items = [make_packing_item(part_no="B", nw=5.0)]
        packing_totals = make_packing_totals(total_nw=Decimal("5.00"))
        validation = ValidationResult()

        success = allocate_weights(
            invoice_items, packing_items, packing_totals, validation
        )

        assert not success
        assert validation.has_errors()
        assert "ERR_040" in validation.errors[0][0]

    def test_packing_part_not_in_invoice_error(
        self, make_invoice_item, make_packing_item, make_packing_totals
    ):
        """Test error when packing part not in invoice."""
        invoice_items = [make_invoice_item(part_no="A")]
        packing_items = [
            make_packing_item(part_no="A", nw=5.0),
            make_packing_item(part_no="B", nw=5.0),  # Not in invoice
        ]
        packing_totals = make_packing_totals(total_nw=Decimal("10.00"))
        validation = ValidationResult()

        success = allocate_weights(
            invoice_items, packing_items, packing_totals, validation
        )

        assert not success
        assert "ERR_043" in validation.errors[0][0]

    def test_zero_weight_error(
        self, make_invoice_item, make_packing_item, make_packing_totals
    ):
        """Test error when packing part has zero weight."""
        invoice_items = [make_invoice_item(part_no="A")]
        packing_items = [make_packing_item(part_no="A", nw=0.0, qty=100)]
        packing_totals = make_packing_totals(total_nw=Decimal("0.00"))
        validation = ValidationResult()

        success = allocate_weights(
            invoice_items, packing_items, packing_totals, validation
        )

        # Zero weight parts are skipped in aggregation, so A won't be found
        assert not success

    def test_aggregate_disagrees_with_total_error(
        self, make_invoice_item, make_packing_item, make_packing_totals
    ):
        """Test error when packing sum disagrees with total by more than 0.1."""
        invoice_items = [make_invoice_item(part_no="A")]
        packing_items = [make_packing_item(part_no="A", nw=5.0)]
        # Total is way off from packing sum (5.0 vs 10.0 = 5.0 diff > 0.1)
        packing_totals = make_packing_totals(total_nw=Decimal("10.00"))
        validation = ValidationResult()

        success = allocate_weights(
            invoice_items, packing_items, packing_totals, validation
        )

        assert not success
        assert "ERR_047" in validation.errors[0][0]

    def test_small_difference_allowed(
        self, make_invoice_item, make_packing_item, make_packing_totals
    ):
        """Test small difference (<=0.1) between sum and total is allowed."""
        invoice_items = [make_invoice_item(part_no="A")]
        packing_items = [make_packing_item(part_no="A", nw=5.0)]
        # Difference of 0.05 should be allowed
        packing_totals = make_packing_totals(total_nw=Decimal("5.05"))
        validation = ValidationResult()

        success = allocate_weights(
            invoice_items, packing_items, packing_totals, validation
        )

        assert success

    def test_zero_quantity_error(
        self, make_invoice_item, make_packing_item, make_packing_totals
    ):
        """Test error when total quantity for a part is zero."""
        invoice_items = [make_invoice_item(part_no="A", qty=0)]
        packing_items = [make_packing_item(part_no="A", nw=5.0)]
        packing_totals = make_packing_totals(total_nw=Decimal("5.00"))
        validation = ValidationResult()

        success = allocate_weights(
            invoice_items, packing_items, packing_totals, validation
        )

        assert not success
        assert "ERR_045" in validation.errors[0][0]
