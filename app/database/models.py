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
    JSON,
    ForeignKey,
    Index,
    UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class UserModel(Base):
    """User account table for authentication and Role-Based Access Control (RBAC)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="VIEWER", nullable=False)  # ADMIN, AP_MANAGER, REVIEWER, VIEWER
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    review_actions = relationship("ReviewActionModel", back_populates="reviewer_user")


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
    purchase_orders = relationship("PurchaseOrderModel", back_populates="vendor", cascade="all, delete-orphan")


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
    review_actions = relationship("ReviewActionModel", back_populates="invoice", cascade="all, delete-orphan", order_by="desc(ReviewActionModel.created_at), desc(ReviewActionModel.id)")

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
    review_actions = relationship("ReviewActionModel", back_populates="review_task")


class ReviewActionModel(Base):
    """Audit log of human review decisions, comments, and status transitions."""
    __tablename__ = "review_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_task_id = Column(Integer, ForeignKey("review_tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # APPROVED, REJECTED
    previous_invoice_status = Column(String(50), nullable=False)
    new_invoice_status = Column(String(50), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reviewer_name = Column(String(100), default="Finance Reviewer", nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    invoice = relationship("InvoiceModel", back_populates="review_actions")
    review_task = relationship("ReviewTaskModel", back_populates="review_actions")
    reviewer_user = relationship("UserModel", back_populates="review_actions")


class PurchaseOrderModel(Base):
    """Enterprise Purchase Order master table."""
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    po_number = Column(String(100), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="RESTRICT"), nullable=False, index=True)
    po_date = Column(Date, nullable=True)
    currency = Column(String(10), default="USD", nullable=False)

    subtotal = Column(Numeric(12, 2), nullable=True)
    discount = Column(Numeric(12, 2), default=0.00, nullable=True)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=True)
    authorized_total = Column(Numeric(12, 2), nullable=False)
    remaining_balance = Column(Numeric(12, 2), nullable=False)

    status = Column(String(50), default="APPROVED", nullable=False, index=True)  # DRAFT, PENDING, APPROVED, PARTIALLY_USED, EXHAUSTED, CANCELLED, CLOSED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    vendor = relationship("VendorModel", back_populates="purchase_orders")
    line_items = relationship("PurchaseOrderLineItemModel", back_populates="purchase_order", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_vendor_po_num", "vendor_id", "po_number"),
        UniqueConstraint("vendor_id", "po_number", name="uq_vendor_po_num"),
    )


class PurchaseOrderLineItemModel(Base):
    """Line items for Purchase Orders."""
    __tablename__ = "purchase_order_line_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    product_code = Column(String(100), nullable=True)
    quantity = Column(Numeric(10, 2), default=1.00, nullable=False)
    unit = Column(String(20), default="units", nullable=True)
    unit_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    discount = Column(Numeric(12, 2), default=0.00, nullable=True)
    tax_rate = Column(Numeric(5, 2), default=0.00, nullable=True)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=True)
    line_total = Column(Numeric(12, 2), default=0.00, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    purchase_order = relationship("PurchaseOrderModel", back_populates="line_items")


class AnalystQueryModel(Base):
    """Database audit storage for natural language Data Analyst Assistant Q&A history."""
    __tablename__ = "analyst_queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    tools_used = Column(JSON, nullable=True)
    sources = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

