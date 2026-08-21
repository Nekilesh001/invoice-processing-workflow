from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import InvoiceModel, ReviewTaskModel

router = APIRouter(prefix="/reviews", tags=["Human Review Tasks"])


@router.get("", response_model=List[Dict[str, Any]])
def list_review_tasks(
    status_filter: Optional[str] = Query("PENDING", alias="status", description="Filter tasks by status: PENDING, APPROVED, REJECTED"),
    db: Session = Depends(get_db)
):
    """
    Retrieve human-in-the-loop review tasks.
    """
    query = db.query(ReviewTaskModel)
    if status_filter:
        query = query.filter(ReviewTaskModel.status == status_filter)

    tasks = query.order_by(ReviewTaskModel.created_at.desc()).all()
    results = []
    for t in tasks:
        inv = t.invoice
        line_items = []
        if inv and inv.line_items:
            for item in inv.line_items:
                line_items.append({
                    "id": item.id,
                    "description": item.description,
                    "quantity": float(item.quantity) if item.quantity is not None else 0.0,
                    "unit_price": float(item.unit_price) if item.unit_price is not None else 0.0,
                    "line_total": float(item.line_total) if item.line_total is not None else 0.0
                })

        val_records = []
        if inv and inv.validation_records:
            for rec in inv.validation_records:
                import json
                val_records.append({
                    "is_valid": rec.is_valid,
                    "errors": json.loads(rec.errors_json) if rec.errors_json else [],
                    "warnings": json.loads(rec.warnings_json) if rec.warnings_json else []
                })

        raw_json_data = {
            "invoice_number": inv.invoice_number if inv else None,
            "po_number": inv.po_number if inv else None,
            "invoice_date": str(inv.invoice_date) if (inv and inv.invoice_date) else None,
            "due_date": str(inv.due_date) if (inv and inv.due_date) else None,
            "currency": inv.currency if inv else "USD",
            "vendor_name": inv.vendor.name if (inv and inv.vendor) else None,
            "customer_name": inv.customer.name if (inv and inv.customer) else None,
            "subtotal": float(inv.subtotal) if (inv and inv.subtotal is not None) else None,
            "tax_amount": float(inv.tax_amount) if (inv and inv.tax_amount is not None) else None,
            "total_amount": float(inv.total_amount) if (inv and inv.total_amount is not None) else None,
            "line_items": line_items,
            "flagged_reason": t.reason
        }

        results.append({
            "id": t.id,
            "invoice_id": t.invoice_id,
            "reason": t.reason,
            "status": t.status,
            "assigned_to": t.assigned_to,
            "invoice_number": inv.invoice_number if inv else "N/A",
            "po_number": inv.po_number if inv else None,
            "vendor_name": inv.vendor.name if (inv and inv.vendor) else "Unassigned Vendor",
            "customer_name": inv.customer.name if (inv and inv.customer) else "Unassigned Customer",
            "invoice_date": str(inv.invoice_date) if (inv and inv.invoice_date) else None,
            "due_date": str(inv.due_date) if (inv and inv.due_date) else None,
            "currency": inv.currency if inv else "USD",
            "subtotal": float(inv.subtotal) if (inv and inv.subtotal is not None) else 0.0,
            "tax_amount": float(inv.tax_amount) if (inv and inv.tax_amount is not None) else 0.0,
            "total_amount": float(inv.total_amount) if (inv and inv.total_amount is not None) else 0.0,
            "line_items": line_items,
            "validation_records": val_records,
            "raw_json": raw_json_data,
            "created_at": t.created_at.isoformat() if t.created_at else None
        })
    return results


@router.post("/{task_id}/approve", response_model=Dict[str, Any])
def approve_review_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Human Reviewer manual approval: updates review task status to APPROVED and sets invoice status to APPROVED.
    """
    task = db.query(ReviewTaskModel).filter(ReviewTaskModel.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review task #{task_id} not found."
        )

    task.status = "APPROVED"
    if task.invoice:
        task.invoice.status = "APPROVED"

    db.commit()
    return {
        "task_id": task.id,
        "invoice_id": task.invoice_id,
        "status": "APPROVED",
        "message": f"Review task #{task_id} approved. Invoice #{task.invoice_id} status updated to APPROVED."
    }


@router.post("/{task_id}/reject", response_model=Dict[str, Any])
def reject_review_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Human Reviewer manual rejection: updates review task status to REJECTED and sets invoice status to REJECTED.
    """
    task = db.query(ReviewTaskModel).filter(ReviewTaskModel.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review task #{task_id} not found."
        )

    task.status = "REJECTED"
    if task.invoice:
        task.invoice.status = "REJECTED"

    db.commit()
    return {
        "task_id": task.id,
        "invoice_id": task.invoice_id,
        "status": "REJECTED",
        "message": f"Review task #{task_id} rejected. Invoice #{task.invoice_id} status updated to REJECTED."
    }
