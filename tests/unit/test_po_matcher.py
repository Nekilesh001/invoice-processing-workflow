import pytest
from decimal import Decimal
from datetime import date

from app.database.connection import get_engine, init_db, get_session_factory
from app.database.repositories.invoice_repository import InvoiceRepository
from app.database.repositories.purchase_order_repository import PurchaseOrderRepository
from app.validation.po_matcher import match_invoice_to_po
from app.schemas.matching import LineMatchStatus, POMatchStatus
from app.agents.tools import compare_invoice_to_purchase_order
from app.agents.invoice_agent import InvoiceAgent
from app.schemas.invoice import ExtractedInvoice, VendorInfo, LineItem
from app.validation.validator import InvoiceValidator


@pytest.fixture
def po_matching_db_session():
    """Provides test SQLite session populated with synthetic POs and line items."""
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()

    inv_repo = InvoiceRepository()
    v1 = inv_repo.get_or_create_vendor(session, "Acme Cloud Solutions Inc.", tax_id="US-88492019")

    po_repo = PurchaseOrderRepository()
    # Seed PO-8842 with 2 line items
    po_repo.create(session, {
        "po_number": "PO-8842",
        "vendor_id": v1.id,
        "authorized_total": "3300.00",
        "remaining_balance": "3300.00",
        "status": "APPROVED"
    }, [
        {
            "description": "Enterprise Cloud Server Subscriptions",
            "product_code": "SKU-CLOUD-100",
            "quantity": 10.0,
            "unit_price": 300.0,
            "line_total": 3000.0
        },
        {
            "description": "Dedicated IP Addon",
            "product_code": "SKU-IP-200",
            "quantity": 3.0,
            "unit_price": 100.0,
            "line_total": 300.0
        }
    ])

    session.commit()
    yield session
    session.close()


def test_case_1_perfect_line_match(po_matching_db_session):
    """Case 1 — Invoice line items match PO line items perfectly."""
    inv_items = [
        {"description": "Enterprise Cloud Server Subscriptions", "product_code": "SKU-CLOUD-100", "quantity": 10.0, "unit_price": 300.0, "line_total": 3000.0},
        {"description": "Dedicated IP Addon", "product_code": "SKU-IP-200", "quantity": 3.0, "unit_price": 100.0, "line_total": 300.0}
    ]
    res = compare_invoice_to_purchase_order("PO-8842", inv_items, session=po_matching_db_session)
    assert res["is_match"] is True
    assert res["overall_status"] == "MATCH"
    assert res["matched_line_count"] == 2
    assert res["mismatched_line_count"] == 0


def test_case_2_quantity_mismatch(po_matching_db_session):
    """Case 2 — Invoice claims 15 units instead of 10 units authorized on PO."""
    inv_items = [
        {"description": "Enterprise Cloud Server Subscriptions", "product_code": "SKU-CLOUD-100", "quantity": 15.0, "unit_price": 300.0, "line_total": 4500.0},
        {"description": "Dedicated IP Addon", "product_code": "SKU-IP-200", "quantity": 3.0, "unit_price": 100.0, "line_total": 300.0}
    ]
    res = compare_invoice_to_purchase_order("PO-8842", inv_items, session=po_matching_db_session)
    assert res["is_match"] is False
    assert res["overall_status"] == "PARTIAL_MATCH"
    assert res["mismatched_line_count"] == 1
    assert "Quantity mismatch" in res["reasons"][0]


def test_case_3_unit_price_mismatch(po_matching_db_session):
    """Case 3 — Invoice claims unit price $400 instead of $300 authorized on PO."""
    inv_items = [
        {"description": "Enterprise Cloud Server Subscriptions", "product_code": "SKU-CLOUD-100", "quantity": 10.0, "unit_price": 400.0, "line_total": 4000.0}
    ]
    res = compare_invoice_to_purchase_order("PO-8842", inv_items, session=po_matching_db_session)
    assert res["is_match"] is False
    assert "Unit price mismatch" in res["reasons"][0]


