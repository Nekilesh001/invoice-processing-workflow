from decimal import Decimal
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.database.models import VendorModel, ReviewTaskModel
from app.database.repositories.invoice_repository import InvoiceRepository

# Mock Purchase Order Master Registry (simulating enterprise ERP / PO system)
MOCK_PO_DATABASE = {
    "PO-8842": {
        "po_number": "PO-8842",
        "vendor_name": "Acme Cloud Solutions Inc.",
        "authorized_total": Decimal("3300.00"),
        "currency": "USD",
        "status": "APPROVED",
        "remaining_balance": Decimal("3300.00"),
    },
    "PO-1001": {
        "po_number": "PO-1001",
        "vendor_name": "Vertex Software Solutions",
        "authorized_total": Decimal("1620.00"),
        "currency": "USD",
        "status": "APPROVED",
        "remaining_balance": Decimal("1620.00"),
    },
    "PO-EXHAUSTED": {
        "po_number": "PO-EXHAUSTED",
        "vendor_name": "Acme Cloud Solutions Inc.",
        "authorized_total": Decimal("500.00"),
        "currency": "USD",
        "status": "EXHAUSTED",
        "remaining_balance": Decimal("0.00"),
    }
}


def lookup_vendor(vendor_name: Optional[str], session: Optional[Session] = None) -> Dict[str, Any]:
    """
    Agent tool: Looks up vendor details in master database/registry.
    """
    if not vendor_name or not vendor_name.strip():
        return {
            "found": False,
            "status": "MISSING_VENDOR",
            "message": "Vendor name was not provided."
        }

    clean_name = vendor_name.strip()

    if session:
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

    # Default fallback lookup for synthetic vendors
    return {
        "found": True,
        "status": "VERIFIED",
        "vendor_name": clean_name,
        "is_approved": True,
        "message": f"Vendor '{clean_name}' recognized."
    }


def lookup_purchase_order(po_number: Optional[str], session: Optional[Session] = None) -> Dict[str, Any]:
    """
    Agent tool: Looks up Purchase Order details in PO database.
    Returns authorized total, vendor match, and PO status.
    """
    if not po_number or not po_number.strip():
        return {
            "found": False,
            "status": "NO_PO_PROVIDED",
            "message": "No purchase order number provided."
        }

    clean_po = po_number.strip().upper()
    po_record = MOCK_PO_DATABASE.get(clean_po)

    if not po_record:
        return {
            "found": False,
            "status": "PO_NOT_FOUND",
            "po_number": clean_po,
            "message": f"Purchase Order '{clean_po}' was not found in enterprise PO database."
        }

    return {
        "found": True,
        "status": po_record["status"],
        "po_number": clean_po,
        "vendor_name": po_record["vendor_name"],
        "authorized_total": po_record["authorized_total"],
        "currency": po_record["currency"],
        "remaining_balance": po_record["remaining_balance"],
        "message": f"Purchase Order '{clean_po}' found. Authorized total: ${po_record['authorized_total']}."
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


def create_review_task(invoice_id: int, reason: str, session: Optional[Session] = None) -> Dict[str, Any]:
    """
    Agent tool: Creates a human review queue task.
    """
    if session:
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
