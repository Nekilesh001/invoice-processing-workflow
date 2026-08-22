import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.database.connection import init_db, get_session_factory, get_db
from app.database.repositories.invoice_repository import InvoiceRepository
from app.database.models import InvoiceModel, ReviewTaskModel, ReviewActionModel


@pytest.fixture
def review_test_db():
    import app.database.models
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()

    inv_repo = InvoiceRepository()
    v1 = inv_repo.get_or_create_vendor(session, "Vertex Software", tax_id="US-999")

    # Create flagged invoice needing review
    inv1 = InvoiceModel(
        invoice_number="INV-FLAGGED-001",
        vendor_id=v1.id,
        po_number="PO-8842",
        total_amount=9000.0,
        status="NEEDS_REVIEW"
    )
    session.add(inv1)
    session.flush()

    task1 = ReviewTaskModel(
        invoice_id=inv1.id,
        reason="QUANTITY_MISMATCH",
        status="PENDING"
    )
    session.add(task1)
    session.commit()

    def override_get_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    client = TestClient(fastapi_app)
    yield client, session, task1, inv1
    fastapi_app.dependency_overrides.clear()
    session.close()


def test_approve_review_task_with_comment(review_test_db):
    client, session, task1, inv1 = review_test_db

    payload = {
        "reviewer": "Senior AP Specialist",
        "comment": "Verified quantity discrepancy with procurement team."
    }
    response = client.post(f"/api/v1/reviews/{task1.id}/approve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"
    assert data["action"] == "APPROVED"
    assert data["reviewer"] == "Senior AP Specialist"
    assert data["comment"] == "Verified quantity discrepancy with procurement team."

    # Check review history API
    history_res = client.get(f"/api/v1/invoices/{inv1.id}/review-history")
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 1
    assert history[0]["action"] == "APPROVED"
    assert history[0]["previous_status"] == "NEEDS_REVIEW"
    assert history[0]["new_status"] == "APPROVED"
    assert history[0]["reviewer"] == "Senior AP Specialist"


def test_reject_review_task_with_comment(review_test_db):
    client, session, task1, inv1 = review_test_db

    payload = {
        "reviewer": "Compliance Lead",
        "comment": "Unauthorized PO balance overrun."
    }
    response = client.post(f"/api/v1/reviews/{task1.id}/reject", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECTED"
    assert data["action"] == "REJECTED"

    # Verify database state updated
    history_res = client.get(f"/api/v1/invoices/{inv1.id}/review-history")
    history = history_res.json()
    assert len(history) == 1
    assert history[0]["action"] == "REJECTED"
    assert history[0]["comment"] == "Unauthorized PO balance overrun."


def test_reject_without_comment_fails(review_test_db):
    client, session, task1, inv1 = review_test_db

    # Empty payload
    response = client.post(f"/api/v1/reviews/{task1.id}/reject", json={})
    assert response.status_code == 400
    assert "required" in response.json()["detail"].lower()

    # Whitespace payload
    response2 = client.post(f"/api/v1/reviews/{task1.id}/reject", json={"comment": "   "})
    assert response2.status_code == 400


def test_double_approval_conflict(review_test_db):
    client, session, task1, inv1 = review_test_db

    # First approval succeeds
    res1 = client.post(f"/api/v1/reviews/{task1.id}/approve", json={"comment": "Approved"})
    assert res1.status_code == 200

    # Second approval fails with 409 Conflict
    res2 = client.post(f"/api/v1/reviews/{task1.id}/approve", json={"comment": "Approve again"})
    assert res2.status_code == 409


def test_double_rejection_conflict(review_test_db):
    client, session, task1, inv1 = review_test_db

    # First rejection succeeds
    res1 = client.post(f"/api/v1/reviews/{task1.id}/reject", json={"comment": "Rejecting order"})
    assert res1.status_code == 200

    # Second rejection fails with 409 Conflict
    res2 = client.post(f"/api/v1/reviews/{task1.id}/reject", json={"comment": "Rejecting again"})
    assert res2.status_code == 409


def test_review_history_ordering(review_test_db):
    client, session, task1, inv1 = review_test_db

    # Insert two actions directly into database
    a1 = ReviewActionModel(
        invoice_id=inv1.id,
        action="REJECTED",
        previous_invoice_status="NEEDS_REVIEW",
        new_invoice_status="REJECTED",
        reviewer_name="Analyst 1",
        comment="First decision"
    )
    a2 = ReviewActionModel(
        invoice_id=inv1.id,
        action="APPROVED",
        previous_invoice_status="REJECTED",
        new_invoice_status="APPROVED",
        reviewer_name="Analyst 2",
        comment="Second decision override"
    )
    session.add(a1)
    session.add(a2)
    session.commit()

    history_res = client.get(f"/api/v1/invoices/{inv1.id}/review-history")
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 2
    # Verify ordering (most recent first)
    assert history[0]["comment"] == "Second decision override"
    assert history[1]["comment"] == "First decision"
