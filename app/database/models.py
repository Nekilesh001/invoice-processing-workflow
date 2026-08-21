from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Date,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class VendorModel(Base):
    """Master vendor/biller table."""
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(Text, nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    tax_id = Column(String(100), nullable=True)
    registration_number = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    invoices = relationship("InvoiceModel", back_populates="vendor", cascade="all, delete-orphan")


class CustomerModel(Base):
    """Master customer/buyer table."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(Text, nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    tax_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    invoices = relationship("InvoiceModel", back_populates="customer", cascade="all, delete-orphan")


class InvoiceModel(Base):
    """Central invoice records table."""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(100), nullable=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    po_number = Column(String(100), nullable=True, index=True)
    invoice_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    currency = Column(String(10), default="USD", nullable=False)
    
    subtotal = Column(Numeric(12, 2), nullable=True)
    discount = Column(Numeric(12, 2), default=0.00, nullable=True)
    shipping_charge = Column(Numeric(12, 2), default=0.00, nullable=True)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=True)
    amount_paid = Column(Numeric(12, 2), default=0.00, nullable=True)
    amount_due = Column(Numeric(12, 2), nullable=True)
    
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, APPROVED, REJECTED, NEEDS_REVIEW
    file_hash = Column(String(64), nullable=True, index=True)
    source_filename = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    vendor = relationship("VendorModel", back_populates="invoices")
    customer = relationship("CustomerModel", back_populates="invoices")
    line_items = relationship("InvoiceLineItemModel", back_populates="invoice", cascade="all, delete-orphan")
    validation_records = relationship("ValidationRecordModel", back_populates="invoice", cascade="all, delete-orphan")
    review_tasks = relationship("ReviewTaskModel", back_populates="invoice", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_vendor_invoice_num", "vendor_id", "invoice_number"),
        UniqueConstraint("vendor_id", "invoice_number", name="uq_vendor_invoice_num"),
    )


class InvoiceLineItemModel(Base):
    """Detailed invoice line items table."""
    __tablename__ = "invoice_line_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    product_code = Column(String(100), nullable=True)
    quantity = Column(Numeric(10, 2), default=1.00, nullable=False)
    unit_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    discount = Column(Numeric(12, 2), default=0.00, nullable=True)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=True)
    line_total = Column(Numeric(12, 2), default=0.00, nullable=False)

    invoice = relationship("InvoiceModel", back_populates="line_items")


class ValidationRecordModel(Base):
    """Stored validation check execution history."""
    __tablename__ = "invoice_validation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    is_valid = Column(Boolean, nullable=False)
    errors_json = Column(Text, nullable=True)
    warnings_json = Column(Text, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    invoice = relationship("InvoiceModel", back_populates="validation_records")


class ProcessingRunModel(Base):
    """System processing run audit log."""
    __tablename__ = "processing_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    extraction_method = Column(String(50), nullable=False)
    extracted_chars = Column(Integer, default=0, nullable=False)
    duration_ms = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ReviewTaskModel(Base):
    """Human-in-the-loop review task queue."""
    __tablename__ = "review_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(String(255), nullable=False)  # MISSING_REQUIRED_FIELD, TOTAL_MISMATCH, DUPLICATE_SUSPECTED, etc.
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED
    assigned_to = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    invoice = relationship("InvoiceModel", back_populates="review_tasks")
