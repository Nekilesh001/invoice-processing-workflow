import pytest
from app.agents.procurement_agent import ProcurementAgent
from app.schemas.invoice import ExtractedInvoice, VendorInfo, LineItem
from app.schemas.processing import ValidationResult


def test_procurement_agent_normal_vendor_and_po(db_session):
    agent = ProcurementAgent()
    inv = ExtractedInvoice(
        invoice_number="INV-TEST-001",
        invoice_date="2026-08-01",
        due_date="2026-08-31",
        po_number="PO-8842",
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        line_items=[
            LineItem(description="Enterprise Cloud Infrastructure Tier 3 Subscriptions", quantity=10, unit_price=300, line_total=3000)
        ],
        subtotal=3000.0,
        tax_amount=300.0,
        total_amount=3300.0
    )
    val = ValidationResult(is_valid=True)

    assessment, trace = agent.evaluate(inv, val, db_session=db_session)
    assert assessment.vendor_verified is True
    assert assessment.po_verified is True
    assert trace.agent_name == "ProcurementVerificationAgent"
    assert "lookup_vendor" in trace.tools_used


def test_procurement_agent_unknown_vendor(db_session):
    agent = ProcurementAgent()
    inv = ExtractedInvoice(
        invoice_number="INV-TEST-999",
        vendor=VendorInfo(vendor_name="Unregistered Cybernetics LLC"),
        subtotal=500.0,
        total_amount=500.0
    )
    val = ValidationResult(is_valid=True)

    assessment, trace = agent.evaluate(inv, val, db_session=db_session)
    assert assessment.vendor_verified is False
    assert assessment.status == "REVIEW"
    assert "UNKNOWN_VENDOR" in assessment.issues
    assert assessment.recommended_action == "HUMAN_REVIEW"


def test_procurement_agent_po_not_found(db_session):
    agent = ProcurementAgent()
    inv = ExtractedInvoice(
        invoice_number="INV-TEST-PO-MISSING",
        po_number="PO-999999",
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        total_amount=100.0
    )
    val = ValidationResult(is_valid=True)

    assessment, trace = agent.evaluate(inv, val, db_session=db_session)
    assert assessment.vendor_verified is True
    assert assessment.po_verified is False
    assert any("PO_NOT_FOUND" in issue for issue in assessment.issues)
    assert assessment.recommended_action == "HUMAN_REVIEW"
