from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional
from app.database.connection import get_db
from app.database.models import InvoiceModel, ReviewTaskModel, ReviewActionModel, UserModel
from app.schemas.review import ReviewActionRequest, ReviewActionResponse

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
            "vendor_name": inv.vendor.name if (inv and inv.vendor) else None,
            "customer_name": inv.customer.name if (inv and inv.customer) else None,
            "total_amount": float(inv.total_amount) if (inv and inv.total_amount is not None) else 0.0,
            "line_items": line_items,
            "validation": val_records[0] if val_records else None
        }

        results.append({
            "task_id": t.id,
            "invoice_id": t.invoice_id,
            "reason": t.reason,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "invoice_number": inv.invoice_number if inv else None,
            "invoice_date": str(inv.invoice_date) if (inv and inv.invoice_date) else None,
            "due_date": str(inv.due_date) if (inv and inv.due_date) else None,
            "vendor_name": inv.vendor.name if (inv and inv.vendor) else "Unknown",
            "total_amount": float(inv.total_amount) if (inv and inv.total_amount is not None) else 0.0,
            "po_number": inv.po_number if inv else None,
            "raw_json": raw_json_data
        })
    return results


@router.post("/{task_id}/approve", response_model=Dict[str, Any])
def approve_review_task(
    task_id: int,
    payload: Optional[ReviewActionRequest] = None,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Human Reviewer manual approval: updates task & invoice status to APPROVED, and records review decision history.
    """
    task = db.query(ReviewTaskModel).filter(ReviewTaskModel.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review task #{task_id} not found."
        )

    if task.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Review task #{task_id} has already been closed with status {task.status}."
        )

    if current_user and current_user.role == "VIEWER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden. VIEWER role is not authorized to approve invoices."
        )

    reviewer_name = current_user.full_name or current_user.username if current_user else (payload.reviewer if (payload and payload.reviewer) else "Finance Reviewer")
    reviewer_id = current_user.id if current_user else None
    comment = payload.get_effective_comment() if payload else None

    previous_status = task.invoice.status if task.invoice else "NEEDS_REVIEW"
    new_status = "APPROVED"

    task.status = "APPROVED"
    if task.invoice:
        task.invoice.status = new_status

    action_record = ReviewActionModel(
        review_task_id=task.id,
        invoice_id=task.invoice_id,
        action="APPROVED",
        previous_invoice_status=previous_status,
        new_invoice_status=new_status,
        reviewer_id=reviewer_id,
        reviewer_name=reviewer_name,
        comment=comment
    )
    db.add(action_record)
    db.commit()

    return {
        "task_id": task.id,
        "invoice_id": task.invoice_id,
        "status": "APPROVED",
        "action": "APPROVED",
        "reviewer": reviewer_name,
        "comment": comment,
        "message": f"Review task #{task_id} approved. Invoice #{task.invoice_id} status updated to APPROVED."
    }


@router.post("/{task_id}/reject", response_model=Dict[str, Any])
def reject_review_task(
    task_id: int,
    payload: Optional[ReviewActionRequest] = None,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Human Reviewer manual rejection: requires mandatory comment, transactionally updates task & invoice status to REJECTED, and records review decision history.
    """
    task = db.query(ReviewTaskModel).filter(ReviewTaskModel.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review task #{task_id} not found."
        )

    if task.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Review task #{task_id} has already been closed with status {task.status}."
        )

    if current_user and current_user.role == "VIEWER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden. VIEWER role is not authorized to reject invoices."
        )

    comment = payload.get_effective_comment() if payload else None
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reviewer comment is required when rejecting an invoice."
        )

    reviewer_name = current_user.full_name or current_user.username if current_user else (payload.reviewer if (payload and payload.reviewer) else "Finance Reviewer")
    reviewer_id = current_user.id if current_user else None
    previous_status = task.invoice.status if task.invoice else "NEEDS_REVIEW"
    new_status = "REJECTED"

    task.status = "REJECTED"
    if task.invoice:
        task.invoice.status = new_status

    action_record = ReviewActionModel(
        review_task_id=task.id,
        invoice_id=task.invoice_id,
        action="REJECTED",
        previous_invoice_status=previous_status,
        new_invoice_status=new_status,
        reviewer_id=reviewer_id,
        reviewer_name=reviewer_name,
        comment=comment
    )
    db.add(action_record)
    db.commit()

    return {
        "task_id": task.id,
        "invoice_id": task.invoice_id,
        "status": "REJECTED",
        "action": "REJECTED",
        "reviewer": reviewer_name,
        "comment": comment,
        "message": f"Review task #{task_id} rejected. Invoice #{task.invoice_id} status updated to REJECTED."
    }
