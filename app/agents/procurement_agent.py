import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.tools import (
    compare_invoice_to_purchase_order,
    lookup_purchase_order,
    lookup_vendor,
    validate_invoice_totals,
)
from app.schemas.invoice import ExtractedInvoice
from app.schemas.multi_agent import AgentTrace, ProcurementAssessment
from app.schemas.processing import ValidationResult

logger = logging.getLogger(__name__)


class ProcurementAgent:
    """
    Specialized Procurement Verification Agent:
    Responsible solely for procurement-side verification:
    - Master Vendor registry verification
    - Purchase Order validation & balance check
    - Invoice line item to PO line item matching
    - Procurement compliance policy enforcement
    """

    def __init__(self, name: str = "ProcurementVerificationAgent"):
        self.name = name

    def evaluate(
        self,
        extracted_invoice: ExtractedInvoice,
        validation_result: ValidationResult,
        db_session: Optional[Session] = None,
    ) -> tuple[ProcurementAssessment, AgentTrace]:
        """
        Evaluates procurement compliance and returns a ProcurementAssessment and AgentTrace.
        """
        import uuid
        from datetime import datetime

        run_id = f"proc-{uuid.uuid4().hex[:8]}"
        started_at = datetime.utcnow()
        tools_used = []
        tool_results = []
        issues = []
        evidence = []

        vendor_name = extracted_invoice.vendor.vendor_name if extracted_invoice.vendor else None
        po_number = extracted_invoice.po_number

        vendor_verified = False
        po_verified = False
        po_match = False
        line_match_status = "NOT_APPLICABLE"
        recommended_action = "CONTINUE"
        status = "PASS"

        # Step 1: Vendor Verification
        tools_used.append("lookup_vendor")
        vendor_res = lookup_vendor(vendor_name, session=db_session)
        tool_results.append({"tool": "lookup_vendor", "args": {"vendor_name": vendor_name}, "output": vendor_res})

        if vendor_res.get("found") and vendor_res.get("status") == "VERIFIED":
            vendor_verified = True
            evidence.append({"type": "vendor_verification", "details": vendor_res})
        else:
            vendor_verified = False
            issues.append("UNKNOWN_VENDOR")
            status = "REVIEW"
            recommended_action = "HUMAN_REVIEW"
            evidence.append({"type": "vendor_verification_failure", "details": vendor_res})

        # Step 2: PO Verification & Matching
        if po_number and po_number.strip() and po_number.upper() != "NONE":
            tools_used.append("lookup_purchase_order")
            po_res = lookup_purchase_order(po_number, session=db_session)
            tool_results.append({"tool": "lookup_purchase_order", "args": {"po_number": po_number}, "output": po_res})

            if po_res.get("found") and po_res.get("status") in ["PO_FOUND", "APPROVED"]:
                po_verified = True
                evidence.append({"type": "po_verification", "details": po_res})

                auth_total = po_res.get("authorized_total")
                tot_amount = float(extracted_invoice.total_amount or 0.0)
                if auth_total is not None and abs(float(auth_total) - tot_amount) > 0.01:
                    po_verified = False
                    po_match = False
                    issues.append(f"PO_MISMATCH: Invoice total (${tot_amount:.2f}) does not match authorized PO total (${auth_total:.2f}).")
                    status = "FAIL"
                    recommended_action = "HUMAN_REVIEW"
                elif extracted_invoice.line_items and po_res.get("line_items"):
                    tools_used.append("compare_invoice_to_purchase_order")
                    raw_line_items = [item.model_dump() for item in extracted_invoice.line_items]
                    match_res = compare_invoice_to_purchase_order(
                        po_number=po_number,
                        invoice_line_items=raw_line_items,
                        session=db_session
                    )
                    tool_results.append({"tool": "compare_invoice_to_purchase_order", "args": {"po_number": po_number, "line_items_count": len(raw_line_items)}, "output": match_res})
                    evidence.append({"type": "po_line_matching", "details": match_res})

                    is_matched = match_res.get("is_match") or match_res.get("matched", False)
                    if is_matched:
                        po_match = True
                        line_match_status = "MATCH"
                    else:
                        po_match = False
                        line_match_status = "MISMATCH"
                        reasons_str = "; ".join(match_res.get("reasons", [])) or match_res.get("reason", "Line mismatch")
                        issues.append(f"PO_LINE_MISMATCH: {reasons_str}")
                        status = "FAIL"
                        recommended_action = "HUMAN_REVIEW"
                else:
                    po_match = True
                    line_match_status = "NO_LINES_TO_MATCH"
            else:
                po_verified = False
                issues.append(f"PO_NOT_FOUND: Purchase order '{po_number}' invalid or missing")
                if status != "FAIL":
                    status = "REVIEW"
                recommended_action = "HUMAN_REVIEW"
                evidence.append({"type": "po_verification_failure", "details": po_res})
        else:
            # Invoice does not reference a PO
            line_match_status = "NO_PO_REFERENCED"
            evidence.append({"type": "po_info", "message": "No purchase order specified on invoice"})

        # Step 3: Validate Invoice Math Totals
        tools_used.append("validate_invoice_totals")
        totals_args = {
            "subtotal": float(extracted_invoice.subtotal or 0.0),
            "total_amount": float(extracted_invoice.total_amount or 0.0),
            "tax_amount": float(extracted_invoice.tax_amount or 0.0),
            "shipping_charge": float(extracted_invoice.shipping_charge or 0.0),
            "discount": float(extracted_invoice.discount or 0.0),
        }
        totals_res = validate_invoice_totals(**totals_args)
        tool_results.append({"tool": "validate_invoice_totals", "args": totals_args, "output": totals_res})

        if not totals_res.get("is_valid"):
            issues.append(f"TOTAL_MISMATCH: {totals_res.get('reason')}")
            status = "FAIL"
            recommended_action = "HUMAN_REVIEW"

        completed_at = datetime.utcnow()

        assessment = ProcurementAssessment(
            status=status,
            vendor_verified=vendor_verified,
            po_verified=po_verified,
            po_match=po_match,
            line_match_status=line_match_status,
            issues=issues,
            evidence=evidence,
            recommended_action=recommended_action,
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
            errors=issues,
        )

        return assessment, trace
