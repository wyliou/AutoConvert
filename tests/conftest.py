"""Root conftest.py with shared fixtures for all test modules."""

from decimal import Decimal
from pathlib import Path

import pytest

from autoconvert.core.models import (
    ColumnMap,
    InvoiceItem,
    PackingItem,
    PackingTotals,
    ValidationResult,
)


# ============================================================================
# PATH FIXTURES
# ============================================================================
@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def config_dir(project_root: Path) -> Path:
    """Return the config directory."""
    return project_root / "config"


@pytest.fixture
def data_dir(project_root: Path) -> Path:
    """Return the data directory with sample Excel files."""
    return project_root / "data"


# ============================================================================
# MODEL FIXTURES (Factory Functions)
# ============================================================================
@pytest.fixture
def make_invoice_item():
    """Factory fixture for creating InvoiceItem instances."""

    def _make(
        row: int = 1,
        part_no: str = "TEST-001",
        po_no: str = "PO12345",
        qty: float = 100.0,
        price: float = 1.50,
        amount: float = 150.0,
        currency: str = "USD",
        coo: str = "CN",
        cod: str = "",
        brand: str = "TestBrand",
        brand_type: str = "OEM",
        model: str = "MODEL-A",
        inv_no: str = "",
        serial: str = "",
        weight: float = 0.0,
    ) -> InvoiceItem:
        return InvoiceItem(
            row=row,
            part_no=part_no,
            po_no=po_no,
            qty=qty,
            price=price,
            amount=amount,
            currency=currency,
            coo=coo,
            cod=cod,
            brand=brand,
            brand_type=brand_type,
            model=model,
            inv_no=inv_no,
            serial=serial,
            weight=weight,
        )

    return _make


@pytest.fixture
def make_packing_item():
    """Factory fixture for creating PackingItem instances."""

    def _make(
        row: int = 1,
        part_no: str = "TEST-001",
        qty: float = 100.0,
        nw: float = 5.0,
        gw: float = 6.0,
        pack: float = 1.0,
    ) -> PackingItem:
        return PackingItem(
            row=row,
            part_no=part_no,
            qty=qty,
            nw=nw,
            gw=gw,
            pack=pack,
        )

    return _make


@pytest.fixture
def make_packing_totals():
    """Factory fixture for creating PackingTotals instances."""

    def _make(
        total_row: int = 10,
        total_nw: Decimal | float = Decimal("10.00"),
        total_gw: Decimal | float = Decimal("12.00"),
        total_packets: int | None = 2,
        nw_precision: int = 2,
        gw_precision: int = 2,
    ) -> PackingTotals:
        return PackingTotals(
            total_row=total_row,
            total_nw=Decimal(str(total_nw)) if not isinstance(total_nw, Decimal) else total_nw,
            total_gw=Decimal(str(total_gw)) if not isinstance(total_gw, Decimal) else total_gw,
            total_packets=total_packets,
            nw_precision=nw_precision,
            gw_precision=gw_precision,
        )

    return _make


@pytest.fixture
def validation_result() -> ValidationResult:
    """Return a fresh ValidationResult instance."""
    return ValidationResult()


@pytest.fixture
def column_map_invoice() -> ColumnMap:
    """Return a typical invoice column map."""
    return ColumnMap(
        columns={
            "part_no": 0,
            "po_no": 1,
            "qty": 2,
            "price": 3,
            "amount": 4,
            "currency": 5,
            "coo": 6,
            "brand": 7,
            "brand_type": 8,
            "model": 9,
        },
        header_row=7,
        has_subheader=False,
    )


@pytest.fixture
def column_map_packing() -> ColumnMap:
    """Return a typical packing column map."""
    return ColumnMap(
        columns={
            "part_no": 0,
            "qty": 1,
            "nw": 2,
            "gw": 3,
            "pack": 4,
        },
        header_row=7,
        has_subheader=False,
    )


# ============================================================================
# LOOKUP TABLE FIXTURES
# ============================================================================
@pytest.fixture
def currency_rules() -> dict[str, str]:
    """Return sample currency lookup rules."""
    return {
        "USD": "USD",
        "US DOLLAR": "USD",
        "US": "USD",
        "CNY": "CNY",
        "RMB": "CNY",
        "EUR": "EUR",
        "EURO": "EUR",
        "JPY": "JPY",
    }


@pytest.fixture
def country_rules() -> dict[str, str]:
    """Return sample country lookup rules."""
    return {
        "CN": "CN",
        "CHINA": "CN",
        "MADEINCHINA": "CN",
        "TW": "TW",
        "TAIWAN": "TW",
        "JP": "JP",
        "JAPAN": "JP",
        "US": "US",
        "USA": "US",
    }
