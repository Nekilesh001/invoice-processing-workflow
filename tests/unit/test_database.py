from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base
from app.database.models import InvoiceModel, VendorModel
from app.database.repositories.invoice_repository import InvoiceRepository
from app.schemas.invoice import ExtractedInvoice, VendorInfo, CustomerInfo, LineItem
from app.validation.validator import InvoiceValidator


@pytest.fixture
def db_session():
    """In-memory SQLite session fixture for isolated fast database testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_init_db_schema_creation(db_session):
    repo = InvoiceRepository()
    vendor = repo.get_or_create_vendor(db_session, "Acme Cloud Solutions")
    assert vendor.id is not None
    assert vendor.name == "Acme Cloud Solutions"


def test_save_extracted_invoice_with_lines_and_validation(db_session):
    repo = InvoiceRepository()
    validator = InvoiceValidator()

    invoice = ExtractedInvoice(
        invoice_number="INV-2026-101",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        customer=CustomerInfo(customer_name="Global Logistics Corp"),
        line_items=[
            LineItem(
                description="Cloud Hosting",
                quantity=Decimal("1.0"),
                unit_price=Decimal("1000.00"),
                line_total=Decimal("1000.00")
            )
        ],
        subtotal=Decimal("1000.00"),
        tax_amount=Decimal("100.00"),
        total_amount=Decimal("1100.00"),
        amount_due=Decimal("1100.00")
    )

    validation_result = validator.validate(invoice)
    saved_invoice = repo.save_invoice(
        db_session,
        extracted_invoice=invoice,
        validation_result=validation_result,
        source_filename="invoice_001_normal.pdf"
    )

    assert saved_invoice.id is not None
    assert saved_invoice.invoice_number == "INV-2026-101"
    assert saved_invoice.status == "APPROVED"
    assert saved_invoice.vendor.name == "Acme Cloud Solutions Inc."
    assert saved_invoice.customer.name == "Global Logistics Corp"
    assert len(saved_invoice.line_items) == 1
    assert saved_invoice.line_items[0].description == "Cloud Hosting"
    assert len(saved_invoice.validation_records) == 1
    assert saved_invoice.validation_records[0].is_valid is True


def test_duplicate_check(db_session):
    repo = InvoiceRepository()
    invoice = ExtractedInvoice(
        invoice_number="INV-2026-DUP",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        vendor=VendorInfo(vendor_name="Duplicate Vendor Ltd"),
        subtotal=Decimal("500.00"),
        total_amount=Decimal("500.00")
    )

    assert repo.check_duplicate(db_session, "Duplicate Vendor Ltd", "INV-2026-DUP") is False

    repo.save_invoice(db_session, invoice)

    assert repo.check_duplicate(db_session, "Duplicate Vendor Ltd", "INV-2026-DUP") is True
    assert repo.check_duplicate(db_session, "Duplicate Vendor Ltd", "INV-2026-DIFFERENT") is False


def test_get_by_id_and_list_invoices(db_session):
    repo = InvoiceRepository()
    invoice = ExtractedInvoice(
        invoice_number="INV-2026-LIST",
        vendor=VendorInfo(vendor_name="List Vendor"),
        subtotal=Decimal("300.00"),
        total_amount=Decimal("300.00")
    )

    saved = repo.save_invoice(db_session, invoice)
    fetched = repo.get_by_id(db_session, saved.id)
    
    assert fetched is not None
    assert fetched.invoice_number == "INV-2026-LIST"

    invoices = repo.list_invoices(db_session)
    assert len(invoices) >= 1
