from pathlib import Path
from typing import Optional, Tuple, Union
from pydantic import ValidationError

from app.extraction.extractor import DocumentExtractor, ExtractionResult
from app.llm.client import LLMClient
from app.schemas.invoice import ExtractedInvoice


class InvoiceExtractionService:
    """
    End-to-end Invoice Extraction Pipeline Service:
    1. Extracts raw/cleaned text from PDF or Image document (using native extraction or OCR fallback).
    2. Invokes LLM via OpenAI-compatible API to parse text into structured JSON.
    3. Validates JSON payload against Pydantic ExtractedInvoice model.
    """

    def __init__(
        self,
        document_extractor: Optional[DocumentExtractor] = None,
        llm_client: Optional[LLMClient] = None,
    ):
        self.extractor = document_extractor or DocumentExtractor()
        self.llm_client = llm_client or LLMClient()

    def process_document(
        self, file_input: Union[str, Path, bytes], file_name: str = "document.pdf"
    ) -> Tuple[ExtractedInvoice, ExtractionResult]:
        """
        Executes document text extraction and structured LLM parsing.
        Returns a tuple of (ExtractedInvoice, ExtractionResult).
        """
        # Step 1: Extract document text
        extraction_result = self.extractor.extract(file_input, file_name=file_name)

        if not extraction_result.cleaned_text.strip():
            raise ValueError(f"No readable text found in document '{file_name}'.")

        # Step 2: Query LLM for structured JSON
        raw_json_dict = self.llm_client.extract_invoice_json(
            extraction_result.cleaned_text
        )

        # Step 3: Validate into Pydantic ExtractedInvoice model
        try:
            extracted_invoice = ExtractedInvoice.model_validate(raw_json_dict)
        except ValidationError as e:
            raise ValueError(f"LLM JSON response failed Pydantic schema validation: {str(e)}") from e

        return extracted_invoice, extraction_result
