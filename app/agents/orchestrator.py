import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.procurement_agent import ProcurementAgent
from app.agents.risk_agent import FinancialRiskAgent
from app.schemas.invoice import ExtractedInvoice
from app.schemas.multi_agent import MultiAgentInvoiceState
from app.schemas.processing import ValidationResult
from app.services.approval_policy import ApprovalPolicyEngine, FinalDecision

logger = logging.getLogger(__name__)


class InvoiceOrchestrator:
    """
    Multi-Agent Invoice Verification Orchestrator:
    Coordinates specialized agents sequentially:
    1. ProcurementVerificationAgent -> ProcurementAssessment
    2. FinancialRiskAgent -> RiskAssessment
    3. ApprovalPolicyEngine -> FinalDecision
    
    Maintains unified MultiAgentInvoiceState and complete audit traces.
    """

    def __init__(
        self,
        procurement_agent: Optional[ProcurementAgent] = None,
        risk_agent: Optional[FinancialRiskAgent] = None,
        policy_engine: Optional[ApprovalPolicyEngine] = None,
    ):
        self.procurement_agent = procurement_agent or ProcurementAgent()
        self.risk_agent = risk_agent or FinancialRiskAgent()
        self.policy_engine = policy_engine or ApprovalPolicyEngine()

    def process_invoice(
        self,
        extracted_invoice: ExtractedInvoice,
        validation_result: ValidationResult,
        db_session: Optional[Session] = None,
        on_tool_callback: Optional[Any] = None,
    ) -> tuple[FinalDecision, MultiAgentInvoiceState]:
        """
        Executes sequential multi-agent orchestration and returns final decision with multi-agent state.
        """
        invoice_number = extracted_invoice.invoice_number
        vendor_name = extracted_invoice.vendor.vendor_name if extracted_invoice.vendor else None
        po_number = extracted_invoice.po_number
        total_amount = float(extracted_invoice.total_amount or 0.0)

        state = MultiAgentInvoiceState(
            invoice_number=invoice_number,
            vendor_name=vendor_name,
            po_number=po_number,
            total_amount=total_amount,
        )

        # Agent 1: Procurement Verification
        try:
            proc_assessment, proc_trace = self.procurement_agent.evaluate(
                extracted_invoice=extracted_invoice,
                validation_result=validation_result,
                db_session=db_session
            )
            state.procurement_assessment = proc_assessment
            state.agent_traces.append(proc_trace)
            if on_tool_callback and proc_trace.tools_used:
                for tool in proc_trace.tools_used:
                    on_tool_callback(tool, {}, {"status": proc_assessment.status})
        except Exception as e:
            logger.error(f"ProcurementAgent execution failed: {e}")
            state.errors.append(f"ProcurementAgent error: {str(e)}")

        # Agent 2: Financial Risk / Fraud Assessment
        try:
            risk_assessment, risk_trace = self.risk_agent.evaluate(
                extracted_invoice=extracted_invoice,
                validation_result=validation_result,
                db_session=db_session
            )
            state.risk_assessment = risk_assessment
            state.agent_traces.append(risk_trace)
            if on_tool_callback and risk_trace.tools_used:
                for tool in risk_trace.tools_used:
                    on_tool_callback(tool, {}, {"risk_level": risk_assessment.risk_level})
        except Exception as e:
            logger.error(f"FinancialRiskAgent execution failed: {e}")
            state.errors.append(f"FinancialRiskAgent error: {str(e)}")

        # Final Safety Layer: Approval Policy Engine
        final_decision = self.policy_engine.evaluate(
            validation_result=validation_result,
            procurement=state.procurement_assessment,
            risk=state.risk_assessment
        )
        state.final_decision = final_decision.model_dump()

        return final_decision, state
