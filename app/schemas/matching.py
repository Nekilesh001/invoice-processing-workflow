from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LineMatchStatus(str, Enum):
    MATCH = "MATCH"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    PRICE_MISMATCH = "PRICE_MISMATCH"
    DISCOUNT_MISMATCH = "DISCOUNT_MISMATCH"
    TAX_MISMATCH = "TAX_MISMATCH"
    TOTAL_MISMATCH = "TOTAL_MISMATCH"
    MISSING_FROM_PO = "MISSING_FROM_PO"
    MISSING_FROM_INVOICE = "MISSING_FROM_INVOICE"
    AMBIGUOUS_MATCH = "AMBIGUOUS_MATCH"


class POMatchStatus(str, Enum):
    MATCH = "MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    MISMATCH = "MISMATCH"
    AMBIGUOUS_MATCH = "AMBIGUOUS_MATCH"
    MISSING_PO = "MISSING_PO"
    INVALID_PO = "INVALID_PO"
    ERROR = "ERROR"


class LineMatchResult(BaseModel):
    """Structured line-item comparison result between an invoice line and a PO line."""
    invoice_line_id: Optional[int] = None
    po_line_id: Optional[int] = None
    invoice_description: Optional[str] = None
    po_description: Optional[str] = None
    product_code: Optional[str] = None
    
    invoice_quantity: Decimal = Decimal("0.0")
    po_quantity: Decimal = Decimal("0.0")
    quantity_difference: Decimal = Decimal("0.0")
    
    invoice_unit_price: Decimal = Decimal("0.0")
    po_unit_price: Decimal = Decimal("0.0")
    unit_price_difference: Decimal = Decimal("0.0")
    
    invoice_line_total: Decimal = Decimal("0.0")
    po_line_total: Decimal = Decimal("0.0")
    
    status: LineMatchStatus = LineMatchStatus.MATCH
    reasons: List[str] = Field(default_factory=list)


class InvoicePOMatchResult(BaseModel):
    """Overall deterministic comparison result between an Invoice and a Purchase Order."""
    is_match: bool = False
    overall_status: POMatchStatus = POMatchStatus.MISMATCH
    invoice_id: Optional[int] = None
    po_number: Optional[str] = None
    purchase_order_id: Optional[int] = None
    
    matched_line_count: int = 0
    mismatched_line_count: int = 0
    missing_from_invoice_count: int = 0
    missing_from_po_count: int = 0
    
    total_variance: float = 0.0
    currency: str = "USD"
    reasons: List[str] = Field(default_factory=list)
    line_results: List[LineMatchResult] = Field(default_factory=list)
