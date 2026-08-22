import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.database.connection import init_db, get_session_factory, get_db
from app.database.models import UserModel
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


@pytest.fixture
def auth_test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()

    # Seed users
    admin_pwd = hash_password("Admin@123")
    user_admin = UserModel(username="test_admin", email="admin@test.com", password_hash=admin_pwd, role="ADMIN", is_active=True)
    user_reviewer = UserModel(username="test_reviewer", email="reviewer@test.com", password_hash=admin_pwd, role="REVIEWER", is_active=True)
    user_viewer = UserModel(username="test_viewer", email="viewer@test.com", password_hash=admin_pwd, role="VIEWER", is_active=True)

    session.add_all([user_admin, user_reviewer, user_viewer])
    session.commit()

    def override_get_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    client = TestClient(fastapi_app)
    yield client, session, user_admin, user_reviewer, user_viewer
    fastapi_app.dependency_overrides.clear()
    session.close()


def test_password_hashing_and_verification():
    raw_pass = "SecurePass@2026"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPass", hashed) is False


def test_jwt_token_creation_and_decoding():
    payload = {"sub": "42", "username": "johndoe", "role": "REVIEWER"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)

    assert decoded is not None
    assert decoded["sub"] == "42"
    assert decoded["username"] == "johndoe"
    assert decoded["role"] == "REVIEWER"


def test_login_api_success(auth_test_db):
    client, session, _, _, _ = auth_test_db

    response = client.post("/api/v1/auth/login", json={
        "username_or_email": "test_admin",
        "password": "Admin@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "test_admin"
    assert data["user"]["role"] == "ADMIN"


def test_login_api_invalid_credentials(auth_test_db):
    client, session, _, _, _ = auth_test_db

    response = client.post("/api/v1/auth/login", json={
        "username_or_email": "test_admin",
        "password": "WrongPassword"
    })
    assert response.status_code == 401


def test_auth_me_protected_endpoint(auth_test_db):
    client, session, _, user_reviewer, _ = auth_test_db

    token = create_access_token({"sub": str(user_reviewer.id), "role": user_reviewer.role})

    # Unauthenticated request -> 401
    unauth_res = client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401

    # Authenticated request -> 200
    auth_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert auth_res.status_code == 200
    assert auth_res.json()["username"] == "test_reviewer"
    assert auth_res.json()["role"] == "REVIEWER"


def test_rbac_role_permission_enforcement(auth_test_db):
    client, session, _, user_reviewer, user_viewer = auth_test_db

    # Create dummy review task
    from app.database.models import InvoiceModel, ReviewTaskModel
    inv = InvoiceModel(invoice_number="INV-RBAC-01", status="NEEDS_REVIEW")
    session.add(inv)
    session.flush()
    task = ReviewTaskModel(invoice_id=inv.id, reason="TEST_FLAG", status="PENDING")
    session.add(task)
    session.commit()

    token_viewer = create_access_token({"sub": str(user_viewer.id), "role": user_viewer.role})
    token_reviewer = create_access_token({"sub": str(user_reviewer.id), "role": user_reviewer.role})

    # Viewer role attempting approval -> 403 Forbidden
    res_viewer = client.post(f"/api/v1/reviews/{task.id}/approve", headers={"Authorization": f"Bearer {token_viewer}"})
    assert res_viewer.status_code == 403

    # Reviewer role approving -> 200 OK
    res_reviewer = client.post(f"/api/v1/reviews/{task.id}/approve", headers={"Authorization": f"Bearer {token_reviewer}"})
    assert res_reviewer.status_code == 200
    assert res_reviewer.json()["action"] == "APPROVED"
    assert res_reviewer.json()["reviewer"] == "test_reviewer"
