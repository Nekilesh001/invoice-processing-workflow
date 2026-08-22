import sys
import time
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database.connection import init_db, get_session_factory
from app.database.models import VendorModel, PurchaseOrderModel, PurchaseOrderLineItemModel
from app.extraction.extractor import DocumentExtractor
from app.llm.client import LLMClient
from app.services.pipeline_runner import InvoicePipelineRunner
from app.schemas.processing import ProcessingStatus


def seed_evaluation_database(session):
    """Seed test database with master vendors and POs required for evaluation."""
    v1 = VendorModel(
        name="Acme Cloud Solutions Inc.",
        tax_id="US-88492019",
        registration_number="REG-994182"
    )
    session.add(v1)
    session.flush()

    po1 = PurchaseOrderModel(
        po_number="PO-8842",
        vendor_id=v1.id,
        status="APPROVED",
        authorized_total=3300.00,
        remaining_balance=3300.00,
        currency="USD"
    )
    session.add(po1)
    session.flush()

    li1 = PurchaseOrderLineItemModel(
        purchase_order_id=po1.id,
        description="Enterprise Cloud Server Infrastructure",
        quantity=1.0,
        unit_price=2500.00,
        line_total=2500.00
    )
    li2 = PurchaseOrderLineItemModel(
        purchase_order_id=po1.id,
        description="Database Service",
        quantity=2.0,
        unit_price=250.00,
        line_total=500.00
    )
    session.add_all([li1, li2])
    session.commit()


def run_evaluation():
    sample_dir = settings.BASE_DIR / "data" / "sample_invoices"
    pdf_files = sorted(sample_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No sample invoice PDFs found in {sample_dir}")
        return

    print("=" * 85)
    print(" AI INVOICE PROCESSING PLATFORM — MASTER EVALUATION BENCHMARK ")
    print("=" * 85)
    print(f"Evaluating {len(pdf_files)} test document(s) against in-memory benchmark DB...\n")

    # In-memory evaluation database engine
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()
    seed_evaluation_database(session)

    runner = InvoicePipelineRunner()

    total_docs = len(pdf_files)
    native_count = 0
    ocr_count = 0
    approved_count = 0
    review_count = 0
    failed_count = 0
    durations = []
    unsafe_approvals = 0

    print(f"{'DOCUMENT':<32} | {'EXTRACTION':<10} | {'VALIDATION':<10} | {'AGENT DECISION':<14} | {'TIME(ms)':<8}")
    print("-" * 85)

    for pdf_path in pdf_files:
        start_t = time.perf_counter()
        try:
            res = runner.process_file(pdf_path, db_session=session)
            elapsed_ms = (time.perf_counter() - start_t) * 1000
            durations.append(elapsed_ms)

            if res.extraction_method == "native_pdf":
                native_count += 1
            else:
                ocr_count += 1

            val_str = "VALID" if res.validation_result and res.validation_result.is_valid else "INVALID"
            status_str = res.status.value if hasattr(res.status, "value") else str(res.status)

            if res.status == ProcessingStatus.SUCCESS:
                approved_count += 1
            elif res.status in (ProcessingStatus.NEEDS_REVIEW, ProcessingStatus.DUPLICATE_SUSPECTED):
                review_count += 1
            else:
                failed_count += 1

            # Safety check: Normal invoice is PO-8842; any file with 'mismatch' or 'invalid' must NEVER be AUTO_PROCESS / SUCCESS
            if ("mismatch" in pdf_path.name.lower() or "invalid" in pdf_path.name.lower()) and res.status == ProcessingStatus.SUCCESS:
                unsafe_approvals += 1

            print(f"{pdf_path.name:<32} | {res.extraction_method:<10} | {val_str:<10} | {status_str:<14} | {elapsed_ms:<8.1f}")
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_t) * 1000
            failed_count += 1
            print(f"{pdf_path.name:<32} | {'ERROR':<10} | {'FAILED':<10} | {'FAILED':<14} | {elapsed_ms:<8.1f}")

    session.close()

    avg_latency = sum(durations) / len(durations) if durations else 0.0
    ocr_rate = (ocr_count / total_docs) * 100 if total_docs > 0 else 0.0

    print("-" * 85)
    print("\nMASTER EVALUATION METRICS SUMMARY")
    print("-" * 45)
    print(f"Total Documents Evaluated      : {total_docs}")
    print(f"Native PDF Extractions         : {native_count} ({(native_count/total_docs)*100:.1f}%)")
    print(f"Tesseract OCR Fallbacks        : {ocr_count} ({ocr_rate:.1f}%)")
    print(f"Auto-Approved Invoices         : {approved_count}")
    print(f"Human Review Flagged Invoices  : {review_count}")
    print(f"Failed Invoices                : {failed_count}")
    print(f"Unsafe Auto-Approvals          : {unsafe_approvals} (Safety score: {100.0 if unsafe_approvals == 0 else 0.0}%)")
    print(f"Average Pipeline Latency       : {avg_latency:.2f} ms")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    run_evaluation()
