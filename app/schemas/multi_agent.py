from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProcurementAssessment(BaseModel):
    """Structured assessment returned by Procurement Verification Agent."""
    status: str = Field(..., description="PASS, REVIEW, FAIL, or UNKNOWN")
    vendor_verified: bool = Field(False, description="True if vendor exists in master registry")
    po_verified: bool = Field(False, description="True if PO exists and is approved")
    po_match: bool = Field(False, description="True if invoice totals match authorized PO balance")
    line_match_status: str = Field("MATCH", description="MATCH, MISMATCH, NOT_APPLICABLE, or UNKNOWN")
    issues: List[str] = Field(default_factory=list, description="List of procurement compliance issues")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Supporting evidence data structures")
    recommended_action: str = Field("CONTINUE", description="CONTINUE, HUMAN_REVIEW, or REJECT")


class RiskAssessment(BaseModel):
    """Structured assessment returned by Financial Risk / Fraud Agent."""
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, or UNKNOWN")
    risk_score: float = Field(0.0, description="Risk score indicator from 0.0 (safe) to 1.0 (extreme risk)")
    flags: List[str] = Field(default_factory=list, description="Risk flags e.g. UNUSUAL_INVOICE_AMOUNT, DUPLICATE_SUSPECTED")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Empirical evidence from historical vendor data")
    recommended_action: str = Field("CONTINUE", description="CONTINUE, HUMAN_REVIEW, or REJECT")
    data_sufficiency: str = Field("SUFFICIENT", description="SUFFICIENT or INSUFFICIENT_DATA")


class AgentTrace(BaseModel):
    """Execution audit trace for individual specialized agents."""
    agent_name: str = Field(..., description="Name of the agent e.g. ProcurementAgent")
    agent_run_id: str = Field(..., description="Unique run identifier")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    iterations: int = Field(1, description="Number of Observe-Reason-Act iterations executed")
    tools_used: List[str] = Field(default_factory=list, description="List of tool names invoked")
    tool_results: List[Dict[str, Any]] = Field(default_factory=list, description="Executed tool outputs")
    final_assessment: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)


class MultiAgentInvoiceState(BaseModel):
    """Unified state context shared across multi-agent orchestrator."""
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    po_number: Optional[str] = None
    total_amount: float = 0.0
    
    procurement_assessment: Optional[ProcurementAssessment] = None
    risk_assessment: Optional[RiskAssessment] = None
    final_decision: Optional[Dict[str, Any]] = None
    agent_traces: List[AgentTrace] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class AnalyticsQuestionRequest(BaseModel):
    """Request payload for Data Analyst Assistant."""
    question: str = Field(..., min_length=3, description="Natural language question about AP business data")


class AnalyticsQuestionResponse(BaseModel):
    """Structured response returned by Data Analyst Assistant."""
    answer: str = Field(..., description="Natural language answer synthesized from read-only data")
    tools_used: List[str] = Field(default_factory=list, description="Controlled read-only tools executed")
    sources: List[str] = Field(default_factory=list, description="Database tables/entities queried")
    raw_data: Optional[Any] = Field(None, description="Structured query results")
