import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.connection import get_db_context, init_db
from app.database.models import VendorModel, PurchaseOrderModel
from app.database.repositories.invoice_repository import InvoiceRepository
from app.database.repositories.purchase_order_repository import PurchaseOrderRepository


def seed_database():
    """
    Idempotent database seeder:
    Inserts realistic master Vendors and Purchase Orders into MySQL ('invoice_db').
    Safe to run multiple times without duplicating data.
    """
    print("[SEED] Initializing database tables...")
    init_db()
    print("[SEED] Starting database seeding process...")

    with get_db_context() as db:
        inv_repo = InvoiceRepository()
        po_repo = PurchaseOrderRepository()

        # 1. Seed Master Vendors
        vendors_data = [
            {
                "name": "Acme Cloud Solutions Inc.",
                "tax_id": "US-88492019",
                "email": "billing@acmecloud.com",
                "phone": "+1-800-555-0199",
                "address": "100 Cloud Way, Suite 400, San Francisco, CA 94107"
            },
            {
                "name": "Vertex Software Solutions",
                "tax_id": "US-10293847",
                "email": "invoices@vertexsoft.io",
                "phone": "+1-888-555-0142",
                "address": "500 Tech Boulevard, Austin, TX 78701"
            },
            {
                "name": "Aether Dynamics Technologies",
                "tax_id": "US-99182736",
                "email": "accounts@aetherdynamics.com",
                "phone": "+1-800-555-0188",
                "address": "700 Innovation Parkway, Seattle, WA 98101"
            }
        ]

        created_vendors = {}
        for v_info in vendors_data:
            v_name = v_info["name"]
            existing_v = db.query(VendorModel).filter(VendorModel.name == v_name).first()
            if existing_v:
                print(f"  [OK] Vendor '{v_name}' already exists (ID: {existing_v.id}). Skipping.")
                created_vendors[v_name] = existing_v
            else:
                new_v = inv_repo.get_or_create_vendor(
                    db,
                    vendor_name=v_name,
                    tax_id=v_info["tax_id"],
                    email=v_info["email"],
                    phone=v_info["phone"],
                    address=v_info["address"]
                )
                print(f"  [+] Created Vendor '{v_name}' (ID: {new_v.id}).")
                created_vendors[v_name] = new_v

        db.commit()

        # 2. Seed Purchase Orders
        po_seeds = [
            {
                "po_number": "PO-8842",
                "vendor_name": "Acme Cloud Solutions Inc.",
                "authorized_total": "3300.00",
                "remaining_balance": "3300.00",
                "status": "APPROVED",
                "line_items": [
                    {
                        "description": "Enterprise Cloud Infrastructure Tier 3 Subscriptions",
                        "quantity": 10.0,
                        "unit_price": 300.0,
                        "line_total": 3000.0
                    },
                    {
                        "description": "Dedicated IP Address Add-ons",
                        "quantity": 3.0,
                        "unit_price": 100.0,
                        "line_total": 300.0
                    }
                ]
            },
            {
                "po_number": "PO-1001",
                "vendor_name": "Vertex Software Solutions",
                "authorized_total": "1620.00",
                "remaining_balance": "1620.00",
                "status": "APPROVED",
                "line_items": [
                    {
                        "description": "Software License - Pro Edition Annual Renewal",
                        "quantity": 1.0,
                        "unit_price": 1500.0,
                        "line_total": 1500.0
                    },
                    {
                        "description": "Priority Support SLA Surcharge (8%)",
                        "quantity": 1.0,
                        "unit_price": 120.0,
                        "line_total": 120.0
                    }
                ]
            },
            {
                "po_number": "PO-EXHAUSTED",
                "vendor_name": "Acme Cloud Solutions Inc.",
                "authorized_total": "500.00",
                "remaining_balance": "0.00",
                "status": "EXHAUSTED",
                "line_items": [
                    {
                        "description": "Legacy Storage Backup (Exhausted Budget)",
                        "quantity": 1.0,
                        "unit_price": 500.0,
                        "line_total": 500.0
                    }
                ]
            },
            {
                "po_number": "PO-CANCELLED",
                "vendor_name": "Aether Dynamics Technologies",
                "authorized_total": "10000.00",
                "remaining_balance": "10000.00",
                "status": "CANCELLED",
                "line_items": [
                    {
                        "description": "Cancelled Hardware Procurement Order",
                        "quantity": 1.0,
                        "unit_price": 10000.0,
                        "line_total": 10000.0
                    }
                ]
            }
        ]

        for po_info in po_seeds:
            po_num = po_info["po_number"]
            vendor_obj = created_vendors[po_info["vendor_name"]]

            existing_po = db.query(PurchaseOrderModel).filter(
                PurchaseOrderModel.po_number == po_num,
                PurchaseOrderModel.vendor_id == vendor_obj.id
            ).first()

            if existing_po:
                print(f"  [OK] Purchase Order '{po_num}' already exists for vendor '{vendor_obj.name}' (ID: {existing_po.id}). Skipping.")
            else:
                po_data = {
                    "po_number": po_num,
                    "vendor_id": vendor_obj.id,
                    "authorized_total": po_info["authorized_total"],
                    "remaining_balance": po_info["remaining_balance"],
                    "status": po_info["status"]
                }
                new_po = po_repo.create(db, po_data, po_info["line_items"])
                print(f"  [+] Created Purchase Order '{po_num}' [{po_info['status']}] (ID: {new_po.id}).")

        db.commit()
        print("[SUCCESS] Database seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
