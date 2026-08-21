"""
Document Extraction Module.
Handles native PDF extraction, scanned document detection, and Tesseract OCR fallback.
"""

from app.extraction.cleaner import clean_extracted_text
from app.extraction.extractor import DocumentExtractor, ExtractionResult

__all__ = ["clean_extracted_text", "DocumentExtractor", "ExtractionResult"]