def test_case_4_invoice_line_missing_from_po(po_matching_db_session):
    """Case 4 — Invoice contains extra unapproved item missing from PO."""
    inv_items = [
        {"description": "Enterprise Cloud Server Subscriptions", "product_code": "SKU-CLOUD-100", "quantity": 10.0, "unit_price": 300.0, "line_total": 3000.0},
        {"description": "Unapproved Luxury Espresso Machine", "product_code": "SKU-COFFEE-99", "quantity": 1.0, "unit_price": 500.0, "line_total": 500.0}
    ]
    res = compare_invoice_to_purchase_order("PO-8842", inv_items, session=po_matching_db_session)
    assert res["is_match"] is False
    assert res["missing_from_po_count"] == 1
    assert "missing from Purchase Order" in res["reasons"][0]


def test_case_5_po_line_missing_from_invoice(po_matching_db_session):
    """Case 5 — Invoice bills only 1 of 2 authorized PO lines."""
    inv_items = [
        {"description": "Enterprise Cloud Server Subscriptions", "product_code": "SKU-CLOUD-100", "quantity": 10.0, "unit_price": 300.0, "line_total": 3000.0}
    ]
    res = compare_invoice_to_purchase_order("PO-8842", inv_items, session=po_matching_db_session)
    assert res["is_match"] is False
    assert res["missing_from_invoice_count"] == 1
    assert "missing from invoice" in res["reasons"][0]


def test_case_6_ambiguous_matching_detection():
    """Case 6 — Multiple candidate PO lines match invoice item ambiguously."""
    inv_items = [{"description": "Cloud Service", "quantity": 1.0, "unit_price": 100.0, "line_total": 100.0}]
    po_items = [
        {"description": "Cloud Service Tier A", "quantity": 1.0, "unit_price": 100.0, "line_total": 100.0},
        {"description": "Cloud Service Tier B", "quantity": 1.0, "unit_price": 100.0, "line_total": 100.0}
    ]
    match_res = match_invoice_to_po(inv_items, po_items)
    assert match_res.is_match is False
    assert match_res.line_results[0].status == LineMatchStatus.AMBIGUOUS_MATCH


def test_case_7_single_po_line_uniqueness():
    """Case 7 — Proves that a single PO line cannot be matched by two invoice lines."""
    inv_items = [
        {"description": "Dedicated IP Addon", "product_code": "SKU-IP-200", "quantity": 3.0, "unit_price": 100.0, "line_total": 300.0},
        {"description": "Dedicated IP Addon", "product_code": "SKU-IP-200", "quantity": 3.0, "unit_price": 100.0, "line_total": 300.0}
    ]
    po_items = [
        {"description": "Dedicated IP Addon", "product_code": "SKU-IP-200", "quantity": 3.0, "unit_price": 100.0, "line_total": 300.0}
    ]
    match_res = match_invoice_to_po(inv_items, po_items)
    assert match_res.is_match is False
    assert match_res.matched_line_count == 1
    assert match_res.missing_from_po_count == 1


def test_case_8_header_total_matches_but_lines_mismatch(po_matching_db_session):
    """Case 10 — Header totals match ($3300) but line quantities differ -> HUMAN_REVIEW."""
    agent = InvoiceAgent()
    validator = InvoiceValidator()

    # Total is $3300 ($3000 + $300), but item quantities differ (5 units @ $600 instead of 10 @ $300)
    invoice = ExtractedInvoice(
        invoice_number="INV-2026-QTY-MISMATCH",
        invoice_date=date(2026, 8, 15),
        due_date=date(2026, 9, 15),
        po_number="PO-8842",
        vendor=VendorInfo(vendor_name="Acme Cloud Solutions Inc."),
        line_items=[
            LineItem(description="Enterprise Cloud Server Subscriptions", quantity=Decimal("5.0"), unit_price=Decimal("600.00"), line_total=Decimal("3000.00")),
            LineItem(description="Dedicated IP Addon", quantity=Decimal("3.0"), unit_price=Decimal("100.00"), line_total=Decimal("300.00"))
        ],
        subtotal=Decimal("3300.00"),
        total_amount=Decimal("3300.00")
    )
    val_res = validator.validate(invoice)
    decision = agent.evaluate_and_decide(invoice, val_res, db_session=po_matching_db_session)

    assert decision.action == "HUMAN_REVIEW"
    assert "PO_LINE_MISMATCH" in decision.reason
