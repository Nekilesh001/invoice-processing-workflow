import pytest
from app.agents.risk_agent import FinancialRiskAgent
from app.agents.risk_tools import (
    check_invoice_amount_anomaly,
    check_invoice_number_pattern,
    get_vendor_invoice_history,
)
from app.schemas.invoice import ExtractedInvoice, VendorInfo
from app.schemas.processing import ValidationResult


def test_risk_tools_number_pattern():
    res1 = check_invoice_number_pattern("INV-2026-8810")
    assert res1["suspicious"] is False

    res2 = check_invoice_number_pattern("INV-12345")
    assert res2["suspicious"] is True


def test_risk_agent_normal_invoice(db_session):
    agent = FinancialRiskAgent()
    inv = ExtractedInvoice(
        invoice_number="INV-2026-NORMAL",
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        total_amount=150.0
    )
    val = ValidationResult(is_valid=True)

    assessment, trace = agent.evaluate(inv, val, db_session=db_session)
    assert assessment.risk_level in ["LOW", "MEDIUM"]
    assert trace.agent_name == "FinancialRiskAgent"
    assert "check_duplicate_invoice" in trace.tools_used


def test_risk_agent_duplicate_pattern(db_session):
    agent = FinancialRiskAgent()
    inv = ExtractedInvoice(
        invoice_number="INV-2026-002",  # Already exists in DB seed
        vendor=VendorInfo(vendor_name="Vertex Software Solutions"),
        total_amount=1620.0
    )
    val = ValidationResult(is_valid=True)

    assessment, trace = agent.evaluate(inv, val, db_session=db_session)
    assert "DUPLICATE_INVOICE_SUSPECTED" in assessment.flags
    assert assessment.risk_score >= 0.5
    assert assessment.risk_level == "HIGH"
