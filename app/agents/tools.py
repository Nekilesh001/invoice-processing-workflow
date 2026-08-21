from decimal import Decimal
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.database.models import VendorModel, ReviewTaskModel
from app.database.repositories.invoice_repository import InvoiceRepository
from app.database.repositories.purchase_order_repository import PurchaseOrderRepository


def lookup_vendor(vendor_name: Optional[str], session: Optional[Session] = None) -> Dict[str, Any]:
    """
    Agent tool: Looks up vendor details in master database registry.
    Safe behavior: Unknown vendors return UNKNOWN_VENDOR status and are NOT automatically verified.
    """
    if not vendor_name or not vendor_name.strip():
        return {
            "found": False,
            "status": "MISSING_VENDOR",
            "is_approved": False,
            "message": "Vendor name was not provided."
        }

    clean_name = vendor_name.strip()

    if session:
        try:
            vendor = session.query(VendorModel).filter(VendorModel.name.ilike(f"%{clean_name}%")).first()
            if vendor:
                return {
                    "found": True,
                    "status": "VERIFIED",
                    "vendor_id": vendor.id,
                    "vendor_name": vendor.name,
                    "tax_id": vendor.tax_id,
                    "is_approved": True,
                    "message": f"Vendor '{vendor.name}' verified in database."
                }
        except Exception as e:
            return {
                "found": False,
                "status": "DATABASE_ERROR",
                "is_approved": False,
                "vendor_name": clean_name,
                "message": f"Database error during vendor lookup: {str(e)}"
            }

    # Safe behavior: Return UNKNOWN_VENDOR if not registered in master vendor table
    return {
        "found": False,
        "status": "UNKNOWN_VENDOR",
        "vendor_name": clean_name,
        "is_approved": False,
        "message": f"Vendor '{clean_name}' was not found in master vendor registry."
    }


def lookup_purchase_order(po_number: Optional[str], session: Optional[Session] = None) -> Dict[str, Any]:
    """
    Agent tool: Looks up Purchase Order details in enterprise MySQL database via PurchaseOrderRepository.
    Returns authorized total, vendor match, remaining balance, and PO status.
    """
    if not po_number or not po_number.strip():
        return {
            "found": False,
            "status": "NO_PO_PROVIDED",
            "message": "No purchase order number provided."
        }

    clean_po = po_number.strip().upper()

    if not session:
        return {
            "found": False,
            "status": "NO_DATABASE_SESSION",
            "po_number": clean_po,
            "message": "Database session required for purchase order lookup."
        }

    try:
        repo = PurchaseOrderRepository()
        po = repo.get_by_po_number(session, clean_po)

        if not po:
            return {
                "found": False,
                "status": "PO_NOT_FOUND",
                "po_number": clean_po,
                "message": f"Purchase Order '{clean_po}' was not found in enterprise PO database."
            }

        line_items_summary = []
        if po.line_items:
            for li in po.line_items:
                line_items_summary.append({
                    "description": li.description,
                    "quantity": float(li.quantity),
                    "unit_price": float(li.unit_price),
                    "line_total": float(li.line_total)
                })

        return {
            "found": True,
            "status": po.status,
            "po_number": clean_po,
            "vendor_id": po.vendor_id,
            "vendor_name": po.vendor.name if po.vendor else "Unknown",
            "authorized_total": float(po.authorized_total),
            "remaining_balance": float(po.remaining_balance),
            "currency": po.currency,
            "line_items": line_items_summary,
            "message": f"Purchase Order '{clean_po}' found in database. Authorized total: ${po.authorized_total}."
        }
    except Exception as e:
        return {
            "found": False,
            "status": "DATABASE_ERROR",
            "po_number": clean_po,
            "message": f"Database error during purchase order lookup: {str(e)}"
        }


