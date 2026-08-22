from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repositories.purchase_order_repository import PurchaseOrderRepository

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


@router.get("", response_model=List[Dict[str, Any]])
def list_purchase_orders(
    search: Optional[str] = Query(None, description="Search by PO number or vendor name"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: APPROVED, EXHAUSTED, CANCELLED, DRAFT"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retrieve paginated list of enterprise Purchase Orders with search and status filtering.
    """
    repo = PurchaseOrderRepository()
    pos = repo.list(session=db, vendor_id=vendor_id, status=status_filter, search=search, limit=limit, offset=offset)

    results = []
    for po in pos:
        results.append({
            "id": po.id,
            "po_number": po.po_number,
            "vendor_id": po.vendor_id,
            "vendor_name": po.vendor.name if po.vendor else "Unknown",
            "po_date": str(po.po_date) if po.po_date else None,
            "currency": po.currency,
            "subtotal": float(po.subtotal) if po.subtotal is not None else None,
            "discount": float(po.discount) if po.discount is not None else 0.0,
            "tax_amount": float(po.tax_amount) if po.tax_amount is not None else 0.0,
            "total_amount": float(po.total_amount) if po.total_amount is not None else float(po.authorized_total),
            "authorized_total": float(po.authorized_total),
            "remaining_balance": float(po.remaining_balance),
            "status": po.status,
            "created_at": po.created_at.isoformat() if po.created_at else None
        })
    return results


@router.get("/{po_id}", response_model=Dict[str, Any])
def get_purchase_order_detail(
    po_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve detailed Purchase Order record by primary key ID, including line items and related invoices.
    """
    repo = PurchaseOrderRepository()
    po = repo.get_by_id(session=db, po_id=po_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order #{po_id} not found."
        )

    line_items_data = [
        {
            "id": item.id,
            "description": item.description,
            "product_code": item.product_code,
            "quantity": float(item.quantity),
            "unit": item.unit,
            "unit_price": float(item.unit_price),
            "discount": float(item.discount) if item.discount else 0.0,
            "tax_rate": float(item.tax_rate) if item.tax_rate else 0.0,
            "tax_amount": float(item.tax_amount) if item.tax_amount else 0.0,
            "line_total": float(item.line_total)
        }
        for item in po.line_items
    ]

    related_invoices = repo.get_related_invoices(session=db, po=po)
    invoices_data = [
        {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
            "currency": inv.currency,
            "total_amount": float(inv.total_amount) if inv.total_amount is not None else None,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None
        }
        for inv in related_invoices
    ]

    return {
        "id": po.id,
        "po_number": po.po_number,
        "vendor_id": po.vendor_id,
        "vendor": {
            "id": po.vendor.id,
            "name": po.vendor.name,
            "email": po.vendor.email,
            "tax_id": po.vendor.tax_id
        } if po.vendor else None,
        "po_date": str(po.po_date) if po.po_date else None,
        "currency": po.currency,
        "subtotal": float(po.subtotal) if po.subtotal is not None else None,
        "discount": float(po.discount) if po.discount is not None else 0.0,
        "tax_amount": float(po.tax_amount) if po.tax_amount is not None else 0.0,
        "total_amount": float(po.total_amount) if po.total_amount is not None else float(po.authorized_total),
        "authorized_total": float(po.authorized_total),
        "remaining_balance": float(po.remaining_balance),
        "status": po.status,
        "line_items": line_items_data,
        "related_invoices": invoices_data,
        "created_at": po.created_at.isoformat() if po.created_at else None
    }
