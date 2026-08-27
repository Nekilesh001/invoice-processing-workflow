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
    1. Detects file type (PDF vs Image) via magic bytes and file extension.
    2. For PDFs: Attempts native PDF text extraction via PyMuPDF (`fitz`).
       Falls back to Tesseract OCR page-by-page if native text is absent/insufficient.
    3. For Images: Loads image via PIL and performs Tesseract OCR directly without PyMuPDF.
    """

    MIN_NATIVE_CHAR_THRESHOLD = 20  # Minimum character count to consider native text valid

    def __init__(self, tesseract_cmd: Optional[str] = None):
        cmd = tesseract_cmd or settings.TESSERACT_CMD
        if cmd and Path(cmd).exists():
            pytesseract.pytesseract.tesseract_cmd = cmd

    def _detect_file_type(self, file_bytes: bytes, file_name: str) -> str:
        ext = Path(file_name).suffix.lower()

        # Check magic bytes
        if file_bytes.startswith(b"%PDF"):
            return "pdf"
        if (
            file_bytes.startswith(b"\x89PNG")
            or file_bytes.startswith(b"\xff\xd8\xff")
            or file_bytes.startswith(b"\x49\x49")
            or file_bytes.startswith(b"\x4d\x4d")
            or (file_bytes.startswith(b"RIFF") and b"WEBP" in file_bytes[:16])
        ):
            return "image"

        # Check extension fallback
        if ext == ".pdf":
            return "pdf"
        if ext in [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".webp"]:
            return "image"

        return "unsupported"

    def extract(self, file_input: Union[str, Path, bytes], file_name: str = "document.pdf") -> ExtractionResult:
        """
        Extracts text from PDF or Image file path or raw bytes.
        Returns an ExtractionResult object with text and metadata.
        """
        start_time = time.perf_counter()

        if isinstance(file_input, (str, Path)):
            path = Path(file_input)
            if not path.exists():
                raise FileNotFoundError(f"Invoice document not found: {path}")
            file_name = path.name
            file_bytes = path.read_bytes()
        elif isinstance(file_input, bytes):
            file_bytes = file_input
        else:
            raise ValueError("file_input must be a file path (str/Path) or bytes.")

        if not file_bytes:
            raise ValueError(f"Document '{file_name}' is empty (0 bytes).")

        doc_type = self._detect_file_type(file_bytes, file_name)

        if doc_type == "pdf":
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
            except Exception as e:
                raise ValueError(f"Unsupported or corrupted PDF document '{file_name}': {str(e)}") from e

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
                    pix = page.get_pixmap(dpi=300)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    page_ocr_text = pytesseract.image_to_string(img)
                    ocr_text_pages.append(page_ocr_text)

                full_raw_text = "\n".join(ocr_text_pages)
                extraction_method = "ocr"
                ocr_applied = True

            doc.close()

        elif doc_type == "image":
            try:
                img = Image.open(io.BytesIO(file_bytes))
                page_count = getattr(img, "n_frames", 1)
                full_raw_text = pytesseract.image_to_string(img)
                extraction_method = "ocr"
                ocr_applied = True
            except Exception as e:
                raise ValueError(f"Unsupported or corrupted image file '{file_name}': {str(e)}") from e

        else:
            raise ValueError(f"Unsupported file type for extraction: '{file_name}'")

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
