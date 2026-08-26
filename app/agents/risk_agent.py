import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.risk_tools import (
    check_invoice_amount_anomaly,
    check_invoice_number_pattern,
    get_vendor_invoice_history,
)
from app.agents.tools import check_duplicate_invoice
from app.schemas.invoice import ExtractedInvoice
from app.schemas.multi_agent import AgentTrace, RiskAssessment
from app.schemas.processing import ValidationResult

logger = logging.getLogger(__name__)


class FinancialRiskAgent:
    """
    Specialized Financial Risk & Fraud Assessment Agent:
    Evaluates suspicious or anomalous invoice behavior:
    - Duplicate detection & re-processing patterns
    - Unusual invoice amount anomalies vs vendor historical average
    - Generic or suspicious invoice numbering patterns
    - Historical vendor activity verification
    """

    def __init__(self, name: str = "FinancialRiskAgent"):
        self.name = name

    def evaluate(
        self,
        extracted_invoice: ExtractedInvoice,
        validation_result: ValidationResult,
        db_session: Optional[Session] = None,
    ) -> tuple[RiskAssessment, AgentTrace]:
        """
        Evaluates financial risk metrics and returns a RiskAssessment and AgentTrace.
        """
        import uuid
        from datetime import datetime

        run_id = f"risk-{uuid.uuid4().hex[:8]}"
        started_at = datetime.utcnow()
        tools_used = []
        tool_results = []
        flags = []
        evidence = []

        vendor_name = extracted_invoice.vendor.vendor_name if extracted_invoice.vendor else None
        invoice_number = extracted_invoice.invoice_number
        total_amount = float(extracted_invoice.total_amount or 0.0)

        risk_score = 0.0
        data_sufficiency = "SUFFICIENT"

        # Check 1: Duplicate Invoice Detection
        tools_used.append("check_duplicate_invoice")
        dup_res = check_duplicate_invoice(
            vendor_name=vendor_name,
            invoice_number=invoice_number,
            session=db_session
        )
        tool_results.append({"tool": "check_duplicate_invoice", "output": dup_res})

        if dup_res.get("is_duplicate"):
            flags.append("DUPLICATE_INVOICE_SUSPECTED")
            risk_score += 0.5
            evidence.append({"check": "duplicate_detection", "details": dup_res})

        # Check 2: Invoice Number Pattern Check
        tools_used.append("check_invoice_number_pattern")
        num_res = check_invoice_number_pattern(invoice_number)
        tool_results.append({"tool": "check_invoice_number_pattern", "output": num_res})

        if num_res.get("suspicious"):
            flags.append("SUSPICIOUS_INVOICE_NUMBER")
            risk_score += 0.2
            evidence.append({"check": "invoice_number_pattern", "details": num_res})

        # Check 3: Historical Vendor Activity & Amount Anomaly
        tools_used.append("get_vendor_invoice_history")
        hist_res = get_vendor_invoice_history(vendor_name, session=db_session)
        tool_results.append({"tool": "get_vendor_invoice_history", "output": hist_res})
        evidence.append({"check": "vendor_history", "details": hist_res})

        if hist_res.get("data_sufficiency") == "INSUFFICIENT_DATA":
            data_sufficiency = "INSUFFICIENT_DATA"

        tools_used.append("check_invoice_amount_anomaly")
        anomaly_res = check_invoice_amount_anomaly(
            total_amount=total_amount,
            vendor_name=vendor_name,
            session=db_session
        )
        tool_results.append({"tool": "check_invoice_amount_anomaly", "output": anomaly_res})

        if anomaly_res.get("is_anomaly"):
            flags.append(anomaly_res.get("anomaly_type", "UNUSUAL_INVOICE_AMOUNT"))
            risk_score += 0.4
            evidence.append({"check": "amount_anomaly", "details": anomaly_res})

        # Final Risk Rating Classification
        risk_score = round(min(risk_score, 1.0), 2)
        if risk_score >= 0.5:
            risk_level = "HIGH"
            recommended_action = "HUMAN_REVIEW"
        elif risk_score >= 0.2:
            risk_level = "MEDIUM"
            recommended_action = "CONTINUE"
        else:
            risk_level = "LOW"
            recommended_action = "CONTINUE"

        completed_at = datetime.utcnow()

        assessment = RiskAssessment(
            risk_level=risk_level,
            risk_score=risk_score,
            flags=flags,
            evidence=evidence,
            recommended_action=recommended_action,
            data_sufficiency=data_sufficiency,
        )

        trace = AgentTrace(
            agent_name=self.name,
            agent_run_id=run_id,
            started_at=started_at,
            completed_at=completed_at,
            iterations=len(tools_used),
            tools_used=tools_used,
            tool_results=tool_results,
            final_assessment=assessment.model_dump(),
            errors=flags,
        )

        return assessment, trace