def check_duplicate_invoice(
    vendor_name: Optional[str], invoice_number: Optional[str], session: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Agent tool: Queries database for duplicate vendor + invoice_number pairs.
    """
    if not vendor_name or not invoice_number:
        return {"is_duplicate": False, "reason": "Missing vendor or invoice number"}

    if session:
        repo = InvoiceRepository()
        is_dup = repo.check_duplicate(session, vendor_name, invoice_number)
        return {
            "is_duplicate": is_dup,
            "vendor_name": vendor_name,
            "invoice_number": invoice_number,
            "message": "Duplicate detected in database." if is_dup else "No duplicate found."
        }

    return {"is_duplicate": False, "message": "No duplicate found (no active session)."}


def validate_invoice_totals(
    subtotal: float,
    total_amount: float,
    tax_amount: float = 0.0,
    shipping_charge: float = 0.0,
    discount: float = 0.0,
    other_charges: float = 0.0
) -> Dict[str, Any]:
    """
    Agent tool: Executes deterministic Python math validation: subtotal + tax + shipping + other - discount == total_amount.
    """
    sub_d = Decimal(str(subtotal))
    tax_d = Decimal(str(tax_amount))
    ship_d = Decimal(str(shipping_charge))
    disc_d = Decimal(str(discount))
    other_d = Decimal(str(other_charges))
    tot_d = Decimal(str(total_amount))

    expected = sub_d + tax_d + ship_d + other_d - disc_d
    diff = abs(expected - tot_d)

    is_valid = diff <= Decimal("0.01")
    return {
        "is_valid": is_valid,
        "expected_total": float(expected),
        "claimed_total": float(tot_d),
        "difference": float(diff),
        "message": "Invoice math is correct." if is_valid else f"Math mismatch: Subtotal + Tax - Discount = ${expected:.2f}, but Total claims ${tot_d:.2f}."
    }


def create_review_task(invoice_id: int, reason: str, session: Optional[Session] = None) -> Dict[str, Any]:
    """
    Agent tool: Creates a human review queue task.
    Idempotent: Avoids duplicate creation if a PENDING review task already exists for invoice_id.
    """
    if session:
        existing = session.query(ReviewTaskModel).filter(
            ReviewTaskModel.invoice_id == invoice_id,
            ReviewTaskModel.status == "PENDING"
        ).first()

        if existing:
            return {
                "task_id": existing.id,
                "invoice_id": invoice_id,
                "reason": existing.reason,
                "status": "PENDING",
                "message": f"Idempotent: Pending review task #{existing.id} already exists for invoice #{invoice_id}."
            }

        review_task = ReviewTaskModel(
            invoice_id=invoice_id,
            reason=reason,
            status="PENDING"
        )
        session.add(review_task)
        session.flush()
        return {
            "task_id": review_task.id,
            "invoice_id": invoice_id,
            "reason": reason,
            "status": "PENDING",
            "message": f"Human review task #{review_task.id} created for reason: '{reason}'."
        }

    return {
        "task_id": 999,
        "invoice_id": invoice_id,
        "reason": reason,
        "status": "PENDING",
        "message": f"Simulated review task created for reason: '{reason}'."
    }


# OpenAI Function / Tool Calling Schema Specifications
AGENT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "lookup_vendor",
            "description": "Looks up vendor details in master database registry to verify tax ID and approval status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vendor_name": {"type": "string", "description": "Name of the vendor/biller to verify"}
                },
                "required": ["vendor_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_purchase_order",
            "description": "Looks up Purchase Order in PO database to verify authorized amount, vendor, and status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "po_number": {"type": "string", "description": "Purchase Order number (e.g. PO-8842)"}
                },
                "required": ["po_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_duplicate_invoice",
            "description": "Queries database for pre-existing matching vendor name and invoice number pairs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vendor_name": {"type": "string", "description": "Name of the vendor"},
                    "invoice_number": {"type": "string", "description": "Invoice number"}
                },
                "required": ["vendor_name", "invoice_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_invoice_totals",
            "description": "Executes Python deterministic arithmetic check: subtotal + tax + shipping + other - discount == total_amount.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subtotal": {"type": "number", "description": "Subtotal amount"},
                    "total_amount": {"type": "number", "description": "Claimed total amount"},
                    "tax_amount": {"type": "number", "description": "Tax amount"},
                    "shipping_charge": {"type": "number", "description": "Shipping fee"},
                    "discount": {"type": "number", "description": "Discount amount"}
                },
                "required": ["subtotal", "total_amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_review_task",
            "description": "Routes invoice to human review queue due to validation error, PO mismatch, or duplicate suspect.",
            "parameters": {
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "integer", "description": "Invoice database ID"},
                    "reason": {"type": "string", "description": "Reason for human review escalation"}
                },
                "required": ["invoice_id", "reason"]
            }
        }
    }
]
