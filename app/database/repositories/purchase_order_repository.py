from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, joinedload

from app.database.models import PurchaseOrderModel, PurchaseOrderLineItemModel, VendorModel


class PurchaseOrderRepository:
    """
    Data Access Repository for querying and managing Purchase Orders in enterprise database.
    """

    def get_by_po_number(self, session: Session, po_number: str, vendor_id: Optional[int] = None) -> Optional[PurchaseOrderModel]:
        """
        Retrieves Purchase Order by po_number, eagerly loading vendor and line items.
        Optionally filters by vendor_id.
        """
        if not po_number or not po_number.strip():
            return None

        clean_po = po_number.strip().upper()
        query = session.query(PurchaseOrderModel).options(
            joinedload(PurchaseOrderModel.vendor),
            joinedload(PurchaseOrderModel.line_items)
        ).filter(PurchaseOrderModel.po_number == clean_po)

        if vendor_id is not None:
            query = query.filter(PurchaseOrderModel.vendor_id == vendor_id)

        return query.first()

    def get_by_id(self, session: Session, po_id: int) -> Optional[PurchaseOrderModel]:
        """Retrieves Purchase Order by primary key ID."""
        return session.query(PurchaseOrderModel).options(
            joinedload(PurchaseOrderModel.vendor),
            joinedload(PurchaseOrderModel.line_items)
        ).filter(PurchaseOrderModel.id == po_id).first()

    def create(
        self,
        session: Session,
        po_data: Dict[str, Any],
        line_items_data: Optional[List[Dict[str, Any]]] = None
    ) -> PurchaseOrderModel:
        """
        Creates a new Purchase Order record with optional line items.
        """
        po = PurchaseOrderModel(
            po_number=po_data["po_number"].strip().upper(),
            vendor_id=po_data["vendor_id"],
            po_date=po_data.get("po_date"),
            currency=po_data.get("currency", "USD"),
            subtotal=Decimal(str(po_data.get("subtotal", 0.0))),
            discount=Decimal(str(po_data.get("discount", 0.0))),
            tax_amount=Decimal(str(po_data.get("tax_amount", 0.0))),
            total_amount=Decimal(str(po_data.get("total_amount", po_data["authorized_total"]))),
            authorized_total=Decimal(str(po_data["authorized_total"])),
            remaining_balance=Decimal(str(po_data.get("remaining_balance", po_data["authorized_total"]))),
            status=po_data.get("status", "APPROVED")
        )
        session.add(po)
        session.flush()

        if line_items_data:
            for item in line_items_data:
                li = PurchaseOrderLineItemModel(
                    purchase_order_id=po.id,
                    description=item.get("description", "Item"),
                    product_code=item.get("product_code"),
                    quantity=Decimal(str(item.get("quantity", 1.0))),
                    unit=item.get("unit", "units"),
                    unit_price=Decimal(str(item.get("unit_price", 0.0))),
                    discount=Decimal(str(item.get("discount", 0.0))),
                    tax_rate=Decimal(str(item.get("tax_rate", 0.0))),
                    tax_amount=Decimal(str(item.get("tax_amount", 0.0))),
                    line_total=Decimal(str(item.get("line_total", 0.0)))
                )
                session.add(li)
            session.flush()

        return po

    def list(self, session: Session, vendor_id: Optional[int] = None, status: Optional[str] = None) -> List[PurchaseOrderModel]:
        """Lists all purchase orders with optional filtering."""
        query = session.query(PurchaseOrderModel).options(
            joinedload(PurchaseOrderModel.vendor)
        )
        if vendor_id is not None:
            query = query.filter(PurchaseOrderModel.vendor_id == vendor_id)
        if status:
            query = query.filter(PurchaseOrderModel.status == status)

        return query.order_by(PurchaseOrderModel.created_at.desc()).all()
