import pytest
from invoice_service import InvoiceService, Invoice, LineItem

def test_compute_total_basic():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-001",
        customer_id="C-001",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="A", category="book", unit_price=100.0, qty=2)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 0
    assert isinstance(warnings, list)

def test_invalid_qty_raises():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-002",
        customer_id="C-001",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="A", category="book", unit_price=100.0, qty=0)]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv)


def test_invalid_invoice_fields_raise():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="",
        customer_id="",
        country="US",
        membership="none",
        coupon=None,
        items=[LineItem(sku="", category="invalid", unit_price=-1.0, qty=-1)]
    )
    with pytest.raises(ValueError) as exc:
        service.compute_total(inv)
    message = str(exc.value)
    assert "Missing invoice_id" in message
    assert "Missing customer_id" in message
    assert "Invalid qty" in message
    assert "Invalid price" in message
    assert "Unknown category" in message


def test_coupon_and_membership_discounts_apply():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-003",
        customer_id="C-003",
        country="JP",
        membership="gold",
        coupon="WELCOME10",
        items=[LineItem(sku="B", category="electronics", unit_price=2000.0, qty=2)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 0
    assert warnings == []


def test_unknown_coupon_adds_warning():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-004",
        customer_id="C-004",
        country="US",
        membership="none",
        coupon="NOTREAL",
        items=[LineItem(sku="C", category="food", unit_price=10.0, qty=5)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 0
    assert "Unknown coupon" in warnings


def test_fragile_fee_shipping_default_and_upgrade_warning():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-005",
        customer_id="C-005",
        country="FR",
        membership="none",
        coupon=None,
        items=[
            LineItem(sku="D", category="other", unit_price=3000.0, qty=4, fragile=True)
        ]
    )
    total, warnings = service.compute_total(inv)
    assert total > 0
    assert "Consider membership upgrade" in warnings
