from datetime import date
from decimal import Decimal
import pytest
from unittest.mock import MagicMock

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
    assert float(po_res["authorized_total"]) == 3300.00

    po_invalid = lookup_purchase_order("PO-FAKE-999")
    assert po_invalid["found"] is False
    assert po_invalid["status"] == "PO_NOT_FOUND"


def test_scenario_1_normal_invoice_auto_process():
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


def test_scenario_2_duplicate_invoice_human_review():
    agent = InvoiceAgent()
    validator = InvoiceValidator()

    # Mock duplicate check return
    invoice = ExtractedInvoice(
        invoice_number="INV-2026-DUP",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        po_number="PO-8842",
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        subtotal=Decimal("3300.00"),
        total_amount=Decimal("3300.00")
    )
    val_res = validator.validate(invoice)

    mock_db = MagicMock()
    # Simulate DB finding existing invoice
    mock_db.query().filter().first.return_value = MagicMock()

    decision = agent.evaluate_and_decide(invoice, val_res, db_session=mock_db)

    assert decision.action == "HUMAN_REVIEW"
    assert "DUPLICATE_SUSPECTED" in decision.reason


def test_scenario_3_vendor_not_found_human_review():
    agent = InvoiceAgent()
    validator = InvoiceValidator()

    invoice = ExtractedInvoice(
        invoice_number="INV-2026-UNKNOWN-VENDOR",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        vendor=VendorInfo(vendor_name=""),  # Empty vendor
        subtotal=Decimal("1000.00"),
        total_amount=Decimal("1000.00")
    )
    val_res = validator.validate(invoice)
    decision = agent.evaluate_and_decide(invoice, val_res)

    assert decision.action == "HUMAN_REVIEW"
    assert "VENDOR_UNKNOWN" in decision.reason or "VALIDATION_FAILED" in decision.reason


def test_scenario_4_po_mismatch_human_review():
    agent = InvoiceAgent()
    validator = InvoiceValidator()

    # Invoice claims $5000 total for PO-8842 which is authorized for $3300!
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


def test_scenario_5_missing_po_no_po_tool_call():
    agent = InvoiceAgent()
    validator = InvoiceValidator()

    # Invoice without PO number
    invoice = ExtractedInvoice(
        invoice_number="INV-2026-NO-PO",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        po_number=None,
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        line_items=[
            LineItem(
                description="Consulting",
                quantity=Decimal("1.0"),
                unit_price=Decimal("1000.00"),
                line_total=Decimal("1000.00")
            )
        ],
        subtotal=Decimal("1000.00"),
        total_amount=Decimal("1000.00")
    )

    val_res = validator.validate(invoice)
    decision = agent.evaluate_and_decide(invoice, val_res)

    executed_tool_names = [t["tool"] for t in decision.executed_tools]
    assert "lookup_purchase_order" not in executed_tool_names  # Proves dynamic tool selection based on evidence!


def test_scenario_6_tool_failure_human_review_fallback():
    agent = InvoiceAgent()
    validator = InvoiceValidator()

    # Non-existent PO number causes PO lookup failure -> HUMAN_REVIEW
    invoice = ExtractedInvoice(
        invoice_number="INV-2026-BAD-PO",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        po_number="PO-NONEXISTENT-9999",
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        subtotal=Decimal("1000.00"),
        total_amount=Decimal("1000.00")
    )

    val_res = validator.validate(invoice)
    decision = agent.evaluate_and_decide(invoice, val_res)

    assert decision.action == "HUMAN_REVIEW"
    assert "PO_NOT_FOUND" in decision.reason


def test_scenario_7_max_iterations_safety_boundary():
    agent = InvoiceAgent(max_iterations=0)  # Max iterations = 0 force boundary check
    validator = InvoiceValidator()

    invoice = ExtractedInvoice(
        invoice_number="INV-2026-BOUNDARY",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        subtotal=Decimal("1000.00"),
        total_amount=Decimal("1000.00")
    )

    val_res = validator.validate(invoice)
    decision = agent.evaluate_and_decide(invoice, val_res)

    assert decision.action == "HUMAN_REVIEW"
    assert "MAX_ITERATIONS_EXCEEDED" in decision.reason
