from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repositories.vendor_repository import VendorRepository

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.get("", response_model=List[Dict[str, Any]])
def list_vendors(
    search: Optional[str] = Query(None, description="Search by vendor name, tax ID, or registration number"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retrieve master vendor registry with search filtering and aggregated PO/invoice counts.
    """
    repo = VendorRepository()
    return repo.list_vendors(session=db, search=search, limit=limit, offset=offset)


@router.get("/{vendor_id}", response_model=Dict[str, Any])
def get_vendor_detail(
    vendor_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve detailed master vendor record by primary key ID, including purchase orders and invoices.
    """
    repo = VendorRepository()
    vendor = repo.get_by_id(session=db, vendor_id=vendor_id)
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor #{vendor_id} not found."
        )

    pos_data = [
        {
            "id": po.id,
            "po_number": po.po_number,
            "po_date": str(po.po_date) if po.po_date else None,
            "currency": po.currency,
            "authorized_total": float(po.authorized_total),
            "remaining_balance": float(po.remaining_balance),
            "status": po.status,
            "created_at": po.created_at.isoformat() if po.created_at else None
        }
        for po in vendor.purchase_orders
    ]

    invoices_data = [
        {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "po_number": inv.po_number,
            "invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
            "currency": inv.currency,
            "total_amount": float(inv.total_amount) if inv.total_amount is not None else None,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None
        }
        for inv in vendor.invoices
    ]

    return {
        "id": vendor.id,
        "name": vendor.name,
        "address": vendor.address,
        "email": vendor.email,
        "phone": vendor.phone,
        "tax_id": vendor.tax_id,
        "registration_number": vendor.registration_number,
        "is_approved": True,
        "purchase_orders": pos_data,
        "invoices": invoices_data,
        "created_at": vendor.created_at.isoformat() if vendor.created_at else None
    }
