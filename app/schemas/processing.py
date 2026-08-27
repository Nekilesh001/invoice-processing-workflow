from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.invoice import ExtractedInvoice


class ProcessingStatus(str, Enum):
    SUCCESS = "SUCCESS"
    DUPLICATE_SUSPECTED = "DUPLICATE_SUSPECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FAILED = "FAILED"


class ValidationRuleResult(BaseModel):
    """Result of a single deterministic business rule validation check."""
    rule_name: str = Field(..., description="Name of validation rule (e.g. total_calculation_check)")
    passed: bool = Field(..., description="Whether check passed")
    message: str = Field(..., description="Human readable detail or error explanation")
    severity: str = Field(default="error", description="Severity tier: 'error' or 'warning'")


class ValidationResult(BaseModel):
    """Aggregated validation output for an extracted invoice."""
    is_valid: bool = Field(..., description="True if no blocking error rules failed")
    errors: List[ValidationRuleResult] = Field(default_factory=list, description="List of failed error rules")
    warnings: List[ValidationRuleResult] = Field(default_factory=list, description="List of failed warning rules")
    checked_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of validation run")


class ProcessingResult(BaseModel):
    """Top-level invoice processing pipeline result."""
    document_name: str = Field(..., description="Name of source invoice file")
    status: ProcessingStatus = Field(..., description="Overall processing status")
    extraction_method: str = Field(..., description="Document text extraction method used (native_pdf or ocr)")
    extracted_invoice: Optional[ExtractedInvoice] = Field(default=None, description="Extracted invoice model")
    validation_result: Optional[ValidationResult] = Field(default=None, description="Validation results")
    database_invoice_id: Optional[int] = Field(default=None, description="Database primary key if saved")
    review_task_id: Optional[int] = Field(default=None, description="Review task ID if human review is required")
    procurement_assessment: Optional[Dict[str, Any]] = Field(default=None, description="Structured procurement verification agent output")
    risk_assessment: Optional[Dict[str, Any]] = Field(default=None, description="Structured financial risk agent output")
    error_message: Optional[str] = Field(default=None, description="Pipeline error description if status is FAILED")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")
