from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database.connection import Base
from app.database.repositories.invoice_repository import InvoiceRepository
from app.schemas.processing import ProcessingStatus
from app.services.pipeline_runner import InvoicePipelineRunner


@pytest.fixture
def sqlite_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@patch("app.llm.client.LLMClient.extract_invoice_json")
def test_pipeline_normal_invoice_success(mock_llm_extract, sqlite_session):
    mock_llm_extract.return_value = {
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-08-15",
        "due_date": "2026-09-15",
        "currency": "USD",
        "po_number": "PO-8842",
        "vendor": {
            "vendor_name": "Acme Cloud Solutions Inc.",
            "vendor_email": "billing@acmecloud.com"
        },
        "customer": {
            "customer_name": "Global Logistics Corp"
        },
        "line_items": [
            {
                "description": "Enterprise Cloud Server Infrastructure",
                "quantity": 1.0,
                "unit_price": 2500.00,
                "line_total": 2500.00
            },
            {
                "description": "Database Service",
                "quantity": 2.0,
                "unit_price": 250.00,
                "line_total": 500.00
            }
        ],
        "subtotal": 3000.00,
        "tax_amount": 300.00,
        "total_amount": 3300.00,
        "amount_due": 3300.00
    }

    runner = InvoicePipelineRunner()
    pdf_path = settings.BASE_DIR / "data" / "sample_invoices" / "invoice_001_normal.pdf"

    result = runner.process_file(pdf_path, db_session=sqlite_session)

    assert result.status == ProcessingStatus.SUCCESS
    assert result.database_invoice_id is not None
    assert result.validation_result.is_valid is True
    assert result.review_task_id is None


@patch("app.llm.client.LLMClient.extract_invoice_json")
def test_pipeline_missing_due_date_needs_review(mock_llm_extract, sqlite_session):
    mock_llm_extract.return_value = {
        "invoice_number": "INV-2026-002",
        "invoice_date": "2026-08-18",
        "due_date": None,  # Missing due date!
        "currency": "USD",
        "vendor": {"vendor_name": "Vertex Software Solutions"},
        "customer": {"customer_name": "Apex Retailers LLC"},
        "line_items": [
            {"description": "API Integration", "quantity": 10.0, "unit_price": 150.00, "line_total": 1500.00}
        ],
        "subtotal": 1500.00,
        "tax_amount": 120.00,
        "total_amount": 1620.00,
        "amount_due": 1620.00
    }

    runner = InvoicePipelineRunner()
    pdf_path = settings.BASE_DIR / "data" / "sample_invoices" / "invoice_002_missing_due_date.pdf"

    result = runner.process_file(pdf_path, db_session=sqlite_session)

    assert result.status == ProcessingStatus.NEEDS_REVIEW
    assert result.database_invoice_id is not None
    assert result.validation_result.is_valid is False
    assert result.review_task_id is not None


@patch("app.llm.client.LLMClient.extract_invoice_json")
def test_pipeline_duplicate_detection(mock_llm_extract, sqlite_session):
    mock_json = {
        "invoice_number": "INV-2026-DUP",
        "invoice_date": "2026-08-15",
        "due_date": "2026-09-15",
        "currency": "USD",
        "vendor": {"vendor_name": "Duplicate Vendor Inc."},
        "subtotal": 1000.00,
        "total_amount": 1000.00
    }
    mock_llm_extract.return_value = mock_json

    runner = InvoicePipelineRunner()
    pdf_path = settings.BASE_DIR / "data" / "sample_invoices" / "invoice_001_normal.pdf"

    # First run -> SUCCESS
    res1 = runner.process_file(pdf_path, db_session=sqlite_session)
    assert res1.status == ProcessingStatus.SUCCESS

    # Second run with same vendor and invoice_number -> DUPLICATE_SUSPECTED
    res2 = runner.process_file(pdf_path, db_session=sqlite_session)
    assert res2.status == ProcessingStatus.DUPLICATE_SUSPECTED
