from pathlib import Path
from typing import Optional, Union
from sqlalchemy.orm import Session

from app.database.connection import get_db, init_db
from app.database.repositories.invoice_repository import InvoiceRepository
from app.extraction.extractor import DocumentExtractor
from app.llm.client import LLMClient
from app.schemas.processing import ProcessingResult, ProcessingStatus
from app.validation.validator import InvoiceValidator


class InvoicePipelineRunner:
    """
    End-to-End Invoice Processing Workflow Orchestrator:
    Document -> Text (Native/OCR) -> LLM -> Pydantic Schema -> Validation -> SQL Database
    """

    def __init__(
        self,
        extractor: Optional[DocumentExtractor] = None,
        llm_client: Optional[LLMClient] = None,
        validator: Optional[InvoiceValidator] = None,
        repository: Optional[InvoiceRepository] = None,
    ):
        self.extractor = extractor or DocumentExtractor()
        self.llm_client = llm_client or LLMClient()
        self.validator = validator or InvoiceValidator()
        self.repository = repository or InvoiceRepository()

    def process_file(
        self, file_input: Union[str, Path, bytes], file_name: str = "document.pdf", db_session: Optional[Session] = None
    ) -> ProcessingResult:
        """
        Executes end-to-end processing pipeline for a single invoice document.
        """
        resolved_filename = Path(file_input).name if isinstance(file_input, (str, Path)) else file_name

        try:
            # Step 1: Document text extraction (PyMuPDF or Tesseract OCR)
            extraction_result = self.extractor.extract(file_input, file_name=resolved_filename)

            if not extraction_result.cleaned_text.strip():
                return ProcessingResult(
                    document_name=resolved_filename,
                    status=ProcessingStatus.FAILED,
                    extraction_method=extraction_result.extraction_method,
                    error_message=f"No readable text found in document '{resolved_filename}'."
                )

            # Step 2: LLM Structured Parsing
            raw_json_dict = self.llm_client.extract_invoice_json(extraction_result.cleaned_text)

            # Step 3: Pydantic Schema Validation
            from app.schemas.invoice import ExtractedInvoice
            extracted_invoice = ExtractedInvoice.model_validate(raw_json_dict)

            # Step 4: Business Rules Validation
            validation_result = self.validator.validate(extracted_invoice)

            # Step 5: Duplicate Check & Database Persistence
            def _persist(session: Session) -> ProcessingResult:
                # Check for duplicate vendor + invoice number
                vendor_name = extracted_invoice.vendor.vendor_name if extracted_invoice.vendor else None
                is_duplicate = self.repository.check_duplicate(
                    session, vendor_name=vendor_name, invoice_number=extracted_invoice.invoice_number
                )

                if is_duplicate:
                    status = ProcessingStatus.DUPLICATE_SUSPECTED
                elif validation_result.is_valid:
                    status = ProcessingStatus.SUCCESS
                else:
                    status = ProcessingStatus.NEEDS_REVIEW

                # Persist to database
                db_invoice = self.repository.save_invoice(
                    session=session,
                    extracted_invoice=extracted_invoice,
                    validation_result=validation_result,
                    source_filename=resolved_filename
                )

                review_id = db_invoice.review_tasks[0].id if db_invoice.review_tasks else None

                return ProcessingResult(
                    document_name=resolved_filename,
                    status=status,
                    extraction_method=extraction_result.extraction_method,
                    extracted_invoice=extracted_invoice,
                    validation_result=validation_result,
                    database_invoice_id=db_invoice.id,
                    review_task_id=review_id
                )

            if db_session:
                return _persist(db_session)
            else:
                with get_db() as session:
                    return _persist(session)

        except Exception as e:
            return ProcessingResult(
                document_name=resolved_filename,
                status=ProcessingStatus.FAILED,
                extraction_method="unknown",
                error_message=str(e)
            )
