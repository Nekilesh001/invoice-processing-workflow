import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database.models import (
    InvoiceModel,
    VendorModel,
    PurchaseOrderModel,
    ReviewTaskModel,
    ReviewActionModel,
)

logger = logging.getLogger(__name__)


def get_invoice_summary(session: Session) -> Dict[str, Any]:
    """Analyst Tool: Returns global invoice counts and financial monetary totals."""
    total_count = session.query(InvoiceModel).count()
    approved_count = session.query(InvoiceModel).filter(InvoiceModel.status == "APPROVED").count()
    review_count = session.query(InvoiceModel).filter(InvoiceModel.status == "NEEDS_REVIEW").count()
    rejected_count = session.query(InvoiceModel).filter(InvoiceModel.status == "REJECTED").count()
    pending_count = session.query(InvoiceModel).filter(InvoiceModel.status == "PENDING").count()

    sum_total = session.query(func.sum(InvoiceModel.total_amount)).scalar() or 0.0
    sum_due = session.query(func.sum(InvoiceModel.amount_due)).scalar() or 0.0

    return {
        "total_invoices": total_count,
        "approved_invoices": approved_count,
        "needs_review_invoices": review_count,
        "rejected_invoices": rejected_count,
        "pending_invoices": pending_count,
        "total_monetary_amount": float(sum_total),
        "total_amount_due": float(sum_due)
    }


def get_financial_summary(session: Session) -> Dict[str, Any]:
    """Analyst Tool: Returns high-level financial spend metrics."""
    total_spend = session.query(func.sum(InvoiceModel.total_amount)).scalar() or 0.0
    approved_spend = session.query(func.sum(InvoiceModel.total_amount)).filter(InvoiceModel.status == "APPROVED").scalar() or 0.0
    rejected_spend = session.query(func.sum(InvoiceModel.total_amount)).filter(InvoiceModel.status == "REJECTED").scalar() or 0.0
    review_spend = session.query(func.sum(InvoiceModel.total_amount)).filter(InvoiceModel.status == "NEEDS_REVIEW").scalar() or 0.0

    return {
        "total_financial_volume": float(total_spend),
        "approved_volume": float(approved_spend),
        "rejected_volume": float(rejected_spend),
        "needs_review_volume": float(review_spend)
    }


def get_vendor_invoice_summary(session: Session) -> List[Dict[str, Any]]:
    """Analyst Tool: Ranks vendors by total invoice volume and amount."""
    results = (
        session.query(
            VendorModel.name,
            func.count(InvoiceModel.id).label("invoice_count"),
            func.coalesce(func.sum(InvoiceModel.total_amount), 0).label("total_val")
        )
        .join(InvoiceModel, VendorModel.id == InvoiceModel.vendor_id)
        .group_by(VendorModel.id, VendorModel.name)
        .order_by(desc("total_val"))
        .all()
    )

    summary = []
    for r in results:
        summary.append({
            "vendor_name": r.name,
            "invoice_count": r.invoice_count,
            "total_invoice_value": float(r.total_val)
        })
    return summary


def get_purchase_order_summary(session: Session) -> Dict[str, Any]:
    """Analyst Tool: Returns PO master metrics and balance statistics."""
    total_pos = session.query(PurchaseOrderModel).count()
    approved_pos = session.query(PurchaseOrderModel).filter(PurchaseOrderModel.status == "APPROVED").count()
    exhausted_pos = session.query(PurchaseOrderModel).filter(PurchaseOrderModel.status == "EXHAUSTED").count()
    total_auth = session.query(func.sum(PurchaseOrderModel.authorized_total)).scalar() or 0.0
    total_rem = session.query(func.sum(PurchaseOrderModel.remaining_balance)).scalar() or 0.0

    return {
        "total_purchase_orders": total_pos,
        "approved_pos": approved_pos,
        "exhausted_pos": exhausted_pos,
        "total_authorized_amount": float(total_auth),
        "total_remaining_balance": float(total_rem)
    }


def get_review_queue_summary(session: Session) -> Dict[str, Any]:
    """Analyst Tool: Returns human review task queue statistics."""
    pending_tasks = session.query(ReviewTaskModel).filter(ReviewTaskModel.status == "PENDING").all()
    completed_tasks = session.query(ReviewTaskModel).filter(ReviewTaskModel.status != "PENDING").count()

    reasons = {}
    for task in pending_tasks:
        reason = task.reason or "UNKNOWN"
        reasons[reason] = reasons.get(reason, 0) + 1

    return {
        "pending_review_tasks_count": len(pending_tasks),
        "completed_review_tasks_count": completed_tasks,
        "reasons_breakdown": reasons
    }


def get_invoice_exceptions(session: Session) -> List[Dict[str, Any]]:
    """Analyst Tool: Returns list of active exception invoices requiring human review."""
    invoices = session.query(InvoiceModel).filter(InvoiceModel.status == "NEEDS_REVIEW").all()
    exceptions = []
    for inv in invoices:
        exceptions.append({
            "invoice_id": inv.id,
            "invoice_number": inv.invoice_number,
            "vendor_name": inv.vendor.name if inv.vendor else "Unknown",
            "total_amount": float(inv.total_amount) if inv.total_amount is not None else 0.0,
            "po_number": inv.po_number,
            "status": inv.status
        })
    return exceptions
