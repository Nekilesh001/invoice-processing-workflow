import pytest
from decimal import Decimal

from app.database.connection import get_engine, init_db, get_session_factory
from app.database.models import VendorModel, PurchaseOrderModel
from app.database.repositories.purchase_order_repository import PurchaseOrderRepository
from app.database.repositories.invoice_repository import InvoiceRepository
from app.agents.tools import lookup_purchase_order, lookup_vendor
from app.agents.invoice_agent import InvoiceAgent
from app.schemas.invoice import ExtractedInvoice, VendorInfo
from app.schemas.processing import ValidationResult
from datetime import date


@pytest.fixture
def memory_db_session():
    """Provides a fresh, clean in-memory SQLite database session for unit tests."""
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()

    # Populate synthetic test vendors and POs
    inv_repo = InvoiceRepository()
    v1 = inv_repo.get_or_create_vendor(session, "Acme Cloud Solutions Inc.", tax_id="US-88492019")
    v2 = inv_repo.get_or_create_vendor(session, "Vertex Software Solutions", tax_id="US-10293847")

    po_repo = PurchaseOrderRepository()
    po_repo.create(session, {
        "po_number": "PO-8842",
        "vendor_id": v1.id,
        "authorized_total": "3300.00",
        "remaining_balance": "3300.00",
        "status": "APPROVED"
    }, [{"description": "Cloud Service", "quantity": 10, "unit_price": 330, "line_total": 3300}])

    po_repo.create(session, {
        "po_number": "PO-EXHAUSTED",
        "vendor_id": v1.id,
        "authorized_total": "500.00",
        "remaining_balance": "0.00",
        "status": "EXHAUSTED"
    })

    session.commit()
    yield session
    session.close()


def test_1_po_found_in_database(memory_db_session):
    """Test 1 — PO found in database returning real SQL record."""
    res = lookup_purchase_order("PO-8842", session=memory_db_session)
    assert res["found"] is True
    assert res["status"] == "APPROVED"
    assert res["po_number"] == "PO-8842"
    assert res["vendor_name"] == "Acme Cloud Solutions Inc."
    assert res["authorized_total"] == 3300.0
    assert len(res["line_items"]) == 1


def test_2_po_not_found(memory_db_session):
    """Test 2 — PO not found returning PO_NOT_FOUND."""
    res = lookup_purchase_order("PO-NONEXISTENT-999", session=memory_db_session)
    assert res["found"] is False
    assert res["status"] == "PO_NOT_FOUND"
    assert "PO-NONEXISTENT-999" in res["message"]


def test_3_database_failure_handling():
    """Test 3 — Database failure handling returning DATABASE_ERROR."""
    class BrokenSession:
        def query(self, *args, **kwargs):
            raise RuntimeError("Database connection lost simulated")

    res = lookup_purchase_order("PO-8842", session=BrokenSession())
    assert res["found"] is False
    assert res["status"] == "DATABASE_ERROR"
    assert "Database error" in res["message"]


def test_4_vendor_found_in_database(memory_db_session):
    """Test 4 — Registered vendor found returning VERIFIED."""
    res = lookup_vendor("Acme Cloud Solutions Inc.", session=memory_db_session)
    assert res["found"] is True
    assert res["status"] == "VERIFIED"
    assert res["is_approved"] is True
    assert res["tax_id"] == "US-88492019"


def test_5_unknown_vendor_not_verified(memory_db_session):
    """Test 5 — Unknown vendor returns UNKNOWN_VENDOR and is NOT verified."""
    res = lookup_vendor("Unregistered Rogue Vendor LLC", session=memory_db_session)
    assert res["found"] is False
    assert res["status"] == "UNKNOWN_VENDOR"
    assert res["is_approved"] is False


def test_6_agent_unknown_vendor_routes_to_human_review(memory_db_session):
    """Test 6 — Agent safely routes unknown vendor to HUMAN_REVIEW."""
    agent = InvoiceAgent()
    invoice = ExtractedInvoice(
        invoice_number="INV-9999",
        invoice_date=date(2026, 8, 15),
        vendor=VendorInfo(vendor_name="Unregistered Rogue Vendor LLC"),
        total_amount=Decimal("100.00")
    )
    val_res = ValidationResult(is_valid=True, errors=[], warnings=[], confidence_score=1.0)
    decision = agent.evaluate_and_decide(invoice, val_res, db_session=memory_db_session)

    assert decision.action == "HUMAN_REVIEW"
    assert "UNKNOWN_VENDOR" in decision.reason


def test_7_agent_po_lookup_success(memory_db_session):
    """Test 7 — Agent PO lookup retrieves real SQL-backed PO record."""
    agent = InvoiceAgent()
    invoice = ExtractedInvoice(
        invoice_number="INV-8842",
        invoice_date=date(2026, 8, 15),
        po_number="PO-8842",
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        subtotal=Decimal("3300.00"),
        total_amount=Decimal("3300.00")
    )
    val_res = ValidationResult(is_valid=True, errors=[], warnings=[], confidence_score=1.0)
    decision = agent.evaluate_and_decide(invoice, val_res, db_session=memory_db_session)

    assert decision.action == "AUTO_PROCESS"
    assert decision.po_verified is True


def test_8_no_po_invoice_skips_po_lookup(memory_db_session):
    """Test 8 — Invoice without PO does not call lookup_purchase_order."""
    agent = InvoiceAgent()
    invoice = ExtractedInvoice(
        invoice_number="INV-NO-PO-123",
        invoice_date=date(2026, 8, 15),
        po_number=None,
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        subtotal=Decimal("100.00"),
        total_amount=Decimal("100.00")
    )
    val_res = ValidationResult(is_valid=True, errors=[], warnings=[], confidence_score=1.0)
    decision = agent.evaluate_and_decide(invoice, val_res, db_session=memory_db_session)

    executed_tool_names = [t["tool"] for t in decision.executed_tools]
    assert "lookup_purchase_order" not in executed_tool_names
