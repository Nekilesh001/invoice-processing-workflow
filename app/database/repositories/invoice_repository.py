import json
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.database.models import (
    VendorModel,
    CustomerModel,
    InvoiceModel,
    InvoiceLineItemModel,
    ValidationRecordModel,
    ReviewTaskModel
)
from app.schemas.invoice import ExtractedInvoice
from app.schemas.processing import ValidationResult


class InvoiceRepository:
    """
    Data Access Repository for storing and querying invoices, vendors, line items, and validation history.
    """

    def get_or_create_vendor(self, session: Session, vendor_name: str, **kwargs) -> VendorModel:
        """Finds vendor by name or creates a new master vendor record."""
        vendor = session.query(VendorModel).filter(VendorModel.name == vendor_name.strip()).first()
        if not vendor:
            vendor = VendorModel(
                name=vendor_name.strip(),
                address=kwargs.get("address"),
                email=kwargs.get("email"),
                phone=kwargs.get("phone"),
                tax_id=kwargs.get("tax_id"),
                registration_number=kwargs.get("registration_number")
            )
            session.add(vendor)
            session.flush()
        return vendor

    def get_or_create_customer(self, session: Session, customer_name: str, **kwargs) -> CustomerModel:
        """Finds customer by name or creates a new master customer record."""
        customer = session.query(CustomerModel).filter(CustomerModel.name == customer_name.strip()).first()
        if not customer:
            customer = CustomerModel(
                name=customer_name.strip(),
                address=kwargs.get("address"),
                email=kwargs.get("email"),
                phone=kwargs.get("phone"),
                tax_id=kwargs.get("tax_id")
            )
            session.add(customer)
            session.flush()
        return customer

    def check_duplicate(self, session: Session, vendor_name: Optional[str], invoice_number: Optional[str]) -> bool:
        """
        Checks if an invoice with identical vendor_name and invoice_number already exists.
        Returns True if a duplicate match is found.
        """
        if not vendor_name or not invoice_number:
            return False

        vendor = session.query(VendorModel).filter(VendorModel.name == vendor_name.strip()).first()
        if not vendor:
            return False

        existing = session.query(InvoiceModel).filter(
            InvoiceModel.vendor_id == vendor.id,
            InvoiceModel.invoice_number == invoice_number.strip()
        ).first()

        return existing is not None

    def save_invoice(
        self,
        session: Session,
        extracted_invoice: ExtractedInvoice,
        validation_result: Optional[ValidationResult] = None,
        source_filename: Optional[str] = None
    ) -> InvoiceModel:
        """
        Persists ExtractedInvoice model to database within active transaction.
        Handles vendor/customer linking, line items creation, and validation history insertion.
        """
        vendor_inst = None
        if extracted_invoice.vendor and extracted_invoice.vendor.vendor_name:
            vendor_inst = self.get_or_create_vendor(
                session,
                extracted_invoice.vendor.vendor_name,
                address=extracted_invoice.vendor.vendor_address,
                email=extracted_invoice.vendor.vendor_email,
                phone=extracted_invoice.vendor.vendor_phone,
                tax_id=extracted_invoice.vendor.vendor_tax_id,
                registration_number=extracted_invoice.vendor.vendor_registration_number
            )

        customer_inst = None
        if extracted_invoice.customer and extracted_invoice.customer.customer_name:
            customer_inst = self.get_or_create_customer(
                session,
                extracted_invoice.customer.customer_name,
                address=extracted_invoice.customer.customer_address,
                email=extracted_invoice.customer.customer_email,
                phone=extracted_invoice.customer.customer_phone,
                tax_id=extracted_invoice.customer.customer_tax_id
            )

        status = "PENDING"
        if validation_result:
            status = "APPROVED" if validation_result.is_valid else "NEEDS_REVIEW"

        invoice_rec = InvoiceModel(
            invoice_number=extracted_invoice.invoice_number,
            vendor_id=vendor_inst.id if vendor_inst else None,
            customer_id=customer_inst.id if customer_inst else None,
            po_number=extracted_invoice.po_number,
            invoice_date=extracted_invoice.invoice_date,
            due_date=extracted_invoice.due_date,
            currency=extracted_invoice.currency or "USD",
            subtotal=extracted_invoice.subtotal,
            discount=extracted_invoice.discount,
            shipping_charge=extracted_invoice.shipping_charge,
            tax_amount=extracted_invoice.tax_amount,
            total_amount=extracted_invoice.total_amount,
            amount_paid=extracted_invoice.amount_paid,
            amount_due=extracted_invoice.amount_due,
            status=status,
            source_filename=source_filename
        )
        session.add(invoice_rec)
        session.flush()

        # Insert Line Items
        for item in extracted_invoice.line_items:
            line_item_rec = InvoiceLineItemModel(
                invoice_id=invoice_rec.id,
                description=item.description,
                product_code=item.product_code,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount=item.discount,
                tax_amount=item.tax_amount,
                line_total=item.line_total
            )
            session.add(line_item_rec)

        # Insert Validation Record
        if validation_result:
            errors_data = [e.model_dump() for e in validation_result.errors]
            warnings_data = [w.model_dump() for w in validation_result.warnings]

            val_rec = ValidationRecordModel(
                invoice_id=invoice_rec.id,
                is_valid=validation_result.is_valid,
                errors_json=json.dumps(errors_data),
                warnings_json=json.dumps(warnings_data)
            )
            session.add(val_rec)

            # If validation failed, create human review task entry
            if not validation_result.is_valid:
                primary_reason = validation_result.errors[0].rule_name if validation_result.errors else "VALIDATION_FAILED"
                review_task = ReviewTaskModel(
                    invoice_id=invoice_rec.id,
                    reason=primary_reason,
                    status="PENDING"
                )
                session.add(review_task)

        session.flush()
        return invoice_rec

    def get_by_id(self, session: Session, invoice_id: int) -> Optional[InvoiceModel]:
        """Retrieves invoice by primary key with relations eagerly loaded."""
        return session.query(InvoiceModel).options(
            joinedload(InvoiceModel.vendor),
            joinedload(InvoiceModel.customer),
            joinedload(InvoiceModel.line_items),
            joinedload(InvoiceModel.validation_records)
        ).filter(InvoiceModel.id == invoice_id).first()

    def list_invoices(
        self, session: Session, status: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> List[InvoiceModel]:
        """Retrieves paginated list of invoice records."""
        query = session.query(InvoiceModel).options(
            joinedload(InvoiceModel.vendor),
            joinedload(InvoiceModel.customer)
        )
        if status:
            query = query.filter(InvoiceModel.status == status)
        return query.order_by(InvoiceModel.created_at.desc()).offset(offset).limit(limit).all()
