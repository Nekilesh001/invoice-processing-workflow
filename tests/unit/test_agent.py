from datetime import date
from decimal import Decimal
import pytest

from app.agents.invoice_agent import InvoiceAgent
from app.agents.tools import lookup_vendor, lookup_purchase_order, check_duplicate_invoice
from app.schemas.invoice import ExtractedInvoice, VendorInfo, LineItem
from app.validation.validator import InvoiceValidator


def test_agent_tools_direct():
    v_res = lookup_vendor("Acme Cloud Solutions Inc.")
    assert v_res["found"] is True
    assert v_res["status"] == "VERIFIED"

    po_res = lookup_purchase_order("PO-8842")
    assert po_res["found"] is True
    assert po_res["authorized_total"] == Decimal("3300.00")

    po_invalid = lookup_purchase_order("PO-FAKE-999")
    assert po_invalid["found"] is False
    assert po_invalid["status"] == "PO_NOT_FOUND"


def test_agent_auto_process_matching_po():
    agent = InvoiceAgent()
    validator = InvoiceValidator()

    invoice = ExtractedInvoice(
        invoice_number="INV-2026-001",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        po_number="PO-8842",
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        line_items=[
            LineItem(
                description="Cloud Infra",
                quantity=Decimal("1.0"),
                unit_price=Decimal("3000.00"),
                line_total=Decimal("3000.00")
            )
        ],
        subtotal=Decimal("3000.00"),
        tax_amount=Decimal("300.00"),
        total_amount=Decimal("3300.00"),
        amount_due=Decimal("3300.00")
    )

    val_res = validator.validate(invoice)
    decision = agent.evaluate_and_decide(invoice, val_res)

    assert decision.action == "AUTO_PROCESS"
    assert decision.po_verified is True
    assert decision.vendor_verified is True
    assert len(decision.executed_tools) == 3  # dup check, vendor lookup, PO lookup


def test_agent_human_review_po_mismatch():
    agent = InvoiceAgent()
    validator = InvoiceValidator()

    # Invoice claims $5000 total for PO-8842 which is only authorized for $3300!
    invoice = ExtractedInvoice(
        invoice_number="INV-2026-MISMATCH",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        po_number="PO-8842",
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        subtotal=Decimal("5000.00"),
        total_amount=Decimal("5000.00")
    )

    val_res = validator.validate(invoice)
    decision = agent.evaluate_and_decide(invoice, val_res)

    assert decision.action == "HUMAN_REVIEW"
    assert "PO_MISMATCH" in decision.reason
    assert decision.po_verified is False


def test_agent_human_review_po_not_found():
    agent = InvoiceAgent()
    validator = InvoiceValidator()

    invoice = ExtractedInvoice(
        invoice_number="INV-2026-UNKNOWN-PO",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        po_number="PO-NONEXISTENT-99",
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        subtotal=Decimal("1000.00"),
        total_amount=Decimal("1000.00")
    )

    val_res = validator.validate(invoice)
    decision = agent.evaluate_and_decide(invoice, val_res)

    assert decision.action == "HUMAN_REVIEW"
    assert "PO_NOT_FOUND" in decision.reason
