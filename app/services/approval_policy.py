import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from app.schemas.multi_agent import ProcurementAssessment, RiskAssessment
from app.schemas.processing import ValidationResult

logger = logging.getLogger(__name__)


class FinalDecision(BaseModel):
    """Structured decision output produced by Approval Policy Engine."""
    action: str = Field(..., description="AUTO_PROCESS, HUMAN_REVIEW, or REJECT")
    reason: str = Field(..., description="Explanation of final decision policy trigger")
    confidence_score: float = Field(1.0, description="Decision confidence score")
    procurement_status: str = Field("UNKNOWN")
    risk_level: str = Field("UNKNOWN")
    requires_human_review: bool = Field(False)


class ApprovalPolicyEngine:
    """
    Deterministic Final Approval Policy Engine:
    Acts as the final safety boundary. Specialist agents (Procurement & Risk)
    produce structured assessments, but CANNOT directly approve invoices or mutate database states.
    This policy engine evaluates all assessments against business rules.
    """

    def evaluate(
        self,
        validation_result: ValidationResult,
        procurement: ProcurementAssessment,
        risk: RiskAssessment,
    ) -> FinalDecision:
        """Evaluates procurement assessment, risk assessment, and validation result to produce a FinalDecision."""
        
        # Rule 1: Deterministic Schema/Math Validation Check
        if not validation_result.is_valid:
            err_msg = ", ".join(e.message for e in validation_result.errors) if validation_result.errors else "Validation failed"
            return FinalDecision(
                action="HUMAN_REVIEW",
                reason=f"VALIDATION_FAILED: {err_msg}",
                confidence_score=0.9,
                procurement_status=procurement.status if procurement else "FAIL",
                risk_level=risk.risk_level if risk else "UNKNOWN",
                requires_human_review=True
            )

        # Rule 2: Vendor Registry Check
        if not procurement or not procurement.vendor_verified:
            return FinalDecision(
                action="HUMAN_REVIEW",
                reason="UNKNOWN_VENDOR: Unregistered Vendor is not verified in master registry.",
                confidence_score=1.0,
                procurement_status=procurement.status if procurement else "REVIEW",
                risk_level=risk.risk_level if risk else "UNKNOWN",
                requires_human_review=True
            )

        # Rule 3: Duplicate Invoice Check
        if risk and "DUPLICATE_INVOICE_SUSPECTED" in risk.flags:
            return FinalDecision(
                action="HUMAN_REVIEW",
                reason="DUPLICATE_SUSPECTED: Identical vendor and invoice number already exist in database.",
                confidence_score=0.99,
                procurement_status=procurement.status,
                risk_level=risk.risk_level,
                requires_human_review=True
            )

        # Rule 4: Procurement Compliance & PO Matching Check
        if procurement and procurement.status in ["FAIL", "REVIEW", "UNKNOWN"]:
            issues_str = "; ".join(procurement.issues) if procurement.issues else "Procurement policy compliance issue"
            reason_keyword = "PO_LINE_MISMATCH" if "PO_LINE_MISMATCH" in issues_str or not procurement.po_match else "PROCUREMENT_FLAG"
            return FinalDecision(
                action="HUMAN_REVIEW",
                reason=f"{reason_keyword}: {issues_str}",
                confidence_score=0.95,
                procurement_status=procurement.status,
                risk_level=risk.risk_level if risk else "UNKNOWN",
                requires_human_review=True
            )

        # Rule 5: Financial Risk & Fraud Check
        if risk and risk.risk_level == "HIGH":
            flags_str = ", ".join(risk.flags) if risk.flags else "High financial risk detected"
            return FinalDecision(
                action="HUMAN_REVIEW",
                reason=f"FINANCIAL_RISK: {flags_str}",
                confidence_score=0.95,
                procurement_status=procurement.status,
                risk_level=risk.risk_level,
                requires_human_review=True
            )

        # Rule 6: All Verifications PASSED -> AUTO_PROCESS
        if (
            procurement
            and procurement.status == "PASS"
            and procurement.vendor_verified
            and (not risk or risk.risk_level in ["LOW", "MEDIUM"])
            and validation_result.is_valid
        ):
            return FinalDecision(
                action="AUTO_PROCESS",
                reason="Verified: Master vendor verified, PO matched, and zero financial risk flags.",
                confidence_score=1.0,
                procurement_status="PASS",
                risk_level=risk.risk_level if risk else "LOW",
                requires_human_review=False
            )

        # Fallback Safe Default -> HUMAN_REVIEW
        return FinalDecision(
            action="HUMAN_REVIEW",
            reason="Safety Fallback: Invoice requires human review due to unclassified policy state.",
            confidence_score=0.8,
            procurement_status=procurement.status if procurement else "UNKNOWN",
            risk_level=risk.risk_level if risk else "UNKNOWN",
            requires_human_review=True
        )
