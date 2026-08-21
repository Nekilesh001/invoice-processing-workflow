from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.invoice import ExtractedInvoice
from app.schemas.processing import ValidationResult


class AgentDecisionSchema(BaseModel):
    """Structured Pydantic schema for final LLM Agent decisions."""
    decision: str = Field(..., description="Action decision: AUTO_PROCESS or HUMAN_REVIEW")
    reason: str = Field(..., description="Detailed rationale explaining agent decision")
    requires_human_review: bool = Field(default=False, description="Flag indicating human review escalation")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Agent confidence score")


@dataclass
class AgentState:
    """Observable agent state object tracking loop history, tool executions, and state variables."""
    extracted_invoice: ExtractedInvoice
    validation_result: ValidationResult
    messages: List[Dict[str, Any]] = field(default_factory=list)
    executed_tools: List[Dict[str, Any]] = field(default_factory=list)
    iteration_count: int = 0
    max_iterations: int = 5
    vendor_verified: bool = False
    po_verified: bool = False
    duplicate_checked: bool = False
    final_decision: Optional[AgentDecisionSchema] = None
