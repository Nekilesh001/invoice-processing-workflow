from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InvoiceCounts(BaseModel):
    """Counts of invoices grouped by status."""
    total: int = Field(0, description="Total number of processed invoices")
    approved: int = Field(0, description="Number of approved invoices")
    human_review: int = Field(0, description="Number of invoices requiring human review")
    rejected: int = Field(0, description="Number of rejected invoices")
    processing: int = Field(0, description="Number of currently processing invoices")


class FinancialTotals(BaseModel):
    """Aggregate financial monetary totals in USD."""
    total_invoice_value: float = Field(0.0, description="Sum of total_amount for all invoices")
    approved_value: float = Field(0.0, description="Sum of total_amount for approved invoices")
    review_value: float = Field(0.0, description="Sum of total_amount for review invoices")
    rejected_value: float = Field(0.0, description="Sum of total_amount for rejected invoices")


class ReviewMetrics(BaseModel):
    """Metrics for human review queue."""
    pending_count: int = Field(0, description="Number of pending review tasks")


class VerificationIssue(BaseModel):
    """Aggregated verification issue / flag reason and count."""
    reason: str = Field(..., description="Verification flag reason")
    count: int = Field(0, description="Number of invoices flagged for this reason")


class RecentInvoiceItem(BaseModel):
    """Brief summary item for recent invoices table."""
    id: int
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    total_amount: Optional[float] = None
    po_number: Optional[str] = None
    status: str
    created_at: str


class RecentReviewItem(BaseModel):
    """Brief summary item for recent human review activity log."""
    id: int
    invoice_id: int
    invoice_number: Optional[str] = None
    action: str
    reviewer: str
    comment: Optional[str] = None
    created_at: str


class DashboardSummary(BaseModel):
    """Comprehensive Invoice Operations Dashboard summary schema."""
    invoice_counts: InvoiceCounts
    financial_totals: FinancialTotals
    review_metrics: ReviewMetrics
    verification_issues: List[VerificationIssue]
    recent_invoices: List[RecentInvoiceItem]
    recent_reviews: List[RecentReviewItem]
