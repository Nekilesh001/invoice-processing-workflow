import logging
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agents.invoice_agent import InvoiceAgent
from app.config import settings
from app.database.connection import Base
from app.database.models import InvoiceModel, ReviewTaskModel
from app.extraction.extractor import DocumentExtractor
from app.llm.client import LLMClient
from app.schemas.invoice import ExtractedInvoice, VendorInfo, LineItem
from app.schemas.processing import ProcessingStatus
from app.services.pipeline_runner import InvoicePipelineRunner
from app.validation.validator import InvoiceValidator

# Configure logger output for test verification
logger = logging.getLogger("app.agents.invoice_agent")
logger.setLevel(logging.INFO)


@pytest.fixture
def test_db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@patch("app.llm.client.LLMClient.extract_invoice_json")
def test_scenario_1_normal_invoice_end_to_end(mock_llm_extract, test_db_session):
    """
    Step 3 — Run a Normal Invoice through PipelineRunner -> InvoiceAgent -> DB
    """
    mock_llm_extract.return_value = {
        "invoice_number": "INV-2026-NORMAL-001",
        "invoice_date": "2026-08-15",
        "due_date": "2026-09-15",
        "currency": "USD",
        "po_number": "PO-8842",
        "vendor": {"vendor_name": "Acme Cloud Solutions Inc."},
        "customer": {"customer_name": "Global Logistics Corp"},
        "line_items": [
            {"description": "Cloud Infra", "quantity": 1.0, "unit_price": 3000.00, "line_total": 3000.00}
        ],
        "subtotal": 3000.00,
        "tax_amount": 300.00,
        "total_amount": 3300.00,
        "amount_due": 3300.00
    }

    runner = InvoicePipelineRunner()
    pdf_path = settings.BASE_DIR / "data" / "sample_invoices" / "invoice_001_normal.pdf"

    result = runner.process_file(pdf_path, db_session=test_db_session)

    assert result.status == ProcessingStatus.SUCCESS
    assert result.database_invoice_id is not None

    # Query DB to verify persistence
    inv_db = test_db_session.query(InvoiceModel).filter(InvoiceModel.id == result.database_invoice_id).first()
    assert inv_db is not None
    assert inv_db.status == "APPROVED"
    assert inv_db.invoice_number == "INV-2026-NORMAL-001"


@patch("app.llm.client.LLMClient.extract_invoice_json")
def test_scenario_2_no_po_invoice_tool_selection(mock_llm_extract, test_db_session):
    """
    Step 4 — Run a No-PO Invoice. Verify lookup_purchase_order is NOT called.
    """
    mock_llm_extract.return_value = {
        "invoice_number": "INV-2026-NO-PO-999",
        "invoice_date": "2026-08-15",
        "due_date": "2026-09-15",
        "currency": "USD",
        "po_number": None,  # No PO number present!
        "vendor": {"vendor_name": "Acme Cloud Solutions Inc."},
        "subtotal": 1000.00,
        "total_amount": 1000.00
    }

    runner = InvoicePipelineRunner()
    pdf_path = settings.BASE_DIR / "data" / "sample_invoices" / "invoice_001_normal.pdf"

    result = runner.process_file(pdf_path, db_session=test_db_session)

    assert result.status == ProcessingStatus.SUCCESS

    # Verify executed tools in Agent decision trace
    inv = ExtractedInvoice.model_validate(mock_llm_extract.return_value)
    val_res = InvoiceValidator().validate(inv)
    agent = InvoiceAgent()
    decision = agent.evaluate_and_decide(inv, val_res, db_session=test_db_session)

    executed_tools = [t["tool"] for t in decision.executed_tools]
    assert "lookup_purchase_order" not in executed_tools  # Proves dynamic tool selection based on evidence!


@patch("app.llm.client.LLMClient.extract_invoice_json")
def test_scenario_3_po_mismatch_drives_human_review(mock_llm_extract, test_db_session):
    """
    Step 5 — Run PO-Mismatch Invoice. Verify tool result directly influences decision to HUMAN_REVIEW.
    """
    mock_llm_extract.return_value = {
        "invoice_number": "INV-2026-MISMATCH-88",
        "invoice_date": "2026-08-15",
        "due_date": "2026-09-15",
        "currency": "USD",
        "po_number": "PO-8842",  # PO-8842 is authorized for $3300.00
        "vendor": {"vendor_name": "Acme Cloud Solutions Inc."},
        "subtotal": 9000.00,
        "total_amount": 9000.00  # Mismatch! $9000 vs $3300
    }

    runner = InvoicePipelineRunner()
    pdf_path = settings.BASE_DIR / "data" / "sample_invoices" / "invoice_001_normal.pdf"

    result = runner.process_file(pdf_path, db_session=test_db_session)

    assert result.status == ProcessingStatus.NEEDS_REVIEW
    assert result.database_invoice_id is not None

    inv_db = test_db_session.query(InvoiceModel).filter(InvoiceModel.id == result.database_invoice_id).first()
    assert inv_db.status == "NEEDS_REVIEW"


