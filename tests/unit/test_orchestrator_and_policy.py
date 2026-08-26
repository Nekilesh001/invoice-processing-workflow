import pytest
from app.agents.orchestrator import InvoiceOrchestrator
from app.services.approval_policy import ApprovalPolicyEngine
from app.schemas.invoice import ExtractedInvoice, VendorInfo, LineItem
from app.schemas.multi_agent import ProcurementAssessment, RiskAssessment
from app.schemas.processing import ValidationResult


def test_approval_policy_engine_auto_process():
    policy = ApprovalPolicyEngine()
    val = ValidationResult(is_valid=True)
    proc = ProcurementAssessment(status="PASS", vendor_verified=True, po_verified=True, po_match=True)
    risk = RiskAssessment(risk_level="LOW", risk_score=0.0)

    decision = policy.evaluate(val, proc, risk)
    assert decision.action == "AUTO_PROCESS"
    assert decision.requires_human_review is False


def test_approval_policy_engine_unknown_vendor():
    policy = ApprovalPolicyEngine()
    val = ValidationResult(is_valid=True)
    proc = ProcurementAssessment(status="REVIEW", vendor_verified=False)
    risk = RiskAssessment(risk_level="LOW", risk_score=0.0)

    decision = policy.evaluate(val, proc, risk)
    assert decision.action == "HUMAN_REVIEW"
    assert "Unregistered Vendor" in decision.reason


def test_approval_policy_engine_high_risk():
    policy = ApprovalPolicyEngine()
    val = ValidationResult(is_valid=True)
    proc = ProcurementAssessment(status="PASS", vendor_verified=True)
    risk = RiskAssessment(risk_level="HIGH", risk_score=0.7, flags=["DUPLICATE_INVOICE_SUSPECTED"])

    decision = policy.evaluate(val, proc, risk)
    assert decision.action == "HUMAN_REVIEW"
    assert "DUPLICATE_SUSPECTED" in decision.reason or "FINANCIAL_RISK" in decision.reason


def test_invoice_orchestrator_end_to_end(db_session):
    orchestrator = InvoiceOrchestrator()
    inv = ExtractedInvoice(
        invoice_number="INV-ORCH-001",
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

    final_decision, state = orchestrator.process_invoice(inv, val, db_session=db_session)
    assert final_decision.action is not None
    assert state.procurement_assessment is not None
    assert state.risk_assessment is not None
    assert len(state.agent_traces) == 2
