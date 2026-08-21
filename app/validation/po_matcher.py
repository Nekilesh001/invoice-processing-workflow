import re
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set

from app.config import settings
from app.schemas.matching import (
    InvoicePOMatchResult,
    LineMatchResult,
    LineMatchStatus,
    POMatchStatus,
)


def normalize_string(text: Optional[str]) -> str:
    """Normalizes string by lowercasing, stripping, and removing special punctuation."""
    if not text:
        return ""
    clean = text.lower().strip()
    clean = re.sub(r"[^\w\s]", "", clean)
    return re.sub(r"\s+", " ", clean)


def match_invoice_to_po(
    invoice_items: List[Dict[str, Any]],
    po_items: List[Dict[str, Any]],
    po_number: Optional[str] = None,
    po_authorized_total: Optional[Decimal] = None,
    invoice_total: Optional[Decimal] = None
) -> InvoicePOMatchResult:
    """
    Executes deterministic Python matching between Invoice Line Items and Purchase Order Line Items.
    Separates LLM reasoning from deterministic business math verification.
    """
    price_tol = Decimal(str(settings.PO_PRICE_TOLERANCE))
    total_tol = Decimal(str(settings.PO_TOTAL_TOLERANCE))
    qty_tol = Decimal(str(settings.PO_QUANTITY_TOLERANCE))

    line_results: List[LineMatchResult] = []
    used_po_indices: Set[int] = set()

    matched_count = 0
    mismatched_count = 0
    missing_from_po_count = 0
    overall_reasons: List[str] = []

    for inv_idx, inv_item in enumerate(invoice_items):
        inv_desc = inv_item.get("description", "")
        inv_code = inv_item.get("product_code")
        inv_qty = Decimal(str(inv_item.get("quantity", 1.0)))
        inv_price = Decimal(str(inv_item.get("unit_price", 0.0)))
        inv_total = Decimal(str(inv_item.get("line_total", inv_qty * inv_price)))

        norm_inv_desc = normalize_string(inv_desc)
        norm_inv_code = normalize_string(inv_code) if inv_code else None

        best_po_idx: Optional[int] = None
        matched_by: Optional[str] = None
        candidate_indices: List[int] = []

        # Strategy 1: Product Code Match
        if norm_inv_code:
            for p_idx, po_item in enumerate(po_items):
                if p_idx in used_po_indices:
                    continue
                p_code = po_item.get("product_code")
                if p_code and normalize_string(p_code) == norm_inv_code:
                    candidate_indices.append(p_idx)
            if candidate_indices:
                matched_by = "product_code"

        # Strategy 2: Description Match (Fallback)
        if not candidate_indices and norm_inv_desc:
            for p_idx, po_item in enumerate(po_items):
                if p_idx in used_po_indices:
                    continue
                p_desc = normalize_string(po_item.get("description", ""))
                # Exact or substring match
                if p_desc and (norm_inv_desc == p_desc or norm_inv_desc in p_desc or p_desc in norm_inv_desc):
                    candidate_indices.append(p_idx)
            if candidate_indices:
                matched_by = "description"

        # Ambiguous match detection
        if len(candidate_indices) > 1:
            line_results.append(
                LineMatchResult(
                    invoice_line_id=inv_idx + 1,
                    invoice_description=inv_desc,
                    product_code=inv_code,
                    invoice_quantity=inv_qty,
                    invoice_unit_price=inv_price,
                    invoice_line_total=inv_total,
                    status=LineMatchStatus.AMBIGUOUS_MATCH,
                    reasons=[f"Ambiguous match: Line matched {len(candidate_indices)} candidate PO lines."]
                )
            )
            mismatched_count += 1
            overall_reasons.append(f"Line '{inv_desc}' is ambiguous across multiple PO lines.")
            continue

        if len(candidate_indices) == 1:
            best_po_idx = candidate_indices[0]
            used_po_indices.add(best_po_idx)
        else:
            best_po_idx = None

        if best_po_idx is None:
            # Line missing from PO
            line_results.append(
                LineMatchResult(
                    invoice_line_id=inv_idx + 1,
                    invoice_description=inv_desc,
                    product_code=inv_code,
                    invoice_quantity=inv_qty,
                    invoice_unit_price=inv_price,
                    invoice_line_total=inv_total,
                    status=LineMatchStatus.MISSING_FROM_PO,
                    reasons=[f"Line item '{inv_desc}' not found in PO line items."]
                )
            )
            missing_from_po_count += 1
            overall_reasons.append(f"Invoice item '{inv_desc}' is missing from Purchase Order.")
            continue

        # Single matched PO item -> Execute deterministic math comparisons
        po_item = po_items[best_po_idx]
        po_desc = po_item.get("description", "")
        po_qty = Decimal(str(po_item.get("quantity", 1.0)))
        po_price = Decimal(str(po_item.get("unit_price", 0.0)))
        po_total = Decimal(str(po_item.get("line_total", po_qty * po_price)))

        qty_diff = abs(inv_qty - po_qty)
        price_diff = abs(inv_price - po_price)
        total_diff = abs(inv_total - po_total)

        line_status = LineMatchStatus.MATCH
        line_reasons: List[str] = []

        if qty_diff > qty_tol:
            line_status = LineMatchStatus.QUANTITY_MISMATCH
            line_reasons.append(f"Quantity mismatch: Invoice claims {inv_qty}, PO authorized {po_qty}.")

        if price_diff > price_tol:
            if line_status == LineMatchStatus.MATCH:
                line_status = LineMatchStatus.PRICE_MISMATCH
            line_reasons.append(f"Unit price mismatch: Invoice claims ${inv_price:.2f}, PO specifies ${po_price:.2f}.")

        if total_diff > total_tol and line_status == LineMatchStatus.MATCH:
            line_status = LineMatchStatus.TOTAL_MISMATCH
            line_reasons.append(f"Line total mismatch: Invoice claims ${inv_total:.2f}, PO line total is ${po_total:.2f}.")

        line_res = LineMatchResult(
            invoice_line_id=inv_idx + 1,
            po_line_id=best_po_idx + 1,
            invoice_description=inv_desc,
            po_description=po_desc,
            product_code=inv_code or po_item.get("product_code"),
            invoice_quantity=inv_qty,
            po_quantity=po_qty,
            quantity_difference=qty_diff,
            invoice_unit_price=inv_price,
            po_unit_price=po_price,
            unit_price_difference=price_diff,
            invoice_line_total=inv_total,
            po_line_total=po_total,
            status=line_status,
            reasons=line_reasons
        )
        line_results.append(line_res)

        if line_status == LineMatchStatus.MATCH:
            matched_count += 1
        else:
            mismatched_count += 1
            overall_reasons.extend(line_reasons)

    # Check for PO lines missing from Invoice
    missing_from_invoice_count = 0
    for p_idx, po_item in enumerate(po_items):
        if p_idx not in used_po_indices:
            missing_from_invoice_count += 1
            po_desc = po_item.get("description", "Item")
            line_results.append(
                LineMatchResult(
                    po_line_id=p_idx + 1,
                    po_description=po_desc,
                    product_code=po_item.get("product_code"),
                    po_quantity=Decimal(str(po_item.get("quantity", 1.0))),
                    po_unit_price=Decimal(str(po_item.get("unit_price", 0.0))),
                    po_line_total=Decimal(str(po_item.get("line_total", 0.0))),
                    status=LineMatchStatus.MISSING_FROM_INVOICE,
                    reasons=[f"PO line item '{po_desc}' was not billed on invoice."]
                )
            )
            overall_reasons.append(f"PO line '{po_desc}' missing from invoice.")

    # Calculate overall status
    is_match = (
        mismatched_count == 0
        and missing_from_po_count == 0
        and missing_from_invoice_count == 0
    )

    if is_match:
        overall_status = POMatchStatus.MATCH
    elif matched_count > 0:
        overall_status = POMatchStatus.PARTIAL_MATCH
    else:
        overall_status = POMatchStatus.MISMATCH

    return InvoicePOMatchResult(
        is_match=is_match,
        overall_status=overall_status,
        po_number=po_number,
        matched_line_count=matched_count,
        mismatched_line_count=mismatched_count,
        missing_from_po_count=missing_from_po_count,
        missing_from_invoice_count=missing_from_invoice_count,
        reasons=overall_reasons,
        line_results=line_results
    )
