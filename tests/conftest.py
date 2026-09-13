from pathlib import Path

import pytest

from orderscribe.models import LineItem, PurchaseOrder


@pytest.fixture
def sample_pdf() -> Path:
    return Path(__file__).resolve().parents[1] / "test_docs" / "PO39793-01.pdf"


@pytest.fixture
def order_data() -> dict:
    item = dict.fromkeys(LineItem.model_fields)
    item.update(
        position="10",
        buyer_part_number="4260-0100-09",
        supplier_part_number="VC05-0013",
        description="OTL-Connector 1,5-50mm2, 1xAl/Cu",
        ordered_quantity="96",
        remaining_quantity="96",
        unit="PCS",
        unit_price="1.3920",
        currency="EUR",
        requested_delivery_date="2026-09-11",
    )
    order = dict.fromkeys(PurchaseOrder.model_fields)
    order.update(
        order_number="PO39793",
        order_date="2026-09-10",
        supplier_number="53432",
        total_amount="739.58",
        currency="EUR",
        items=[item],
        notes=[],
        warnings=[],
    )
    return order
