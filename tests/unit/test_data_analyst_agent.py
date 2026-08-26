import pytest
from app.agents.data_analyst_agent import InvoiceDataAnalystAgent
from app.agents.analyst_tools import (
    get_financial_summary,
    get_invoice_summary,
    get_purchase_order_summary,
    get_review_queue_summary,
    get_vendor_invoice_summary,
)


def test_analyst_tools(db_session):
    inv_sum = get_invoice_summary(db_session)
    assert "total_invoices" in inv_sum

    fin_sum = get_financial_summary(db_session)
    assert "total_financial_volume" in fin_sum

    po_sum = get_purchase_order_summary(db_session)
    assert "total_purchase_orders" in po_sum

    rq_sum = get_review_queue_summary(db_session)
    assert "pending_review_tasks_count" in rq_sum

    v_sum = get_vendor_invoice_summary(db_session)
    assert isinstance(v_sum, list)


def test_data_analyst_agent_q_and_a(db_session):
    agent = InvoiceDataAnalystAgent()
    resp = agent.answer_question("How many invoices are pending review?", session=db_session)
    assert resp.answer is not None
    assert len(resp.answer) > 5
    assert "get_review_queue_summary" in resp.tools_used


def test_data_analyst_agent_vendor_query(db_session):
    agent = InvoiceDataAnalystAgent()
    resp = agent.answer_question("Which vendor has the highest invoice volume?", session=db_session)
    assert resp.answer is not None
    assert "get_vendor_invoice_summary" in resp.tools_used
