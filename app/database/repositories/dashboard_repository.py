from typing import Any, Dict, List
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.database.models import (
    InvoiceModel,
    ReviewTaskModel,
    ReviewActionModel,
    VendorModel
)


class DashboardRepository:
    """
    Data Access Repository executing SQL aggregate queries for executive Invoice Operations Dashboard.
    Uses pure SQL aggregates (COUNT, SUM, GROUP BY) to ensure 100% data accuracy from MySQL.
    """

    def get_summary(self, session: Session) -> Dict[str, Any]:
        """
        Executes SQL aggregate calculations and fetches recent activity lists.
        """
        # 1. Invoice Status Counts
        total_count = session.query(func.count(InvoiceModel.id)).scalar() or 0
        approved_count = session.query(func.count(InvoiceModel.id)).filter(InvoiceModel.status == "APPROVED").scalar() or 0
        review_count = session.query(func.count(InvoiceModel.id)).filter(
            InvoiceModel.status.in_(["NEEDS_REVIEW", "PENDING"])
        ).scalar() or 0
        rejected_count = session.query(func.count(InvoiceModel.id)).filter(InvoiceModel.status == "REJECTED").scalar() or 0
        processing_count = session.query(func.count(InvoiceModel.id)).filter(InvoiceModel.status == "PROCESSING").scalar() or 0

        # 2. Financial Value Aggregations (using InvoiceModel.total_amount)
        total_val = float(session.query(func.coalesce(func.sum(InvoiceModel.total_amount), 0.0)).scalar() or 0.0)
        approved_val = float(session.query(func.coalesce(func.sum(InvoiceModel.total_amount), 0.0)).filter(
            InvoiceModel.status == "APPROVED"
        ).scalar() or 0.0)
        review_val = float(session.query(func.coalesce(func.sum(InvoiceModel.total_amount), 0.0)).filter(
            InvoiceModel.status.in_(["NEEDS_REVIEW", "PENDING"])
        ).scalar() or 0.0)
        rejected_val = float(session.query(func.coalesce(func.sum(InvoiceModel.total_amount), 0.0)).filter(
            InvoiceModel.status == "REJECTED"
        ).scalar() or 0.0)

        # 3. Review Queue Metrics
        pending_review_tasks = session.query(func.count(ReviewTaskModel.id)).filter(
            ReviewTaskModel.status == "PENDING"
        ).scalar() or 0

        # 4. Verification Issue Aggregation (grouped by review task reason)
        issue_rows = session.query(
            ReviewTaskModel.reason,
            func.count(ReviewTaskModel.id).label("reason_count")
        ).group_by(ReviewTaskModel.reason).order_by(func.count(ReviewTaskModel.id).desc()).all()

        verification_issues = [
            {"reason": reason, "count": int(cnt)}
            for reason, cnt in issue_rows
        ]

        # 5. Top 10 Recent Invoices
        recent_inv_objs = session.query(InvoiceModel).options(
            joinedload(InvoiceModel.vendor)
        ).order_by(InvoiceModel.created_at.desc(), InvoiceModel.id.desc()).limit(10).all()

        recent_invoices = []
        for inv in recent_inv_objs:
            recent_invoices.append({
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "vendor_name": inv.vendor.name if inv.vendor else "Unknown Vendor",
                "total_amount": float(inv.total_amount) if inv.total_amount is not None else 0.0,
                "po_number": inv.po_number,
                "status": inv.status,
                "created_at": inv.created_at.isoformat() if inv.created_at else None
            })

        # 6. Top 10 Recent Human Review Activity Logs
        recent_act_objs = session.query(ReviewActionModel).options(
            joinedload(ReviewActionModel.invoice)
        ).order_by(ReviewActionModel.created_at.desc(), ReviewActionModel.id.desc()).limit(10).all()

        recent_reviews = []
        for act in recent_act_objs:
            recent_reviews.append({
                "id": act.id,
                "invoice_id": act.invoice_id,
                "invoice_number": act.invoice.invoice_number if act.invoice else f"Invoice #{act.invoice_id}",
                "action": act.action,
                "reviewer": act.reviewer_name,
                "comment": act.comment,
                "created_at": act.created_at.isoformat() if act.created_at else None
            })

        return {
            "invoice_counts": {
                "total": total_count,
                "approved": approved_count,
                "human_review": review_count,
                "rejected": rejected_count,
                "processing": processing_count
            },
            "financial_totals": {
                "total_invoice_value": total_val,
                "approved_value": approved_val,
                "review_value": review_val,
                "rejected_value": rejected_val
            },
            "review_metrics": {
                "pending_count": pending_review_tasks
            },
            "verification_issues": verification_issues,
            "recent_invoices": recent_invoices,
            "recent_reviews": recent_reviews
        }
