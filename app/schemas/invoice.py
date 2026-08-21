from datetime import date
from decimal import Decimal
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class FieldConfidence(BaseModel, Generic[T]):
    """Wrapper holding a field value alongside extraction confidence and source details."""
    value: Optional[T] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    source: Optional[str] = Field(default=None, description="Page or section where value was extracted")
    extraction_method: Optional[str] = Field(default=None, description="Extraction method used: native_pdf, ocr, or llm")


class VendorInfo(BaseModel):
    """Information regarding the seller / vendor / biller."""
    vendor_name: Optional[str] = Field(default=None, description="Legal or trade name of the vendor")
    vendor_address: Optional[str] = Field(default=None, description="Full street address of vendor")
    vendor_email: Optional[str] = Field(default=None, description="Contact email of vendor")
    vendor_phone: Optional[str] = Field(default=None, description="Contact phone number of vendor")
    vendor_tax_id: Optional[str] = Field(default=None, description="Tax Identification Number / VAT / GSTIN")
    vendor_registration_number: Optional[str] = Field(default=None, description="Business registration / CRN")


class CustomerInfo(BaseModel):
    """Information regarding the buyer / customer."""
    customer_name: Optional[str] = Field(default=None, description="Name of buying individual or organization")
    customer_address: Optional[str] = Field(default=None, description="Billing/shipping address of customer")
    customer_email: Optional[str] = Field(default=None, description="Customer contact email")
    customer_phone: Optional[str] = Field(default=None, description="Customer contact phone")
    customer_tax_id: Optional[str] = Field(default=None, description="Customer Tax ID / VAT / GSTIN")


class LineItem(BaseModel):
    """Detailed line item entries in the invoice."""
    description: str = Field(..., description="Description of product or service provided")
    product_code: Optional[str] = Field(default=None, description="Product code, SKU, or part number")
    sku: Optional[str] = Field(default=None, description="Stock Keeping Unit")
    quantity: Decimal = Field(default=Decimal("1.0"), description="Quantity of goods or services rendered")
    unit: Optional[str] = Field(default=None, description="Unit of measure (e.g. hrs, pcs, kg)")
    unit_price: Decimal = Field(default=Decimal("0.00"), description="Price per single unit")
    discount: Optional[Decimal] = Field(default=Decimal("0.00"), description="Discount amount applied to line item")
    tax_rate: Optional[Decimal] = Field(default=None, description="Tax percentage applied to line item (e.g. 18.0)")
    tax_amount: Optional[Decimal] = Field(default=Decimal("0.00"), description="Tax amount for this line item")
    line_total: Decimal = Field(default=Decimal("0.00"), description="Total cost for this line item")


class PaymentInformation(BaseModel):
    """Payment instructions and banking details."""
    payment_method: Optional[str] = Field(default=None, description="Method of payment (e.g., Bank Transfer, Credit Card)")
    payment_terms: Optional[str] = Field(default=None, description="Payment terms (e.g., Net 30, Due on Receipt)")
    bank_name: Optional[str] = Field(default=None, description="Vendor bank name")
    account_name: Optional[str] = Field(default=None, description="Bank account holder name")
    account_number: Optional[str] = Field(default=None, description="Bank account number or IBAN")
    ifsc_routing: Optional[str] = Field(default=None, description="IFSC code, ABA Routing number, or SWIFT/BIC")


class TaxBreakdown(BaseModel):
    """Detailed breakdown of taxes applied to the invoice."""
    taxable_amount: Optional[Decimal] = Field(default=None, description="Base amount subject to tax")
    tax_amount: Optional[Decimal] = Field(default=None, description="Total tax amount")
    tax_rate: Optional[Decimal] = Field(default=None, description="Overall tax percentage rate")
    cgst: Optional[Decimal] = Field(default=None, description="Central GST amount (if applicable)")
    sgst: Optional[Decimal] = Field(default=None, description="State GST amount (if applicable)")
    igst: Optional[Decimal] = Field(default=None, description="Integrated GST amount (if applicable)")
    vat: Optional[Decimal] = Field(default=None, description="Value Added Tax amount (if applicable)")


class ExtractedInvoice(BaseModel):
    """Complete structured invoice schema extracted from document."""

    # Primary Invoice Identification
    invoice_number: Optional[str] = Field(default=None, description="Unique invoice number identifier")
    invoice_date: Optional[date] = Field(default=None, description="Date invoice was issued (YYYY-MM-DD)")
    due_date: Optional[date] = Field(default=None, description="Payment due date (YYYY-MM-DD)")
    invoice_type: Optional[str] = Field(default="INVOICE", description="Type of document (e.g. INVOICE, CREDIT_NOTE, TAX_INVOICE)")
    reference_number: Optional[str] = Field(default=None, description="Reference or job number")

    # Purchase & Order Details
    po_number: Optional[str] = Field(default=None, description="Associated Purchase Order number")
    purchase_order_date: Optional[date] = Field(default=None, description="Date of Purchase Order (YYYY-MM-DD)")
    currency: Optional[str] = Field(default="USD", description="3-letter ISO currency code (e.g. USD, EUR, INR)")
    billing_address: Optional[str] = Field(default=None, description="Billing address if distinct from customer address")
    shipping_address: Optional[str] = Field(default=None, description="Shipping address if applicable")

    # Entity Information
    vendor: VendorInfo = Field(default_factory=VendorInfo, description="Vendor / Biller information")
    customer: CustomerInfo = Field(default_factory=CustomerInfo, description="Customer / Buyer information")

    # Line Items & Financial Totals
    line_items: List[LineItem] = Field(default_factory=list, description="List of invoice line items")
    tax_breakdown: Optional[TaxBreakdown] = Field(default=None, description="Tax details breakdown")
    
    subtotal: Optional[Decimal] = Field(default=None, description="Sum of line item totals before tax/discount")
    discount: Optional[Decimal] = Field(default=Decimal("0.00"), description="Total invoice discount amount")
    shipping_charge: Optional[Decimal] = Field(default=Decimal("0.00"), description="Shipping or freight fees")
    other_charges: Optional[Decimal] = Field(default=Decimal("0.00"), description="Miscellaneous fees")
    tax_amount: Optional[Decimal] = Field(default=Decimal("0.00"), description="Total tax amount")
    total_amount: Optional[Decimal] = Field(default=None, description="Grand total invoice amount")
    amount_paid: Optional[Decimal] = Field(default=Decimal("0.00"), description="Amount already paid")
    amount_due: Optional[Decimal] = Field(default=None, description="Remaining balance due")

    # Payment & Bank Details
    payment_info: Optional[PaymentInformation] = Field(default=None, description="Payment instructions and banking info")
