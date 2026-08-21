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
    """Structured decision output produced by InvoiceAgent."""
    action: str  # "AUTO_PROCESS" or "HUMAN_REVIEW"
    reason: str
    executed_tools: List[Dict[str, Any]] = field(default_factory=list)
    vendor_verified: bool = False
    po_verified: bool = False
    duplicate_checked: bool = False
    confidence_score: float = 1.0


class InvoiceAgent:
    """
    Autonomous LLM-driven Tool-Using Agentic Decision Engine:
    - Bounded Observe -> Reason -> Act -> Observe loop (max_iterations = 5).
    - Dynamically selects domain tools via OpenAI-compatible function calling API.
    - Evaluates tool responses and PO amount alignment.
    - Routes to AUTO_PROCESS or HUMAN_REVIEW with complete audit trace.
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        max_iterations: int = 5,
        prompt_path: Optional[Path] = None,
    ):
        self.llm_client = llm_client or LLMClient()
        self.max_iterations = max_iterations
        self.prompt_path = prompt_path or (
            settings.BASE_DIR / "app" / "prompts" / "invoice_agent_v1.txt"
        )
        self.system_prompt = self._load_system_prompt()

        self.tool_functions = {
            "lookup_vendor": lookup_vendor,
            "lookup_purchase_order": lookup_purchase_order,
            "check_duplicate_invoice": check_duplicate_invoice,
            "validate_invoice_totals": validate_invoice_totals,
            "create_review_task": create_review_task,
        }

    def _load_system_prompt(self) -> str:
        if self.prompt_path.exists():
            return self.prompt_path.read_text(encoding="utf-8")
        return "You are an autonomous AI Invoice Verification Agent."

    def evaluate_and_decide(
        self,
        extracted_invoice: ExtractedInvoice,
        validation_result: ValidationResult,
        db_session: Optional[Session] = None,
    ) -> AgentDecision:
        """
        Executes bounded agent loop: Observe -> Reason -> Act -> Observe.
        """
        state = AgentState(
            extracted_invoice=extracted_invoice,
            validation_result=validation_result,
            max_iterations=self.max_iterations,
        )

        vendor_name = extracted_invoice.vendor.vendor_name if extracted_invoice.vendor else None
        invoice_number = extracted_invoice.invoice_number
        po_number = extracted_invoice.po_number
        total_amount = extracted_invoice.total_amount

        # Build initial prompt messages
        context_str = (
            f"Extracted Invoice Data:\n"
            f"- Vendor Name   : {vendor_name or 'N/A'}\n"
            f"- Invoice Number: {invoice_number or 'N/A'}\n"
            f"- PO Number     : {po_number or 'NONE'}\n"
            f"- Total Amount  : ${total_amount if total_amount is not None else 'N/A'}\n"
            f"- Subtotal      : ${extracted_invoice.subtotal}\n"
            f"- Tax Amount    : ${extracted_invoice.tax_amount}\n"
            f"- Validation Status: {'PASSED' if validation_result.is_valid else 'FAILED'}\n"
        )
        if validation_result.errors:
            err_msg = "; ".join(e.message for e in validation_result.errors)
            context_str += f"- Validation Errors: {err_msg}\n"

        state.messages.append({"role": "system", "content": self.system_prompt})
        state.messages.append({"role": "user", "content": context_str})

        # Agent Loop
        while state.iteration_count < state.max_iterations:
            state.iteration_count += 1

            # Check if LLM client key is configured; if not, execute local tool sequence
            try:
                msg_obj = self.llm_client.chat_completion_with_tools(
                    messages=state.messages, tools=AGENT_TOOLS_SCHEMA
                )
                tool_calls = getattr(msg_obj, "tool_calls", None)
                content = getattr(msg_obj, "content", None)
            except Exception as e:
                logger.info("LLM tool call fallback triggered: %s", str(e))
                tool_calls = None
                content = None

            # Path A: LLM specified tool calls
            if tool_calls:
                for tool_call in tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                    tool_result = self._execute_tool(fn_name, fn_args, db_session)
                    state.executed_tools.append({"tool": fn_name, "args": fn_args, "output": tool_result})

                    # Append assistant tool call and tool response to message history
                    state.messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {"name": fn_name, "arguments": json.dumps(fn_args)}
                            }
                        ]
                    })
                    state.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result)
                    })

                    # Evaluate tool observations
                    stop_decision = self._evaluate_tool_observation(fn_name, tool_result, state)
                    if stop_decision:
                        state.final_decision = stop_decision
                        break

                if state.final_decision:
                    break

            # Path B: LLM returned content (or local offline agentic tool reasoning fallback)
            else:
                decision = self._execute_fallback_agentic_loop(state, db_session)
                state.final_decision = decision
                break

        # Process final decision or fallback to HUMAN_REVIEW
        if not state.final_decision:
            state.final_decision = AgentDecisionSchema(
                decision="HUMAN_REVIEW",
                reason="MAX_ITERATIONS_EXCEEDED: Agent reached iteration limit without conclusive decision.",
                requires_human_review=True
            )

        return AgentDecision(
            action=state.final_decision.decision,
            reason=state.final_decision.reason,
            executed_tools=state.executed_tools,
            vendor_verified=state.vendor_verified,
            po_verified=state.po_verified,
            duplicate_checked=state.duplicate_checked,
            confidence_score=state.final_decision.confidence_score
        )

    def _execute_tool(self, name: str, args: Dict[str, Any], session: Optional[Session]) -> Dict[str, Any]:
        """Executes matching Python tool function."""
        fn = self.tool_functions.get(name)
        if not fn:
            return {"error": f"Unknown tool: {name}"}

        # Check if tool accepts session parameter
        import inspect
        sig = inspect.signature(fn)
        if "session" in sig.parameters:
            args["session"] = session

        return fn(**args)

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
                return AgentDecisionSchema(
                    decision="HUMAN_REVIEW",
                    reason=f"VENDOR_UNKNOWN: {tool_result.get('message', 'Vendor unverified.')}",
                    requires_human_review=True,
                    confidence_score=0.90
                )

        elif fn_name == "lookup_purchase_order":
            if not tool_result.get("found"):
                return AgentDecisionSchema(
                    decision="HUMAN_REVIEW",
                    reason=f"PO_NOT_FOUND: {tool_result.get('message', 'PO missing.')}",
                    requires_human_review=True,
                    confidence_score=0.95
                )
            if tool_result.get("status") == "EXHAUSTED":
                return AgentDecisionSchema(
                    decision="HUMAN_REVIEW",
                    reason=f"PO_EXHAUSTED: {tool_result.get('message', 'PO exhausted.')}",
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

        return None

    def _execute_fallback_agentic_loop(self, state: AgentState, db_session: Optional[Session]) -> AgentDecisionSchema:
        """
        Dynamic agentic observation loop for offline/unconfigured API key environments:
        1. Dynamically selects tools based on invoice evidence.
        2. Executes tool and observes result.
        3. If evidence triggers review -> HUMAN_REVIEW.
        4. If all checks pass -> AUTO_PROCESS.
        """
        inv = state.extracted_invoice

        # Tool 1: Duplicate check
        dup_out = self._execute_tool("check_duplicate_invoice", {
            "vendor_name": inv.vendor.vendor_name if inv.vendor else None,
            "invoice_number": inv.invoice_number
        }, db_session)
        state.executed_tools.append({"tool": "check_duplicate_invoice", "output": dup_out})
        dec = self._evaluate_tool_observation("check_duplicate_invoice", dup_out, state)
        if dec:
            return dec

        # Tool 2: Vendor lookup
        vendor_name = inv.vendor.vendor_name if inv.vendor else None
        v_out = self._execute_tool("lookup_vendor", {"vendor_name": vendor_name}, db_session)
        state.executed_tools.append({"tool": "lookup_vendor", "output": v_out})
        dec = self._evaluate_tool_observation("lookup_vendor", v_out, state)
        if dec:
            return dec

        # Tool 3: PO lookup ONLY if po_number exists (Dynamic tool selection evidence check)
        if inv.po_number:
            po_out = self._execute_tool("lookup_purchase_order", {"po_number": inv.po_number}, db_session)
            state.executed_tools.append({"tool": "lookup_purchase_order", "output": po_out})
            dec = self._evaluate_tool_observation("lookup_purchase_order", po_out, state)
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
