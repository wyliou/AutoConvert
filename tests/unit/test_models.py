"""Unit tests for core/models.py."""

import pytest

from autoconvert.core.models import ColumnMap, ValidationResult


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_initial_state_empty(self):
        """Test that new ValidationResult has no errors or warnings."""
        result = ValidationResult()
        assert not result.has_errors()
        assert not result.has_warnings()
        assert result.errors == []
        assert result.warnings == []

    def test_add_error(self, validation_result: ValidationResult):
        """Test adding an error."""
        validation_result.add_error("ERR_001", "Test error", log=False)

        assert validation_result.has_errors()
        assert len(validation_result.errors) == 1
        assert validation_result.errors[0] == ("ERR_001", "Test error")

    def test_add_warning(self, validation_result: ValidationResult):
        """Test adding a warning."""
        validation_result.add_warning("ATT_001", "Test warning", log=False)

        assert validation_result.has_warnings()
        assert len(validation_result.warnings) == 1
        assert validation_result.warnings[0] == ("ATT_001", "Test warning")

    def test_multiple_errors(self, validation_result: ValidationResult):
        """Test adding multiple errors."""
        validation_result.add_error("ERR_001", "Error 1", log=False)
        validation_result.add_error("ERR_002", "Error 2", log=False)

        assert len(validation_result.errors) == 2

    def test_has_errors_false_with_only_warnings(self, validation_result: ValidationResult):
        """Test has_errors returns False when only warnings exist."""
        validation_result.add_warning("ATT_001", "Warning", log=False)

        assert not validation_result.has_errors()
        assert validation_result.has_warnings()

    def test_merge_combines_results(self):
        """Test merge combines errors and warnings from both results."""
        result1 = ValidationResult()
        result1.add_error("ERR_001", "Error 1", log=False)
        result1.add_warning("ATT_001", "Warning 1", log=False)

        result2 = ValidationResult()
        result2.add_error("ERR_002", "Error 2", log=False)
        result2.add_warning("ATT_002", "Warning 2", log=False)

        result1.merge(result2)

        assert len(result1.errors) == 2
        assert len(result1.warnings) == 2
        assert ("ERR_001", "Error 1") in result1.errors
        assert ("ERR_002", "Error 2") in result1.errors

    def test_merge_empty_into_populated(self):
        """Test merging empty result into populated one."""
        result1 = ValidationResult()
        result1.add_error("ERR_001", "Error", log=False)

        result2 = ValidationResult()
        result1.merge(result2)

        assert len(result1.errors) == 1


class TestColumnMap:
    """Tests for ColumnMap dataclass."""

    def test_get_existing_column(self, column_map_invoice: ColumnMap):
        """Test getting an existing column index."""
        assert column_map_invoice.get("part_no") == 0
        assert column_map_invoice.get("qty") == 2
        assert column_map_invoice.get("model") == 9

    def test_get_nonexistent_column(self, column_map_invoice: ColumnMap):
        """Test getting a non-existent column returns None."""
        assert column_map_invoice.get("nonexistent") is None
        assert column_map_invoice.get("serial") is None

    def test_empty_column_map(self):
        """Test empty ColumnMap behavior."""
        empty_map = ColumnMap()

        assert empty_map.columns == {}
        assert empty_map.header_row == 0
        assert not empty_map.has_subheader
        assert empty_map.get("anything") is None

    def test_header_row_attribute(self, column_map_invoice: ColumnMap):
        """Test header_row attribute."""
        assert column_map_invoice.header_row == 7

    def test_has_subheader_attribute(self):
        """Test has_subheader attribute."""
        map_with_subheader = ColumnMap(
            columns={"test": 0},
            header_row=5,
            has_subheader=True,
        )
        assert map_with_subheader.has_subheader
