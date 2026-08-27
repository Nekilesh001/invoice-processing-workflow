import json
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.tools import (
    AGENT_TOOLS_SCHEMA,
    check_duplicate_invoice,
    compare_invoice_to_purchase_order,
    create_review_task,
    lookup_purchase_order,
    lookup_vendor,
    validate_invoice_totals,
)
from app.config import settings
from app.llm.client import LLMClient
from app.schemas.agent import AgentDecisionSchema, AgentState
from app.schemas.invoice import ExtractedInvoice
from app.schemas.processing import ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class AgentDecision:
    """Final decision output schema returned by InvoiceAgent."""
    action: str
    reason: str
    executed_tools: List[Dict[str, Any]] = field(default_factory=list)
    vendor_verified: bool = False
    po_verified: bool = False
    duplicate_checked: bool = False
    confidence_score: float = 1.0
    procurement_assessment: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None


class InvoiceAgent:
    """
    Multi-Agent Invoice Verification Adapter:
    Wraps InvoiceOrchestrator (ProcurementVerificationAgent + FinancialRiskAgent + ApprovalPolicyEngine)
    to provide multi-agent verification while preserving backward compatibility with AgentDecision interface.
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        max_iterations: int = 5,
        prompt_path: Optional[Path] = None,
    ):
        from app.agents.orchestrator import InvoiceOrchestrator
        self.llm_client = llm_client or LLMClient()
        self.max_iterations = max_iterations
        self.orchestrator = InvoiceOrchestrator()

    def evaluate_and_decide(
        self,
        extracted_invoice: ExtractedInvoice,
        validation_result: ValidationResult,
        db_session: Optional[Session] = None,
        on_tool_callback: Optional[Any] = None,
    ) -> AgentDecision:
        """
        Executes multi-agent orchestrator processing and maps results to AgentDecision.
        """
        if self.max_iterations <= 0:
            return AgentDecision(
                action="HUMAN_REVIEW",
                reason="MAX_ITERATIONS_EXCEEDED: Agent exceeded max reasoning steps without reaching conclusion.",
                confidence_score=0.5
            )
        final_decision, state = self.orchestrator.process_invoice(
            extracted_invoice=extracted_invoice,
            validation_result=validation_result,
            db_session=db_session,
            on_tool_callback=on_tool_callback
        )

        executed_tools = []
        for trace in state.agent_traces:
            for t_item in trace.tool_results:
                executed_tools.append({
                    "tool": t_item.get("tool"),
                    "args": t_item.get("args", {}),
                    "output": t_item.get("output", {}),
                    "agent": trace.agent_name
                })

        proc = state.procurement_assessment
        risk = state.risk_assessment

        return AgentDecision(
            action=final_decision.action,
            reason=final_decision.reason,
            executed_tools=executed_tools,
            vendor_verified=proc.vendor_verified if proc else False,
            po_verified=proc.po_verified if proc else False,
            duplicate_checked="check_duplicate_invoice" in [t.get("tool") for t in executed_tools],
            confidence_score=final_decision.confidence_score,
            procurement_assessment=proc.model_dump() if proc else None,
            risk_assessment=risk.model_dump() if risk else None
        )

    def _execute_tool(self, name: str, args: Dict[str, Any], session: Optional[Session], on_tool_callback: Optional[Any] = None) -> Dict[str, Any]:
        """Executes matching Python tool function."""
        logger.info("Executing Tool: %s(args=%s)", name, args)
        fn = self.tool_functions.get(name)
        if not fn:
            err = {"error": f"Unknown tool: {name}"}
            logger.warning("Tool execution error: %s", err)
            return err

        # Create separate args copy for tool invocation so session is not added to JSON serializable args dict
        call_args = dict(args)
        import inspect
        sig = inspect.signature(fn)
        if "session" in sig.parameters:
            call_args["session"] = session

        result = fn(**call_args)
        logger.info("Tool Output: %s -> %s", name, result)

        if on_tool_callback:
            try:
                on_tool_callback(name, args, result)
            except Exception as cb_err:
                logger.warning("on_tool_callback exception: %s", cb_err)

        return result

    def _evaluate_tool_observation(self, fn_name: str, tool_result: Dict[str, Any], state: AgentState) -> Optional[AgentDecisionSchema]:
        """Evaluates tool execution output and updates agent state or stopping decision."""
        if fn_name == "check_duplicate_invoice":
            state.duplicate_checked = True
            if tool_result.get("is_duplicate"):
                return AgentDecisionSchema(
                    decision="HUMAN_REVIEW",
                    reason="DUPLICATE_SUSPECTED: Identical vendor and invoice number already exist in database.",
                    requires_human_review=True,
                    confidence_score=0.99
                )

        elif fn_name == "lookup_vendor":
            if tool_result.get("found") and tool_result.get("is_approved"):
                state.vendor_verified = True
            else:
                v_name = tool_result.get("vendor_name", "Unknown")
                return AgentDecisionSchema(
                    decision="HUMAN_REVIEW",
                    reason=f"UNKNOWN_VENDOR: Vendor '{v_name}' is not registered in master vendor registry.",
                    requires_human_review=True,
                    confidence_score=0.95
                )

        elif fn_name == "lookup_purchase_order":
            if not tool_result.get("found"):
                return AgentDecisionSchema(
                    decision="HUMAN_REVIEW",
                    reason=f"PO_NOT_FOUND: {tool_result.get('message', 'PO missing.')}",
                    requires_human_review=True,
                    confidence_score=0.95
                )
            po_status = tool_result.get("status")
            if po_status in ["EXHAUSTED", "CANCELLED", "CLOSED", "DRAFT"]:
                return AgentDecisionSchema(
                    decision="HUMAN_REVIEW",
                    reason=f"PO_{po_status}: Purchase Order is in invalid state '{po_status}'.",
                    requires_human_review=True,
                    confidence_score=0.95
                )

            auth_total = tool_result.get("authorized_total")
            tot_amount = state.extracted_invoice.total_amount
            if tot_amount is not None and auth_total is not None:
                if abs(Decimal(str(auth_total)) - tot_amount) > Decimal("0.01"):
                    return AgentDecisionSchema(
                        decision="HUMAN_REVIEW",
                        reason=f"PO_MISMATCH: Invoice total (${tot_amount}) does not match authorized PO total (${auth_total}).",
                        requires_human_review=True,
                        confidence_score=0.98
                    )
            state.po_verified = True

        elif fn_name == "compare_invoice_to_purchase_order":
            if not tool_result.get("is_match"):
                reasons = tool_result.get("reasons", ["PO line items mismatch."])
                reason_str = "; ".join(reasons)
                return AgentDecisionSchema(
                    decision="HUMAN_REVIEW",
                    reason=f"PO_LINE_MISMATCH: {reason_str}",
                    requires_human_review=True,
                    confidence_score=0.98
                )

        return None

    def _execute_fallback_agentic_loop(self, state: AgentState, db_session: Optional[Session], on_tool_callback: Optional[Any] = None) -> AgentDecisionSchema:
        """
        Dynamic agentic observation loop for offline/unconfigured API key environments:
        1. Dynamically selects tools based on invoice evidence.
        2. Executes tool and observes result.
        3. If evidence triggers review -> HUMAN_REVIEW.
        4. If all checks pass -> AUTO_PROCESS.
        """
        inv = state.extracted_invoice

        # Tool 1: Duplicate check
        dup_args = {
            "vendor_name": inv.vendor.vendor_name if inv.vendor else None,
            "invoice_number": inv.invoice_number
        }
        dup_out = self._execute_tool("check_duplicate_invoice", dup_args, db_session, on_tool_callback=on_tool_callback)
        state.executed_tools.append({"tool": "check_duplicate_invoice", "args": dup_args, "output": dup_out})
        dec = self._evaluate_tool_observation("check_duplicate_invoice", dup_out, state)
        if dec:
            return dec

        # Tool 2: Vendor lookup
        vendor_name = inv.vendor.vendor_name if inv.vendor else None
        v_args = {"vendor_name": vendor_name}
        v_out = self._execute_tool("lookup_vendor", v_args, db_session, on_tool_callback=on_tool_callback)
        state.executed_tools.append({"tool": "lookup_vendor", "args": v_args, "output": v_out})
        dec = self._evaluate_tool_observation("lookup_vendor", v_out, state)
        if dec:
            return dec

        # Tool 3: PO lookup ONLY if po_number exists (Dynamic tool selection evidence check)
        if inv.po_number:
            po_args = {"po_number": inv.po_number}
            po_out = self._execute_tool("lookup_purchase_order", po_args, db_session, on_tool_callback=on_tool_callback)
            state.executed_tools.append({"tool": "lookup_purchase_order", "args": po_args, "output": po_out})
            dec = self._evaluate_tool_observation("lookup_purchase_order", po_out, state)
            if dec:
                return dec

            # Tool 4: Compare PO Line Items
            if inv.line_items:
                raw_items = [json.loads(item.model_dump_json()) for item in inv.line_items]
                comp_args = {
                    "po_number": inv.po_number,
                    "invoice_line_items": raw_items
                }
                comp_out = self._execute_tool("compare_invoice_to_purchase_order", comp_args, db_session, on_tool_callback=on_tool_callback)
                state.executed_tools.append({"tool": "compare_invoice_to_purchase_order", "args": comp_args, "output": comp_out})
                dec = self._evaluate_tool_observation("compare_invoice_to_purchase_order", comp_out, state)
                if dec:
                    return dec

        # Check deterministic validation
        if not state.validation_result.is_valid:
            err_msg = state.validation_result.errors[0].message if state.validation_result.errors else "Validation error."
            return AgentDecisionSchema(
                decision="HUMAN_REVIEW",
                reason=f"VALIDATION_FAILED: {err_msg}",
                requires_human_review=True,
                confidence_score=0.95
            )

        return AgentDecisionSchema(
            decision="AUTO_PROCESS",
            reason=f"SUCCESS: Invoice '{inv.invoice_number}' verified via tools.",
            requires_human_review=False,
            confidence_score=1.0
        )
