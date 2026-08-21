import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repositories.invoice_repository import InvoiceRepository
from app.schemas.processing import ProcessingResult
from app.services.pipeline_runner import InvoicePipelineRunner

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post("/process", response_model=ProcessingResult, status_code=status.HTTP_201_CREATED)
def process_invoice_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload an invoice PDF file for extraction, validation, agent reasoning, and database persistence.
    """
    if not file.filename.lower().endswith((".pdf", ".png", ".jpg", ".jpeg", ".tiff")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a PDF or image file."
        )

    # Save uploaded file bytes to temporary file for pipeline processing
    try:
        content = file.file.read()
        runner = InvoicePipelineRunner()
        result = runner.process_file(file_input=content, file_name=file.filename, db_session=db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing invoice document: {str(e)}"
        )


@router.get("", response_model=List[Dict[str, Any]])
def list_invoices(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: PENDING, APPROVED, REJECTED, NEEDS_REVIEW"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retrieve paginated list of processed invoice records.
    """
    repo = InvoiceRepository()
    invoices = repo.list_invoices(session=db, status=status_filter, limit=limit, offset=offset)

    results = []
    for inv in invoices:
        results.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "vendor_name": inv.vendor.name if inv.vendor else None,
            "customer_name": inv.customer.name if inv.customer else None,
            "invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
            "due_date": str(inv.due_date) if inv.due_date else None,
            "currency": inv.currency,
            "total_amount": float(inv.total_amount) if inv.total_amount is not None else None,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None
        })
    return results


@router.get("/{invoice_id}", response_model=Dict[str, Any])
def get_invoice_detail(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve detailed invoice record by primary key ID, including line items.
    """
    repo = InvoiceRepository()
    inv = repo.get_by_id(session=db, invoice_id=invoice_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice #{invoice_id} not found."
        )

    line_items_data = [
        {
            "id": item.id,
            "description": item.description,
            "product_code": item.product_code,
            "quantity": float(item.quantity),
            "unit_price": float(item.unit_price),
            "line_total": float(item.line_total)
        }
        for item in inv.line_items
    ]

    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "po_number": inv.po_number,
        "invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
        "due_date": str(inv.due_date) if inv.due_date else None,
        "currency": inv.currency,
        "subtotal": float(inv.subtotal) if inv.subtotal is not None else None,
        "tax_amount": float(inv.tax_amount) if inv.tax_amount is not None else None,
        "total_amount": float(inv.total_amount) if inv.total_amount is not None else None,
        "amount_due": float(inv.amount_due) if inv.amount_due is not None else None,
        "status": inv.status,
        "source_filename": inv.source_filename,
        "vendor": {
            "name": inv.vendor.name,
            "email": inv.vendor.email,
            "tax_id": inv.vendor.tax_id
        } if inv.vendor else None,
        "customer": {
            "name": inv.customer.name,
            "email": inv.customer.email
        } if inv.customer else None,
        "line_items": line_items_data,
        "created_at": inv.created_at.isoformat() if inv.created_at else None
    }


@router.get("/{invoice_id}/validation", response_model=List[Dict[str, Any]])
def get_invoice_validation_history(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve validation rule execution history for an invoice.
    """
    repo = InvoiceRepository()
    inv = repo.get_by_id(session=db, invoice_id=invoice_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice #{invoice_id} not found."
        )

    records = []
    for rec in inv.validation_records:
        records.append({
            "id": rec.id,
            "is_valid": rec.is_valid,
            "errors": json.loads(rec.errors_json) if rec.errors_json else [],
            "warnings": json.loads(rec.warnings_json) if rec.warnings_json else [],
            "checked_at": rec.checked_at.isoformat() if rec.checked_at else None
        })
    return records
