from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database.connection import Base, get_db
from app.database.models import InvoiceModel, ReviewTaskModel
from app.main import app


@pytest.fixture
def api_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_health_check(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"


def test_list_invoices_empty(api_client):
    response = api_client.get("/api/v1/invoices")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@patch("app.llm.client.LLMClient.extract_invoice_json")
def test_process_invoice_upload(mock_llm_extract, api_client):
    mock_llm_extract.return_value = {
        "invoice_number": "INV-API-001",
        "invoice_date": "2026-08-15",
        "due_date": "2026-09-15",
        "currency": "USD",
        "vendor": {"vendor_name": "API Test Vendor"},
        "customer": {"customer_name": "API Test Customer"},
        "subtotal": 1000.00,
        "tax_amount": 100.00,
        "total_amount": 1100.00,
        "amount_due": 1100.00
    }

    sample_pdf_path = settings.BASE_DIR / "data" / "sample_invoices" / "invoice_001_normal.pdf"
    pdf_bytes = sample_pdf_path.read_bytes()

    files = {"file": ("invoice_001_normal.pdf", pdf_bytes, "application/pdf")}

    response = api_client.post("/api/v1/invoices/process", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["document_name"] == "invoice_001_normal.pdf"
    assert data["status"] in ["SUCCESS", "NEEDS_REVIEW"]
    assert data["database_invoice_id"] is not None


def test_list_and_manage_reviews(api_client):
    res = api_client.get("/api/v1/reviews")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_review_tasks_date_serialization(api_client):
    from datetime import date
    from app.database.connection import get_db

    db = next(app.dependency_overrides[get_db]())

    # 1. Seed invoice WITH dates
    inv1 = InvoiceModel(
        invoice_number="INV-DATE-001",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        total_amount=500.00,
        status="NEEDS_REVIEW"
    )
    db.add(inv1)
    db.flush()

    task1 = ReviewTaskModel(
        invoice_id=inv1.id,
        reason="PO_LINE_MISMATCH: Quantity mismatch",
        status="PENDING"
    )
    db.add(task1)

    # 2. Seed invoice WITHOUT dates
    inv2 = InvoiceModel(
        invoice_number="INV-NODATE-002",
        invoice_date=None,
        due_date=None,
        total_amount=250.00,
        status="NEEDS_REVIEW"
    )
    db.add(inv2)
    db.flush()

    task2 = ReviewTaskModel(
        invoice_id=inv2.id,
        reason="MISSING_REQUIRED_FIELD: Invoice date missing",
        status="PENDING"
    )
    db.add(task2)
    db.commit()

    res = api_client.get("/api/v1/reviews?status=PENDING")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 2

    task1_json = next(t for t in data if t["invoice_number"] == "INV-DATE-001")
    assert task1_json["invoice_date"] == "2026-08-15"
    assert task1_json["due_date"] == "2026-09-15"
    assert task1_json["raw_json"]["invoice_date"] == "2026-08-15"
    assert task1_json["raw_json"]["due_date"] == "2026-09-15"

    task2_json = next(t for t in data if t["invoice_number"] == "INV-NODATE-002")
    assert task2_json["invoice_date"] is None
    assert task2_json["due_date"] is None
    assert task2_json["raw_json"]["invoice_date"] is None
    assert task2_json["raw_json"]["due_date"] is None

