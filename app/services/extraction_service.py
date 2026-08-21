from pathlib import Path
from typing import Optional, Tuple, Union
from pydantic import ValidationError

from app.extraction.extractor import DocumentExtractor, ExtractionResult
from app.llm.client import LLMClient
from app.schemas.invoice import ExtractedInvoice
from app.schemas.processing import ProcessingResult, ProcessingStatus
from app.validation.validator import InvoiceValidator


class InvoiceExtractionService:
    """
    End-to-end Invoice Extraction & Validation Pipeline Service:
    1. Extracts raw/cleaned text from PDF or Image document (using native extraction or OCR fallback).
    2. Invokes LLM via OpenAI-compatible API to parse text into structured JSON.
    3. Validates JSON payload against Pydantic ExtractedInvoice model.
    4. Executes deterministic business rules validation.
    """

    def __init__(
        self,
        document_extractor: Optional[DocumentExtractor] = None,
        llm_client: Optional[LLMClient] = None,
        validator: Optional[InvoiceValidator] = None,
    ):
        self.extractor = document_extractor or DocumentExtractor()
        self.llm_client = llm_client or LLMClient()
        self.validator = validator or InvoiceValidator()

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

    def process_and_validate(
        self, file_input: Union[str, Path, bytes], file_name: str = "document.pdf"
    ) -> ProcessingResult:
        """
        Runs complete pipeline: extraction -> LLM parsing -> business validation -> status determination.
        """
        try:
            extracted_invoice, extraction_result = self.process_document(
                file_input, file_name=file_name
            )

            validation_result = self.validator.validate(extracted_invoice)
            status = (
                ProcessingStatus.SUCCESS
                if validation_result.is_valid
                else ProcessingStatus.NEEDS_REVIEW
            )

            return ProcessingResult(
                document_name=extraction_result.file_name,
                status=status,
                extraction_method=extraction_result.extraction_method,
                extracted_invoice=extracted_invoice,
                validation_result=validation_result,
            )

        except Exception as e:
            return ProcessingResult(
                document_name=file_name if isinstance(file_name, str) else "document.pdf",
                status=ProcessingStatus.FAILED,
                extraction_method="unknown",
                error_message=str(e),
            )
