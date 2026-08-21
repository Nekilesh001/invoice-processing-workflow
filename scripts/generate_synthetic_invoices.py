import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def create_invoice_pdf(output_path: Path, data: dict):
    """Generates a synthetic PDF invoice using ReportLab based on structured data."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=12
    )
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568")
    )
    bold_header_style = ParagraphStyle(
        'BoldHeaderStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor("#2D3748")
    )

    elements = []

    # Title & Header
    elements.append(Paragraph(data.get("title", "INVOICE"), title_style))
    elements.append(Spacer(1, 10))

    # Vendor & Meta Table
    vendor_lines = []
    if data.get("vendor_name"):
        vendor_lines.append(f"<b>{data['vendor_name']}</b>")
    if data.get("vendor_address"):
        vendor_lines.append(data["vendor_address"].replace('\n', '<br/>'))
    if data.get("vendor_email"):
        vendor_lines.append(f"Email: {data['vendor_email']}")
    if data.get("vendor_phone"):
        vendor_lines.append(f"Phone: {data['vendor_phone']}")
    if data.get("vendor_tax_id"):
        vendor_lines.append(f"Tax ID: {data['vendor_tax_id']}")

    vendor_text = "<br/>".join(vendor_lines) if vendor_lines else "<i>[Vendor Information Missing]</i>"

    meta_lines = []
    if data.get("invoice_number"):
        meta_lines.append(f"<b>Invoice #:</b> {data['invoice_number']}")
    if data.get("invoice_date"):
        meta_lines.append(f"<b>Invoice Date:</b> {data['invoice_date']}")
    if data.get("due_date"):
        meta_lines.append(f"<b>Due Date:</b> {data['due_date']}")
    else:
        meta_lines.append("<b>Due Date:</b> <i>[NOT SPECIFIED]</i>")
    if data.get("po_number"):
        meta_lines.append(f"<b>PO #:</b> {data['po_number']}")
    if data.get("currency"):
        meta_lines.append(f"<b>Currency:</b> {data['currency']}")

    meta_text = "<br/>".join(meta_lines)

    header_table_data = [
        [Paragraph(vendor_text, header_style), Paragraph(meta_text, header_style)]
    ]
    header_table = Table(header_table_data, colWidths=[300, 240])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))

    # Customer Information
    customer_lines = ["<b>Billed To:</b>"]
    if data.get("customer_name"):
        customer_lines.append(f"<b>{data['customer_name']}</b>")
    if data.get("customer_address"):
        customer_lines.append(data["customer_address"].replace('\n', '<br/>'))
    if data.get("customer_email"):
        customer_lines.append(f"Email: {data['customer_email']}")

    customer_text = "<br/>".join(customer_lines)
    elements.append(Paragraph(customer_text, header_style))
    elements.append(Spacer(1, 20))

    # Line Items Table
    items = data.get("line_items", [])
    if items:
        table_data = [
            [
                Paragraph("<b>Item Description</b>", bold_header_style),
                Paragraph("<b>Qty</b>", bold_header_style),
                Paragraph("<b>Unit Price</b>", bold_header_style),
                Paragraph("<b>Total</b>", bold_header_style)
            ]
        ]
        for item in items:
            table_data.append([
                Paragraph(item.get("description", ""), header_style),
                Paragraph(str(item.get("quantity", "")), header_style),
                Paragraph(f"{data.get('currency', '$')}{item.get('unit_price', 0):,.2f}", header_style),
                Paragraph(f"{data.get('currency', '$')}{item.get('line_total', 0):,.2f}", header_style)
            ])

        items_table = Table(table_data, colWidths=[280, 60, 100, 100])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 15))

    # Totals Summary Table
    totals_data = []
    if "subtotal" in data:
        totals_data.append(["Subtotal:", f"{data.get('currency', '$')}{data['subtotal']:,.2f}"])
    if "tax_amount" in data:
        totals_data.append(["Tax Amount:", f"{data.get('currency', '$')}{data['tax_amount']:,.2f}"])
    if "total_amount" in data:
        totals_data.append(["Total Amount:", f"{data.get('currency', '$')}{data['total_amount']:,.2f}"])
    if "amount_due" in data:
        totals_data.append(["Amount Due:", f"{data.get('currency', '$')}{data['amount_due']:,.2f}"])

    if totals_data:
        totals_table = Table(totals_data, colWidths=[400, 140])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#1A365D")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(totals_table)

    # Payment Notes
    if data.get("payment_terms"):
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"<b>Payment Terms:</b> {data['payment_terms']}", header_style))

    doc.build(elements)


def generate_all_samples():
    base_dir = Path(__file__).resolve().parent.parent
    sample_dir = base_dir / "data" / "sample_invoices"
    sample_dir.mkdir(parents=True, exist_ok=True)

    # 1. Normal Valid Invoice
    invoice_001 = {
        "title": "TAX INVOICE",
        "vendor_name": "Acme Cloud Solutions Inc.",
        "vendor_address": "100 Innovation Way, Suite 400\nTech City, CA 94016",
        "vendor_email": "billing@acmecloud.com",
        "vendor_phone": "+1 (555) 019-2831",
        "vendor_tax_id": "US-987654321",
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-08-15",
        "due_date": "2026-09-15",
        "po_number": "PO-8842",
        "currency": "USD",
        "customer_name": "Global Logistics Corp",
        "customer_address": "500 Supply Chain Blvd\nSuite 100, Chicago, IL 60601",
        "customer_email": "ap@globallogistics.com",
        "line_items": [
            {"description": "Enterprise Cloud Server Infrastructure - August 2026", "quantity": 1, "unit_price": 2500.00, "line_total": 2500.00},
            {"description": "Database Backup & Clustering Service", "quantity": 2, "unit_price": 250.00, "line_total": 500.00}
        ],
        "subtotal": 3000.00,
        "tax_amount": 300.00,
        "total_amount": 3300.00,
        "amount_due": 3300.00,
        "payment_terms": "Net 30 Days. Bank transfer to Acme Account #99887766."
    }
    create_invoice_pdf(sample_dir / "invoice_001_normal.pdf", invoice_001)

    # 2. Missing Due Date
    invoice_002 = {
        "title": "INVOICE",
        "vendor_name": "Vertex Software Solutions",
        "vendor_address": "42 Code Avenue, Austin, TX 78701",
        "vendor_email": "invoices@vertexsoft.com",
        "invoice_number": "INV-2026-002",
        "invoice_date": "2026-08-18",
        "due_date": None,
        "currency": "USD",
        "customer_name": "Apex Retailers LLC",
        "customer_address": "12 Market Street, Dallas, TX 75201",
        "line_items": [
            {"description": "Custom API Integration Consulting", "quantity": 10, "unit_price": 150.00, "line_total": 1500.00}
        ],
        "subtotal": 1500.00,
        "tax_amount": 120.00,
        "total_amount": 1620.00,
        "amount_due": 1620.00
    }
    create_invoice_pdf(sample_dir / "invoice_002_missing_due_date.pdf", invoice_002)

    # 3. Missing Vendor Info
    invoice_003 = {
        "title": "INVOICE",
        "vendor_name": None,
        "vendor_address": None,
        "invoice_number": "INV-2026-003",
        "invoice_date": "2026-08-10",
        "due_date": "2026-08-25",
        "currency": "USD",
        "customer_name": "Nexus Corp",
        "line_items": [
            {"description": "Hardware Maintenance", "quantity": 1, "unit_price": 800.00, "line_total": 800.00}
        ],
        "subtotal": 800.00,
        "tax_amount": 0.00,
        "total_amount": 800.00,
        "amount_due": 800.00
    }
    create_invoice_pdf(sample_dir / "invoice_003_missing_vendor.pdf", invoice_003)

    # 4. Invalid Total Calculation (Subtotal $1000 + Tax $100 = $1100, but Total claims $1500)
    invoice_004 = {
        "title": "INVOICE",
        "vendor_name": "Delta Tech Services",
        "vendor_address": "88 Data Drive, Seattle, WA 98101",
        "invoice_number": "INV-2026-004",
        "invoice_date": "2026-08-01",
        "due_date": "2026-08-31",
        "currency": "USD",
        "customer_name": "Omni Global",
        "line_items": [
            {"description": "System Audit", "quantity": 1, "unit_price": 1000.00, "line_total": 1000.00}
        ],
        "subtotal": 1000.00,
        "tax_amount": 100.00,
        "total_amount": 1500.00,  # Intentional arithmetic mismatch!
        "amount_due": 1500.00
    }
    create_invoice_pdf(sample_dir / "invoice_004_invalid_total.pdf", invoice_004)

    print(f"Generated 4 synthetic PDF invoices in {sample_dir}")


if __name__ == "__main__":
    generate_all_samples()
