import io
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import pymupdf as fitz  # PyMuPDF
from PIL import Image
import pytesseract

from app.config import settings
from app.extraction.cleaner import clean_extracted_text


@dataclass
class ExtractionResult:
    """Dataclass holding document extraction results and performance metadata."""
    raw_text: str
    cleaned_text: str
    extraction_method: str  # "native_pdf" or "ocr"
    ocr_applied: bool
    page_count: int
    character_count: int
    extraction_time_ms: float
    file_name: str


class DocumentExtractor:
    """
    Document text extraction pipeline:
    1. Attempts native PDF text extraction via PyMuPDF (`fitz`).
    2. Inspects extracted text length/quality.
    3. Falls back to Tesseract OCR page-by-page if native text is absent/insufficient (scanned document).
    """

    MIN_NATIVE_CHAR_THRESHOLD = 20  # Minimum character count to consider native text valid

    def __init__(self, tesseract_cmd: Optional[str] = None):
        cmd = tesseract_cmd or settings.TESSERACT_CMD
        if cmd and Path(cmd).exists():
            pytesseract.pytesseract.tesseract_cmd = cmd

    def extract(self, file_input: Union[str, Path, bytes], file_name: str = "document.pdf") -> ExtractionResult:
        """
        Extracts text from PDF file path or raw bytes.
        Returns an ExtractionResult object with text and metadata.
        """
        start_time = time.perf_counter()

        if isinstance(file_input, (str, Path)):
            path = Path(file_input)
            if not path.exists():
                raise FileNotFoundError(f"Invoice document not found: {path}")
            file_name = path.name
            doc = fitz.open(path)
        elif isinstance(file_input, bytes):
            doc = fitz.open(stream=file_input, filetype="pdf")
        else:
            raise ValueError("file_input must be a file path (str/Path) or bytes.")

        page_count = len(doc)
        if page_count == 0:
            doc.close()
            raise ValueError(f"Document '{file_name}' contains no pages.")

        # Step 1: Attempt native text extraction
        native_text_pages = []
        total_native_chars = 0
        for page in doc:
            page_text = page.get_text()
            native_text_pages.append(page_text)
            total_native_chars += len(page_text.strip())

        full_raw_text = "\n".join(native_text_pages)

        # Step 2: Evaluate native text quality
        if total_native_chars >= self.MIN_NATIVE_CHAR_THRESHOLD:
            extraction_method = "native_pdf"
            ocr_applied = False
        else:
            # Step 3: Native text missing or scanned document -> Fallback to Tesseract OCR
            ocr_text_pages = []
            for page in doc:
                # Render page at 300 DPI for optimal OCR accuracy
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                page_ocr_text = pytesseract.image_to_string(img)
                ocr_text_pages.append(page_ocr_text)

            full_raw_text = "\n".join(ocr_text_pages)
            extraction_method = "ocr"
            ocr_applied = True

        doc.close()

        cleaned_text = clean_extracted_text(full_raw_text)
        end_time = time.perf_counter()
        duration_ms = round((end_time - start_time) * 1000, 2)

        return ExtractionResult(
            raw_text=full_raw_text,
            cleaned_text=cleaned_text,
            extraction_method=extraction_method,
            ocr_applied=ocr_applied,
            page_count=page_count,
            character_count=len(cleaned_text),
            extraction_time_ms=duration_ms,
            file_name=file_name
        )
