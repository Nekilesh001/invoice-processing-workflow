from pathlib import Path
import pymupdf as fitz  # PyMuPDF
from app.config import settings


def test_synthetic_invoices_exist_and_readable():
    """Verify that synthetic invoice PDFs exist and text can be extracted via PyMuPDF."""
    sample_dir = settings.BASE_DIR / "data" / "sample_invoices"
    expected_files = [
        "invoice_001_normal.pdf",
        "invoice_002_missing_due_date.pdf",
        "invoice_003_missing_vendor.pdf",
        "invoice_004_invalid_total.pdf"
    ]

    for filename in expected_files:
        pdf_path = sample_dir / filename
        assert pdf_path.exists(), f"Synthetic invoice file missing: {pdf_path}"

        doc = fitz.open(pdf_path)
        assert len(doc) > 0, f"PDF file {filename} has no pages."
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

        assert len(text.strip()) > 0, f"Extracted text from {filename} is empty."


def test_invoice_001_content():
    """Verify text contents of normal synthetic invoice."""
    pdf_path = settings.BASE_DIR / "data" / "sample_invoices" / "invoice_001_normal.pdf"
    doc = fitz.open(pdf_path)
    text = doc[0].get_text()
    doc.close()

    assert "Acme Cloud Solutions" in text
    assert "INV-2026-001" in text
    assert "3,300.00" in text
