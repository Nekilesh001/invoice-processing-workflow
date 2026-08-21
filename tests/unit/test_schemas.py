from datetime import date, datetime
from decimal import Decimal
import json
from app.schemas.invoice import (
    ExtractedInvoice,
    VendorInfo,
    CustomerInfo,
    LineItem,
    PaymentInformation,
    TaxBreakdown
)
from app.schemas.processing import (
    ProcessingResult,
    ProcessingStatus,
    ValidationResult,
    ValidationRuleResult
)


def test_extracted_invoice_model_instantiation():
    invoice = ExtractedInvoice(
        invoice_number="INV-2026-001",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        currency="USD",
        vendor=VendorInfo(
            vendor_name="Acme Cloud Solutions Inc.",
            vendor_email="billing@acmecloud.com"
        ),
        customer=CustomerInfo(
            customer_name="Global Logistics Corp"
        ),
        line_items=[
            LineItem(
                description="Enterprise Cloud Server Infrastructure",
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

    assert invoice.invoice_number == "INV-2026-001"
    assert invoice.invoice_date == date(2026, 8, 15)
    assert invoice.vendor.vendor_name == "Acme Cloud Solutions Inc."
    assert invoice.total_amount == Decimal("2750.00")
    assert isinstance(invoice.subtotal, Decimal)


def test_extracted_invoice_json_serialization():
    invoice = ExtractedInvoice(
        invoice_number="INV-2026-002",
        total_amount=Decimal("1620.50"),
        vendor=VendorInfo(vendor_name="Vertex Soft")
    )

    json_str = invoice.model_dump_json()
    parsed_dict = json.loads(json_str)

    assert parsed_dict["invoice_number"] == "INV-2026-002"
    assert float(parsed_dict["total_amount"]) == 1620.50
    assert parsed_dict["vendor"]["vendor_name"] == "Vertex Soft"
    assert parsed_dict["due_date"] is None


def test_processing_result_schema():
    val_rule = ValidationRuleResult(
        rule_name="due_date_present",
        passed=False,
        message="Invoice due_date is missing",
        severity="error"
    )
    val_res = ValidationResult(
        is_valid=False,
        errors=[val_rule],
        warnings=[]
    )
    proc_res = ProcessingResult(
        document_name="invoice_002_missing_due_date.pdf",
        status=ProcessingStatus.NEEDS_REVIEW,
        extraction_method="native_pdf",
        validation_result=val_res
    )

    assert proc_res.status == ProcessingStatus.NEEDS_REVIEW
    assert proc_res.validation_result.is_valid is False
    assert len(proc_res.validation_result.errors) == 1
    assert proc_res.validation_result.errors[0].rule_name == "due_date_present"