@patch("app.llm.client.LLMClient.extract_invoice_json")
def test_scenario_4_duplicate_invoice_and_idempotency(mock_llm_extract, test_db_session):
    """
    Step 6 — Process duplicate invoice twice. Verify duplicate detection, DB uniqueness, and review task idempotency.
    """
    mock_json = {
        "invoice_number": "INV-2026-DUP-CHECK",
        "invoice_date": "2026-08-15",
        "due_date": "2026-09-15",
        "currency": "USD",
        "vendor": {"vendor_name": "Duplicate Test Biller Inc."},
        "subtotal": 1200.00,
        "total_amount": 1200.00
    }
    mock_llm_extract.return_value = mock_json

    runner = InvoicePipelineRunner()
    pdf_path = settings.BASE_DIR / "data" / "sample_invoices" / "invoice_001_normal.pdf"

    # First run -> SUCCESS
    res1 = runner.process_file(pdf_path, db_session=test_db_session)
    assert res1.status == ProcessingStatus.SUCCESS

    # Second run -> DUPLICATE_SUSPECTED
    res2 = runner.process_file(pdf_path, db_session=test_db_session)
    assert res2.status == ProcessingStatus.DUPLICATE_SUSPECTED

    # DB Assertions: Verify only 1 invoice header record exists (DB unique constraint protection)
    invoices_count = test_db_session.query(InvoiceModel).filter(
        InvoiceModel.invoice_number == "INV-2026-DUP-CHECK"
    ).count()
    assert invoices_count == 1

    # Verify review tasks count == 1 (Write Tool Idempotency protection)
    tasks_count = test_db_session.query(ReviewTaskModel).filter(
        ReviewTaskModel.invoice_id == res1.database_invoice_id
    ).count()
    assert tasks_count == 1


def test_scenario_5_controlled_tool_failure():
    """
    Step 7 — Run Tool Failure. Verify non-existent PO yields safe HUMAN_REVIEW fallback.
    """
    agent = InvoiceAgent()
    validator = InvoiceValidator()

    invoice = ExtractedInvoice(
        invoice_number="INV-2026-TOOL-FAIL",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        po_number="PO-NONEXISTENT-999",
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        subtotal=Decimal("1000.00"),
        total_amount=Decimal("1000.00")
    )
    val_res = validator.validate(invoice)
    decision = agent.evaluate_and_decide(invoice, val_res)

    assert decision.action == "HUMAN_REVIEW"
    assert "PO_NOT_FOUND" in decision.reason


def test_scenario_6_max_iterations_boundary():
    """
    Step 8 — Test Max Iterations. Verify execution halts at limit with safe HUMAN_REVIEW fallback.
    """
    agent = InvoiceAgent(max_iterations=0)
    validator = InvoiceValidator()

    invoice = ExtractedInvoice(
        invoice_number="INV-2026-BOUNDARY",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        subtotal=Decimal("1000.00"),
        total_amount=Decimal("1000.00")
    )
    val_res = validator.validate(invoice)
    decision = agent.evaluate_and_decide(invoice, val_res)

    assert decision.action == "HUMAN_REVIEW"
    assert "MAX_ITERATIONS_EXCEEDED" in decision.reason


@patch("app.llm.client.LLMClient.extract_invoice_json")
def test_scenario_7_active_pipeline_integration(mock_llm_extract, test_db_session):
    """
    Step 10 — Verify active pipeline integration. Prove InvoiceAgent is invoked during process_file.
    """
    mock_llm_extract.return_value = {
        "invoice_number": "INV-2026-INTEG-001",
        "invoice_date": "2026-08-15",
        "due_date": "2026-09-15",
        "currency": "USD",
        "vendor": {"vendor_name": "Acme Cloud Solutions Inc."},
        "subtotal": 1000.00,
        "total_amount": 1000.00
    }

    mock_agent = MagicMock()
    from app.agents.invoice_agent import AgentDecision
    mock_agent.evaluate_and_decide.return_value = AgentDecision(
        action="AUTO_PROCESS",
        reason="Spy verification passed."
    )

    runner = InvoicePipelineRunner(agent=mock_agent)
    pdf_path = settings.BASE_DIR / "data" / "sample_invoices" / "invoice_001_normal.pdf"

    result = runner.process_file(pdf_path, db_session=test_db_session)

    assert mock_agent.evaluate_and_decide.called is True
    assert result.status == ProcessingStatus.SUCCESS
