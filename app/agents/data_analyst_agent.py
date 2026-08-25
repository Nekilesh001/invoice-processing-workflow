import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.analyst_tools import (
    get_financial_summary,
    get_invoice_exceptions,
    get_invoice_summary,
    get_purchase_order_summary,
    get_review_queue_summary,
    get_vendor_invoice_summary,
)
from app.llm.client import LLMClient
from app.schemas.multi_agent import AnalyticsQuestionResponse

logger = logging.getLogger(__name__)


class InvoiceDataAnalystAgent:
    """
    Invoice Data Analyst Agent:
    Separate business intelligence assistant answering natural-language queries
    about accounts payable metrics, vendor statistics, PO balances, and review queues.
    Operates strictly via controlled, read-only repository tools.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.tool_functions = {
            "get_invoice_summary": get_invoice_summary,
            "get_financial_summary": get_financial_summary,
            "get_vendor_invoice_summary": get_vendor_invoice_summary,
            "get_purchase_order_summary": get_purchase_order_summary,
            "get_review_queue_summary": get_review_queue_summary,
            "get_invoice_exceptions": get_invoice_exceptions,
        }

    def answer_question(self, question: str, session: Session) -> AnalyticsQuestionResponse:
        """
        Executes deterministic routing / tool invocation to gather structured data,
        then synthesizes a natural language answer.
        """
        if not question or not question.strip():
            return AnalyticsQuestionResponse(
                answer="Please provide a valid question regarding accounts payable data.",
                tools_used=[],
                sources=[]
            )

        q_lower = question.strip().lower()
        tools_executed = []
        sources = []
        raw_data = {}

        # Intelligent tool selection based on intent
        if any(term in q_lower for term in ["pending review", "review queue", "review task", "exception"]):
            tools_executed.append("get_review_queue_summary")
            sources.append("review_tasks")
            raw_data["review_queue"] = get_review_queue_summary(session)

            tools_executed.append("get_invoice_exceptions")
            sources.append("invoices")
            raw_data["exceptions"] = get_invoice_exceptions(session)

        if any(term in q_lower for term in ["vendor", "supplier", "biller"]):
            tools_executed.append("get_vendor_invoice_summary")
            sources.append("vendors")
            raw_data["vendor_summary"] = get_vendor_invoice_summary(session)

        if any(term in q_lower for term in ["purchase order", "po ", "balance"]):
            tools_executed.append("get_purchase_order_summary")
            sources.append("purchase_orders")
            raw_data["po_summary"] = get_purchase_order_summary(session)

        if any(term in q_lower for term in ["financial", "spend", "rejected", "approved", "volume", "total", "count", "how many"]):
            if "get_invoice_summary" not in tools_executed:
                tools_executed.append("get_invoice_summary")
                sources.append("invoices")
                raw_data["invoice_summary"] = get_invoice_summary(session)

            if "get_financial_summary" not in tools_executed:
                tools_executed.append("get_financial_summary")
                raw_data["financial_summary"] = get_financial_summary(session)

        # Fallback tool if none matched
        if not tools_executed:
            tools_executed.append("get_invoice_summary")
            sources.append("invoices")
            raw_data["invoice_summary"] = get_invoice_summary(session)

        # Synthesize natural language answer using LLM or structured formatter
        answer_text = self._synthesize_answer(question, raw_data)

        return AnalyticsQuestionResponse(
            answer=answer_text,
            tools_used=tools_executed,
            sources=list(set(sources)),
            raw_data=raw_data
        )

    def _synthesize_answer(self, question: str, raw_data: Dict[str, Any]) -> str:
        """Synthesizes a concise natural language response from gathered read-only metrics."""
        try:
            prompt = (
                f"User Question: '{question}'\n\n"
                f"Retrieved Read-Only Business Data:\n{raw_data}\n\n"
                f"Instructions: Answer the user's question concisely using ONLY the provided business data. "
                f"Do not hallucinate numbers. Do not reveal raw SQL or system keys."
            )
            messages = [
                {"role": "system", "content": "You are a professional Accounts Payable Data Analyst Assistant."},
                {"role": "user", "content": prompt}
            ]
            response = self.llm_client.chat_completion(messages, temperature=0.1)
            if response and response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"LLM synthesis failed ({e}), using deterministic formatter.")

        # Deterministic formatting fallback
        parts = []
        if "review_queue" in raw_data:
            pending = raw_data["review_queue"].get("pending_review_tasks_count", 0)
            parts.append(f"There are currently {pending} invoice(s) pending in the review queue.")

        if "vendor_summary" in raw_data and raw_data["vendor_summary"]:
            top_v = raw_data["vendor_summary"][0]
            parts.append(f"Top vendor by invoice volume is '{top_v['vendor_name']}' with {top_v['invoice_count']} invoice(s) totaling ${top_v['total_invoice_value']:,.2f}.")

        if "invoice_summary" in raw_data:
            inv = raw_data["invoice_summary"]
            parts.append(f"System has recorded {inv['total_invoices']} total invoice(s) (${inv['total_monetary_amount']:,.2f} total monetary volume), with {inv['approved_invoices']} approved, {inv['needs_review_invoices']} requiring review, and {inv['rejected_invoices']} rejected.")

        if "po_summary" in raw_data:
            po = raw_data["po_summary"]
            parts.append(f"Master PO database contains {po['total_purchase_orders']} purchase order(s) with total authorized value of ${po['total_authorized_amount']:,.2f} and ${po['total_remaining_balance']:,.2f} remaining balance.")

        return " ".join(parts) if parts else "I could not determine that from the available data."
