import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.database.connection import init_db, get_session_factory, get_db
from app.database.repositories.invoice_repository import InvoiceRepository
from app.database.models import InvoiceModel, ReviewTaskModel, ReviewActionModel


@pytest.fixture
def dashboard_test_db():
    import app.database.models
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()

    inv_repo = InvoiceRepository()
    v1 = inv_repo.get_or_create_vendor(session, "Acme Cloud Solutions Inc.", tax_id="US-111")

    # 1. Approved invoice: $100.00
    inv1 = InvoiceModel(
        invoice_number="INV-APP-001",
        vendor_id=v1.id,
        total_amount=100.00,
        status="APPROVED"
    )
    # 2. Review invoice: $200.00
    inv2 = InvoiceModel(
        invoice_number="INV-REV-002",
        vendor_id=v1.id,
        total_amount=200.00,
        status="NEEDS_REVIEW"
    )
    # 3. Rejected invoice: $300.00
    inv3 = InvoiceModel(
        invoice_number="INV-REJ-003",
        vendor_id=v1.id,
        total_amount=300.00,
        status="REJECTED"
    )

    session.add_all([inv1, inv2, inv3])
    session.flush()

    task1 = ReviewTaskModel(
        invoice_id=inv2.id,
        reason="QUANTITY_MISMATCH",
        status="PENDING"
    )
    session.add(task1)

    act1 = ReviewActionModel(
        invoice_id=inv3.id,
        action="REJECTED",
        previous_invoice_status="NEEDS_REVIEW",
        new_invoice_status="REJECTED",
        reviewer_name="Finance Reviewer",
        comment="PO balance mismatch"
    )
    session.add(act1)
    session.commit()

    def override_get_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    client = TestClient(fastapi_app)
    yield client, session
    fastapi_app.dependency_overrides.clear()
    session.close()


def test_dashboard_summary_api(dashboard_test_db):
    client, session = dashboard_test_db

    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()

    # Verify counts
    counts = data["invoice_counts"]
    assert counts["total"] == 3
    assert counts["approved"] == 1
    assert counts["human_review"] == 1
    assert counts["rejected"] == 1
    assert counts["processing"] == 0

    # Verify financial totals
    financials = data["financial_totals"]
    assert financials["total_invoice_value"] == 600.00
    assert financials["approved_value"] == 100.00
    assert financials["review_value"] == 200.00
    assert financials["rejected_value"] == 300.00

    # Verify review metrics
    assert data["review_metrics"]["pending_count"] == 1

    # Verify verification issue grouping
    issues = data["verification_issues"]
    assert len(issues) >= 1
    assert issues[0]["reason"] == "QUANTITY_MISMATCH"
    assert issues[0]["count"] == 1

    # Verify recent invoices list
    rec_invs = data["recent_invoices"]
    assert len(rec_invs) == 3

    # Verify recent review activity list
    rec_revs = data["recent_reviews"]
    assert len(rec_revs) == 1
    assert rec_revs[0]["action"] == "REJECTED"


def test_dashboard_empty_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    init_db(engine)
    session_factory = get_session_factory(engine)

    def override_get_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    client = TestClient(fastapi_app)

    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["invoice_counts"]["total"] == 0
    assert data["financial_totals"]["total_invoice_value"] == 0.0
    assert len(data["recent_invoices"]) == 0
    assert len(data["recent_reviews"]) == 0

    fastapi_app.dependency_overrides.clear()
