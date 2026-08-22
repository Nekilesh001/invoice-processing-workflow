import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.database.connection import get_engine, init_db, get_session_factory, get_db
from app.database.repositories.invoice_repository import InvoiceRepository
from app.database.repositories.purchase_order_repository import PurchaseOrderRepository


from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

@pytest.fixture
def api_test_db():
    import app.database.models
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()

    inv_repo = InvoiceRepository()
    v1 = inv_repo.get_or_create_vendor(session, "Acme Cloud Solutions Inc.", tax_id="US-88492019")
    v2 = inv_repo.get_or_create_vendor(session, "Vertex Software Solutions", tax_id="US-10293847")

    po_repo = PurchaseOrderRepository()
    po1 = po_repo.create(session, {
        "po_number": "PO-8842",
        "vendor_id": v1.id,
        "authorized_total": "3300.00",
        "remaining_balance": "3300.00",
        "status": "APPROVED"
    }, [
        {"description": "Cloud Infra", "quantity": 1.0, "unit_price": 3000.0, "line_total": 3000.0}
    ])

    po_repo.create(session, {
        "po_number": "PO-1001",
        "vendor_id": v2.id,
        "authorized_total": "1620.00",
        "remaining_balance": "720.00",
        "status": "APPROVED"
    })

    session.commit()

    def override_get_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    client = TestClient(fastapi_app)
    yield client, session, v1, po1
    fastapi_app.dependency_overrides.clear()
    session.close()


def test_list_vendors_api(api_test_db):
    client, session, v1, po1 = api_test_db
    response = client.get("/api/v1/vendors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    names = [v["name"] for v in data]
    assert "Acme Cloud Solutions Inc." in names


def test_list_vendors_search_api(api_test_db):
    client, session, v1, po1 = api_test_db
    response = client.get("/api/v1/vendors?search=Acme")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Acme Cloud Solutions Inc."


def test_get_vendor_detail_api(api_test_db):
    client, session, v1, po1 = api_test_db
    response = client.get(f"/api/v1/vendors/{v1.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == v1.id
    assert data["name"] == "Acme Cloud Solutions Inc."
    assert len(data["purchase_orders"]) >= 1


def test_get_vendor_detail_not_found(api_test_db):
    client, session, v1, po1 = api_test_db
    response = client.get("/api/v1/vendors/99999")
    assert response.status_code == 404


def test_list_purchase_orders_api(api_test_db):
    client, session, v1, po1 = api_test_db
    response = client.get("/api/v1/purchase-orders")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_list_purchase_orders_filter_api(api_test_db):
    client, session, v1, po1 = api_test_db
    response = client.get("/api/v1/purchase-orders?search=8842")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["po_number"] == "PO-8842"


def test_get_purchase_order_detail_api(api_test_db):
    client, session, v1, po1 = api_test_db
    response = client.get(f"/api/v1/purchase-orders/{po1.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["po_number"] == "PO-8842"
    assert data["vendor"]["name"] == "Acme Cloud Solutions Inc."
    assert len(data["line_items"]) == 1


def test_get_purchase_order_detail_not_found(api_test_db):
    client, session, v1, po1 = api_test_db
    response = client.get("/api/v1/purchase-orders/99999")
    assert response.status_code == 404
