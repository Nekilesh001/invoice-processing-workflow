import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import InvoiceModel, VendorModel, InvoiceLineItemModel

logger = logging.getLogger(__name__)


def get_vendor_invoice_history(vendor_name: Optional[str], session: Optional[Session] = None) -> Dict[str, Any]:
    """
    Risk Agent Tool: Retrieves historical invoice statistics for a vendor from MySQL.
    Read-only query returning invoice count, average invoice amount, min/max amounts, and recent status counts.
    """
    if not vendor_name or not vendor_name.strip():
        return {
            "vendor_name": vendor_name,
            "data_sufficiency": "INSUFFICIENT_DATA",
            "historical_count": 0,
            "message": "Vendor name was not provided."
        }

    clean_name = vendor_name.strip()
    if not session:
        return {
            "vendor_name": clean_name,
            "data_sufficiency": "INSUFFICIENT_DATA",
            "historical_count": 0,
            "message": "Database session required for historical vendor risk check."
        }

    try:
        vendor = session.query(VendorModel).filter(VendorModel.name.ilike(f"%{clean_name}%")).first()
        if not vendor:
            return {
                "vendor_name": clean_name,
                "data_sufficiency": "INSUFFICIENT_DATA",
                "historical_count": 0,
                "message": f"No vendor record found for '{clean_name}'."
            }

        invoices = session.query(InvoiceModel).filter(InvoiceModel.vendor_id == vendor.id).all()
        count = len(invoices)
        if count == 0:
            return {
                "vendor_id": vendor.id,
                "vendor_name": vendor.name,
                "data_sufficiency": "INSUFFICIENT_DATA",
                "historical_count": 0,
                "avg_amount": 0.0,
                "message": f"Zero historical invoices recorded for vendor '{vendor.name}'."
            }

        amounts = [float(inv.total_amount) for inv in invoices if inv.total_amount is not None]
        avg_amt = sum(amounts) / len(amounts) if amounts else 0.0
        min_amt = min(amounts) if amounts else 0.0
        max_amt = max(amounts) if amounts else 0.0

        return {
            "vendor_id": vendor.id,
            "vendor_name": vendor.name,
            "data_sufficiency": "SUFFICIENT" if count >= 2 else "INSUFFICIENT_DATA",
            "historical_count": count,
            "avg_amount": round(avg_amt, 2),
            "min_amount": round(min_amt, 2),
            "max_amount": round(max_amt, 2),
            "message": f"Found {count} historical invoices for vendor '{vendor.name}'."
        }
    except Exception as e:
        logger.error(f"Error querying vendor invoice history: {e}")
        return {
            "vendor_name": clean_name,
            "data_sufficiency": "INSUFFICIENT_DATA",
            "historical_count": 0,
            "error": str(e)
        }


def check_invoice_amount_anomaly(
    total_amount: float,
    vendor_name: Optional[str],
    session: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Risk Agent Tool: Detects if the current invoice total deviates significantly from historical vendor averages.
    Flag triggered if total_amount > 2.5x vendor average (with at least 2 historical invoices).
    """
    history = get_vendor_invoice_history(vendor_name, session=session)
    count = history.get("historical_count", 0)
    avg_amt = history.get("avg_amount", 0.0)

    if count < 2 or avg_amt <= 0:
        return {
            "is_anomaly": False,
            "data_sufficiency": "INSUFFICIENT_DATA",
            "reason": f"Insufficient historical data ({count} prior invoices) to evaluate amount anomaly."
        }

    ratio = total_amount / avg_amt if avg_amt > 0 else 1.0
    if ratio > 2.5:
        return {
            "is_anomaly": True,
            "data_sufficiency": "SUFFICIENT",
            "anomaly_type": "UNUSUAL_INVOICE_AMOUNT",
            "ratio": round(ratio, 2),
            "current_amount": total_amount,
            "historical_avg": avg_amt,
            "reason": f"Current amount (${total_amount:,.2f}) is {ratio:.1f}x higher than vendor average (${avg_amt:,.2f})."
        }

    return {
        "is_anomaly": False,
        "data_sufficiency": "SUFFICIENT",
        "ratio": round(ratio, 2),
        "current_amount": total_amount,
        "historical_avg": avg_amt,
        "reason": f"Invoice amount (${total_amount:,.2f}) is within expected historical range for vendor."
    }


def check_invoice_number_pattern(invoice_number: Optional[str]) -> Dict[str, Any]:
    """
    Risk Agent Tool: Inspects invoice number for suspicious, generic, or sequential patterns.
    """
    if not invoice_number or not invoice_number.strip():
        return {
            "suspicious": True,
            "reason": "Invoice number is missing or empty."
        }

    clean_num = invoice_number.strip().upper()
    suspicious_patterns = ["12345", "00000", "00001", "TEST", "SAMPLE", "DRAFT", "INV-000", "INV-12345"]

    for pattern in suspicious_patterns:
        if pattern in clean_num:
            return {
                "suspicious": True,
                "reason": f"Invoice number '{invoice_number}' contains suspicious generic pattern '{pattern}'."
            }

    return {
        "suspicious": False,
        "reason": f"Invoice number '{invoice_number}' follows standard formatting."
    }
