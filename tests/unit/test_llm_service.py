from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

from app.config import settings
from app.extraction.extractor import ExtractionResult
from app.llm.client import LLMClient
from app.schemas.invoice import ExtractedInvoice
from app.services.extraction_service import InvoiceExtractionService


@pytest.fixture
def mock_llm_json_response():
    return {
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-08-15",
        "due_date": "2026-09-15",
        "currency": "USD",
        "po_number": "PO-8842",
        "vendor": {
            "vendor_name": "Acme Cloud Solutions Inc.",
            "vendor_address": "100 Innovation Way, Suite 400, Tech City, CA 94016",
            "vendor_email": "billing@acmecloud.com",
            "vendor_phone": "+1 (555) 019-2831",
            "vendor_tax_id": "US-987654321"
        },
        "customer": {
            "customer_name": "Global Logistics Corp",
            "customer_address": "500 Supply Chain Blvd, Suite 100, Chicago, IL 60601",
            "customer_email": "ap@globallogistics.com"
        },
        "line_items": [
            {
                "description": "Enterprise Cloud Server Infrastructure - August 2026",
                "quantity": 1.0,
                "unit_price": 2500.00,
                "line_total": 2500.00
            },
            {
                "description": "Database Backup & Clustering Service",
                "quantity": 2.0,
                "unit_price": 250.00,
                "line_total": 500.00
            }
        ],
        "subtotal": 3000.00,
        "tax_amount": 300.00,
        "total_amount": 3300.00,
        "amount_due": 3300.00,
        "payment_info": {
            "payment_terms": "Net 30 Days"
        }
    }


def test_llm_client_unconfigured_api_key():
    client = LLMClient(api_key="")
    with pytest.raises(ValueError, match="LLM API Key is not configured"):
        client.extract_invoice_json("sample document text")


@patch("app.llm.client.OpenAI")
def test_llm_client_extract_json_success(mock_openai_cls, mock_llm_json_response):
    import json
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content=json.dumps(mock_llm_json_response)))
    ]
    mock_client_inst = MagicMock()
    mock_client_inst.chat.completions.create.return_value = mock_response
    mock_openai_cls.return_value = mock_client_inst

    client = LLMClient(api_key="test_api_key")
    result = client.extract_invoice_json("Test invoice document text")

    assert result["invoice_number"] == "INV-2026-001"
    assert result["vendor"]["vendor_name"] == "Acme Cloud Solutions Inc."
    mock_client_inst.chat.completions.create.assert_called_once()


@patch("app.services.extraction_service.LLMClient")
def test_extraction_service_process_document(mock_llm_client_cls, mock_llm_json_response):
    mock_llm_instance = MagicMock()
    mock_llm_instance.extract_invoice_json.return_value = mock_llm_json_response
    mock_llm_client_cls.return_value = mock_llm_instance

    service = InvoiceExtractionService(llm_client=mock_llm_instance)
    pdf_path = settings.BASE_DIR / "data" / "sample_invoices" / "invoice_001_normal.pdf"

    extracted_invoice, extraction_meta = service.process_document(pdf_path)

    assert isinstance(extracted_invoice, ExtractedInvoice)
    assert isinstance(extraction_meta, ExtractionResult)
    assert extracted_invoice.invoice_number == "INV-2026-001"
    assert extracted_invoice.vendor.vendor_name == "Acme Cloud Solutions Inc."
    assert extracted_invoice.total_amount == Decimal("3300.00")
    assert len(extracted_invoice.line_items) == 2
    assert extraction_meta.extraction_method == "native_pdf"
