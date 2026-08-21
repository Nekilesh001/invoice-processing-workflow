from datetime import datetime
from decimal import Decimal
from typing import List

from app.schemas.invoice import ExtractedInvoice
from app.schemas.processing import ValidationResult, ValidationRuleResult


class InvoiceValidator:
    """
    Deterministic business validation engine for extracted invoices.
    Applies math, completeness, date sanity, and logical consistency checks.
    """

    TOLERANCE = Decimal("0.01")  # Maximum allowed currency rounding variance

    def validate(self, invoice: ExtractedInvoice) -> ValidationResult:
        """
        Executes all validation rules against an ExtractedInvoice instance.
        Returns a ValidationResult object with errors and warnings.
        """
        errors: List[ValidationRuleResult] = []
        warnings: List[ValidationRuleResult] = []

        # Rule 1: Required Fields Completeness Check
        self._check_required_fields(invoice, errors)

        # Rule 2: Grand Total Calculation Arithmetic Check
        self._check_total_calculation(invoice, errors, warnings)

        # Rule 3: Line Items Sum vs Subtotal Check
        self._check_line_items_sum(invoice, errors, warnings)

        # Rule 4: Individual Line Item Math Check
        self._check_line_items_math(invoice, errors, warnings)

        # Rule 5: Date Sanity Check (Due Date >= Invoice Date)
        self._check_date_sanity(invoice, errors)

        # Rule 6: Non-Negative Financial Amounts Check
        self._check_non_negative_amounts(invoice, errors)

        # Rule 7: Amount Due vs Total Amount Check
        self._check_amount_due(invoice, errors)

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            checked_at=datetime.utcnow()
        )

    def _check_required_fields(self, invoice: ExtractedInvoice, errors: List[ValidationRuleResult]):
        required_map = {
            "vendor_name": invoice.vendor.vendor_name if invoice.vendor else None,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date,
            "due_date": invoice.due_date,
            "total_amount": invoice.total_amount,
        }

        missing_fields = [field for field, val in required_map.items() if val is None or (isinstance(val, str) and not val.strip())]

        if missing_fields:
            errors.append(
                ValidationRuleResult(
                    rule_name="required_fields_check",
                    passed=False,
                    message=f"Missing mandatory invoice fields: {', '.join(missing_fields)}.",
                    severity="error"
                )
            )

    def _check_total_calculation(self, invoice: ExtractedInvoice, errors: List[ValidationRuleResult], warnings: List[ValidationRuleResult]):
        if invoice.total_amount is None or invoice.subtotal is None:
            return  # Handled by required_fields_check

        subtotal = invoice.subtotal or Decimal("0.00")
        tax = invoice.tax_amount or Decimal("0.00")
        shipping = invoice.shipping_charge or Decimal("0.00")
        other = invoice.other_charges or Decimal("0.00")
        discount = invoice.discount or Decimal("0.00")

        expected_total = subtotal + tax + shipping + other - discount
        diff = abs(expected_total - invoice.total_amount)

        if diff > self.TOLERANCE:
            errors.append(
                ValidationRuleResult(
                    rule_name="total_calculation_check",
                    passed=False,
                    message=(
                        f"Invoice total arithmetic mismatch: Subtotal (${subtotal}) + Tax (${tax}) + Shipping (${shipping}) "
                        f"- Discount (${discount}) = ${expected_total:.2f}, but Total Amount claims ${invoice.total_amount:.2f} "
                        f"(difference of ${diff:.2f})."
                    ),
                    severity="error"
                )
            )

    def _check_line_items_sum(self, invoice: ExtractedInvoice, errors: List[ValidationRuleResult], warnings: List[ValidationRuleResult]):
        if not invoice.line_items or invoice.subtotal is None:
            return

        sum_line_totals = sum(item.line_total for item in invoice.line_items)
        diff = abs(sum_line_totals - invoice.subtotal)

        if diff > self.TOLERANCE:
            errors.append(
                ValidationRuleResult(
                    rule_name="line_items_sum_check",
                    passed=False,
                    message=f"Sum of line items (${sum_line_totals:.2f}) does not match subtotal (${invoice.subtotal:.2f}).",
                    severity="error"
                )
            )

    def _check_line_items_math(self, invoice: ExtractedInvoice, errors: List[ValidationRuleResult], warnings: List[ValidationRuleResult]):
        if not invoice.line_items:
            return

        for idx, item in enumerate(invoice.line_items, start=1):
            qty = item.quantity or Decimal("1.0")
            price = item.unit_price or Decimal("0.00")
            item_discount = item.discount or Decimal("0.00")
            item_tax = item.tax_amount or Decimal("0.00")

            expected_item_total = (qty * price) - item_discount + item_tax
            diff = abs(expected_item_total - item.line_total)

            if diff > self.TOLERANCE:
                warnings.append(
                    ValidationRuleResult(
                        rule_name="line_item_math_check",
                        passed=False,
                        message=(
                            f"Line item #{idx} ('{item.description}'): Qty ({qty}) * Price (${price:.2f}) = ${expected_item_total:.2f}, "
                            f"but line_total claims ${item.line_total:.2f}."
                        ),
                        severity="warning"
                    )
                )

    def _check_date_sanity(self, invoice: ExtractedInvoice, errors: List[ValidationRuleResult]):
        if invoice.invoice_date and invoice.due_date:
            if invoice.due_date < invoice.invoice_date:
                errors.append(
                    ValidationRuleResult(
                        rule_name="date_sanity_check",
                        passed=False,
                        message=f"Payment due_date ({invoice.due_date}) precedes invoice_date ({invoice.invoice_date}).",
                        severity="error"
                    )
                )

    def _check_non_negative_amounts(self, invoice: ExtractedInvoice, errors: List[ValidationRuleResult]):
        field_checks = [
            ("total_amount", invoice.total_amount),
            ("subtotal", invoice.subtotal),
            ("amount_due", invoice.amount_due),
        ]
        negative_fields = [name for name, val in field_checks if val is not None and val < Decimal("0.00")]

        if negative_fields:
            errors.append(
                ValidationRuleResult(
                    rule_name="non_negative_amounts_check",
                    passed=False,
                    message=f"Negative financial amounts detected in: {', '.join(negative_fields)}.",
                    severity="error"
                )
            )

    def _check_amount_due(self, invoice: ExtractedInvoice, errors: List[ValidationRuleResult]):
        if invoice.amount_due is not None and invoice.total_amount is not None:
            if invoice.amount_due > invoice.total_amount + self.TOLERANCE:
                errors.append(
                    ValidationRuleResult(
                        rule_name="amount_due_check",
                        passed=False,
                        message=f"Amount due (${invoice.amount_due:.2f}) exceeds total invoice amount (${invoice.total_amount:.2f}).",
                        severity="error"
                    )
                )
