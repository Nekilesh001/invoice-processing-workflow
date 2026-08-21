from datetime import date
from decimal import Decimal
from app.schemas.invoice import ExtractedInvoice, VendorInfo, LineItem
from app.validation.validator import InvoiceValidator


def test_validator_valid_invoice():
    validator = InvoiceValidator()
    invoice = ExtractedInvoice(
        invoice_number="INV-2026-001",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        line_items=[
            LineItem(
                description="Enterprise Cloud Server",
                quantity=Decimal("1.0"),
                unit_price=Decimal("2500.00"),
                line_total=Decimal("2500.00")
            )
        ],
        subtotal=Decimal("2500.00"),
        tax_amount=Decimal("250.00"),
        total_amount=Decimal("2750.00"),
        amount_due=Decimal("2750.00")
    )

    result = validator.validate(invoice)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validator_missing_due_date():
    validator = InvoiceValidator()
    invoice = ExtractedInvoice(
        invoice_number="INV-2026-002",
        invoice_date=date(2026, 8, 18),
        due_date=None,  # Missing due date!
        vendor=VendorInfo(vendor_name="Vertex Software"),
        subtotal=Decimal("1500.00"),
        tax_amount=Decimal("120.00"),
        total_amount=Decimal("1620.00")
    )

    result = validator.validate(invoice)
    assert result.is_valid is False
    assert any("due_date" in err.message for err in result.errors)


def test_validator_missing_vendor():
    validator = InvoiceValidator()
    invoice = ExtractedInvoice(
        invoice_number="INV-2026-003",
        invoice_date=date(2026, 8, 10),
        due_date=date(2026, 8, 25),
        vendor=VendorInfo(vendor_name=None),  # Missing vendor!
        subtotal=Decimal("800.00"),
        total_amount=Decimal("800.00")
    )

    result = validator.validate(invoice)
    assert result.is_valid is False
    assert any("vendor_name" in err.message for err in result.errors)


def test_validator_arithmetic_mismatch():
    validator = InvoiceValidator()
    invoice = ExtractedInvoice(
        invoice_number="INV-2026-004",
        invoice_date=date(2026, 8, 1),
        due_date=date(2026, 8, 31),
        vendor=VendorInfo(vendor_name="Delta Tech Services"),
        subtotal=Decimal("1000.00"),
        tax_amount=Decimal("100.00"),
        total_amount=Decimal("1500.00")  # Subtotal 1000 + Tax 100 = 1100 != 1500!
    )

    result = validator.validate(invoice)
    assert result.is_valid is False
    assert any(err.rule_name == "total_calculation_check" for err in result.errors)


def test_validator_invalid_date_sanity():
    validator = InvoiceValidator()
    invoice = ExtractedInvoice(
        invoice_number="INV-2026-005",
        invoice_date=date(2026, 8, 20),
        due_date=date(2026, 8, 10),  # Due date precedes invoice date!
        vendor=VendorInfo(vendor_name="Apex Supplies"),
        subtotal=Decimal("500.00"),
        total_amount=Decimal("500.00")
    )

    result = validator.validate(invoice)
    assert result.is_valid is False
    assert any(err.rule_name == "date_sanity_check" for err in result.errors)
