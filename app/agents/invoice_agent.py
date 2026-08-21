from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.tools import (
    check_duplicate_invoice,
    lookup_purchase_order,
    lookup_vendor,
    create_review_task,
)
from app.schemas.invoice import ExtractedInvoice
from app.schemas.processing import ValidationResult


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
    Autonomous Agentic Decision Engine for Invoice Workflow:
    - Analyzes extracted invoice context.
    - Dynamically invokes specialized verification tools (Vendor lookup, PO lookup, Duplicate check).
    - Evaluates business policies and PO amount alignment.
    - Routes invoice to AUTO_PROCESS or HUMAN_REVIEW queue with explicit audit trace.
    """

    def evaluate_and_decide(
        self,
        extracted_invoice: ExtractedInvoice,
        validation_result: ValidationResult,
        db_session: Optional[Session] = None,
    ) -> AgentDecision:
        """
        Executes autonomous agentic workflow and tool calls to determine processing action.
        """
        executed_tools = []
        vendor_name = extracted_invoice.vendor.vendor_name if extracted_invoice.vendor else None
        invoice_number = extracted_invoice.invoice_number
        po_number = extracted_invoice.po_number
        total_amount = extracted_invoice.total_amount

        # Tool Call 1: Duplicate Check
        dup_res = check_duplicate_invoice(vendor_name, invoice_number, session=db_session)
        executed_tools.append({"tool": "check_duplicate_invoice", "output": dup_res})

        if dup_res.get("is_duplicate"):
            return AgentDecision(
                action="HUMAN_REVIEW",
                reason="DUPLICATE_SUSPECTED: Identical vendor and invoice number already present in database.",
                executed_tools=executed_tools,
                duplicate_checked=True,
                confidence_score=0.99
            )

        # Tool Call 2: Vendor Lookup & Verification
        vendor_res = lookup_vendor(vendor_name, session=db_session)
        executed_tools.append({"tool": "lookup_vendor", "output": vendor_res})

        if not vendor_res.get("found"):
            return AgentDecision(
                action="HUMAN_REVIEW",
                reason=f"VENDOR_UNKNOWN: Vendor '{vendor_name}' is missing or not recognized in master registry.",
                executed_tools=executed_tools,
                vendor_verified=False,
                confidence_score=0.85
            )

        vendor_verified = vendor_res.get("is_approved", False)

        # Tool Call 3: Purchase Order Lookup & Verification (if PO present)
        po_verified = False
        if po_number:
            po_res = lookup_purchase_order(po_number, session=db_session)
            executed_tools.append({"tool": "lookup_purchase_order", "output": po_res})

            if not po_res.get("found"):
                return AgentDecision(
                    action="HUMAN_REVIEW",
                    reason=f"PO_NOT_FOUND: Purchase Order '{po_number}' specified on invoice does not exist.",
                    executed_tools=executed_tools,
                    vendor_verified=vendor_verified,
                    po_verified=False,
                    confidence_score=0.90
                )

            if po_res.get("status") == "EXHAUSTED":
                return AgentDecision(
                    action="HUMAN_REVIEW",
                    reason=f"PO_EXHAUSTED: Purchase Order '{po_number}' has zero remaining authorized balance.",
                    executed_tools=executed_tools,
                    vendor_verified=vendor_verified,
                    po_verified=False,
                    confidence_score=0.95
                )

            authorized_total = po_res.get("authorized_total")
            if total_amount is not None and authorized_total is not None:
                diff = abs(authorized_total - total_amount)
                if diff > Decimal("0.01"):
                    return AgentDecision(
                        action="HUMAN_REVIEW",
                        reason=(
                            f"PO_MISMATCH: Invoice total (${total_amount}) does not match authorized PO total "
                            f"(${authorized_total}) for PO '{po_number}'."
                        ),
                        executed_tools=executed_tools,
                        vendor_verified=vendor_verified,
                        po_verified=False,
                        confidence_score=0.98
                    )

            po_verified = True

        # Rule Check 4: Deterministic Validation Errors
        if not validation_result.is_valid:
            primary_error = validation_result.errors[0].message if validation_result.errors else "Validation failed."
            return AgentDecision(
                action="HUMAN_REVIEW",
                reason=f"VALIDATION_FAILED: {primary_error}",
                executed_tools=executed_tools,
                vendor_verified=vendor_verified,
                po_verified=po_verified,
                confidence_score=0.95
            )

        # All agent checks passed -> Auto Process
        return AgentDecision(
            action="AUTO_PROCESS",
            reason=(
                f"SUCCESS: Invoice '{invoice_number}' fully verified via vendor lookup, "
                f"{'PO matching (' + po_number + '), ' if po_verified else ''}math validation, and duplicate checks."
            ),
            executed_tools=executed_tools,
            vendor_verified=vendor_verified,
            po_verified=po_verified,
            duplicate_checked=True,
            confidence_score=1.0
        )
