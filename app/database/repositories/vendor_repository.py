from typing import Any, Dict, List, Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.database.models import VendorModel, PurchaseOrderModel, InvoiceModel


class VendorRepository:
    """
    Data Access Repository for master Vendors registry in MySQL database.
    """

    def get_by_id(self, session: Session, vendor_id: int) -> Optional[VendorModel]:
        """Retrieves master Vendor record by primary key ID with related POs and invoices."""
        return session.query(VendorModel).options(
            joinedload(VendorModel.purchase_orders),
            joinedload(VendorModel.invoices)
        ).filter(VendorModel.id == vendor_id).first()

    def get_by_name(self, session: Session, name: str) -> Optional[VendorModel]:
        """Retrieves master Vendor record by exact name."""
        if not name:
            return None
        return session.query(VendorModel).filter(
            func.lower(VendorModel.name) == name.strip().lower()
        ).first()

    def list_vendors(
        self,
        session: Session,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Lists master vendors with search filtering and aggregated counts for POs and Invoices.
        Avoids N+1 queries using SQL subqueries.
        """
        # Subquery for Purchase Order counts per vendor
        po_counts_sub = session.query(
            PurchaseOrderModel.vendor_id,
            func.count(PurchaseOrderModel.id).label("po_count")
        ).group_by(PurchaseOrderModel.vendor_id).subquery()

        # Subquery for Invoice counts per vendor
        inv_counts_sub = session.query(
            InvoiceModel.vendor_id,
            func.count(InvoiceModel.id).label("inv_count")
        ).group_by(InvoiceModel.vendor_id).subquery()

        query = session.query(
            VendorModel,
            func.coalesce(po_counts_sub.c.po_count, 0).label("po_count"),
            func.coalesce(inv_counts_sub.c.inv_count, 0).label("inv_count")
        ).outerjoin(
            po_counts_sub, VendorModel.id == po_counts_sub.c.vendor_id
        ).outerjoin(
            inv_counts_sub, VendorModel.id == inv_counts_sub.c.vendor_id
        )

        if search and search.strip():
            clean_search = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(VendorModel.name).like(clean_search),
                    func.lower(VendorModel.tax_id).like(clean_search),
                    func.lower(VendorModel.registration_number).like(clean_search)
                )
            )

        results = query.order_by(VendorModel.created_at.desc()).limit(limit).offset(offset).all()

        vendor_list = []
        for vendor, po_count, inv_count in results:
            vendor_list.append({
                "id": vendor.id,
                "name": vendor.name,
                "address": vendor.address,
                "email": vendor.email,
                "phone": vendor.phone,
                "tax_id": vendor.tax_id,
                "registration_number": vendor.registration_number,
                "is_approved": True,  # Vendors in master registry are approved
                "purchase_order_count": int(po_count),
                "invoice_count": int(inv_count),
                "created_at": vendor.created_at.isoformat() if vendor.created_at else None
            })

        return vendor_list
