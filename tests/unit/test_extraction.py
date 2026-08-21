import pytest
from pathlib import Path
from app.config import settings
from app.extraction.cleaner import clean_extracted_text
from app.extraction.extractor import DocumentExtractor, ExtractionResult


def test_clean_extracted_text():
    raw = "  Invoice   #123 \r\n\r\n\r\n  Total:   $100.00 \x00\x07  "
    cleaned = clean_extracted_text(raw)
    assert "Invoice #123" in cleaned
    assert "Total: $100.00" in cleaned
    assert "\x00" not in cleaned


def test_native_pdf_extraction():
    extractor = DocumentExtractor()
    pdf_path = settings.BASE_DIR / "data" / "sample_invoices" / "invoice_001_normal.pdf"
    
    result = extractor.extract(pdf_path)
    
    assert isinstance(result, ExtractionResult)
    assert result.extraction_method == "native_pdf"
    assert result.ocr_applied is False
    assert result.page_count == 1
    assert "Acme Cloud Solutions" in result.cleaned_text
    assert "INV-2026-001" in result.cleaned_text
    assert result.character_count > 50
    assert result.extraction_time_ms > 0


def test_scanned_pdf_ocr_fallback():
    extractor = DocumentExtractor()
    pdf_path = settings.BASE_DIR / "data" / "sample_invoices" / "invoice_006_scanned_invoice.pdf"
    
    result = extractor.extract(pdf_path)
    
    assert isinstance(result, ExtractionResult)
    assert result.extraction_method == "ocr"
    assert result.ocr_applied is True
    assert result.page_count == 1
    assert "SCANNED INVOICE" in result.cleaned_text or "INV-2026-006" in result.cleaned_text
    assert result.character_count > 30


def test_nonexistent_file_handling():
    extractor = DocumentExtractor()
    fake_path = settings.BASE_DIR / "data" / "sample_invoices" / "nonexistent.pdf"
    
    with pytest.raises(FileNotFoundError):
        extractor.extract(fake_path)
