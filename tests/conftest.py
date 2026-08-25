import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base
from app.database.models import VendorModel, PurchaseOrderModel, PurchaseOrderLineItemModel


@pytest.fixture
def db_session():
    """In-memory SQLite session fixture with seeded master vendors & POs."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed vendor
    v1 = VendorModel(name="Acme Cloud Solutions Inc.", tax_id="US-88492019")
    v2 = VendorModel(name="Vertex Software Solutions", tax_id="US-10293847")
    session.add_all([v1, v2])
    session.flush()

    # Seed PO
    po1 = PurchaseOrderModel(
        po_number="PO-8842",
        vendor_id=v1.id,
        status="APPROVED",
        authorized_total=3300.0,
        remaining_balance=3300.0,
        currency="USD"
    )
    session.add(po1)
    session.flush()

    li1 = PurchaseOrderLineItemModel(
        purchase_order_id=po1.id,
        description="Enterprise Cloud Infrastructure Tier 3 Subscriptions",
        quantity=10.0,
        unit_price=300.0,
        line_total=3000.0
    )
    session.add(li1)
    session.flush()

    # Seed an existing invoice for duplicate testing
    from app.database.models import InvoiceModel
    inv1 = InvoiceModel(
        invoice_number="INV-2026-002",
        vendor_id=v2.id,
        status="NEEDS_REVIEW",
        total_amount=1620.0
    )
    session.add(inv1)
    session.commit()

    try:
        yield session
    finally:
        session.close()
