import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database.connection import get_engine, init_db, sessionmaker
from app.services.pipeline_runner import InvoicePipelineRunner


def print_result_summary(result):
    """Prints a clean CLI summary of processing results."""
    print("=" * 65)
    print(f"DOCUMENT      : {result.document_name}")
    print(f"STATUS        : {result.status.value}")
    print(f"EXTRACTION    : {result.extraction_method}")
    print(f"DATABASE ID   : {result.database_invoice_id or 'N/A'}")
    if result.review_task_id:
        print(f"REVIEW TASK ID: {result.review_task_id}")

    if result.extracted_invoice:
        inv = result.extracted_invoice
        print("-" * 65)
        print(f"Vendor Name   : {inv.vendor.vendor_name if inv.vendor else 'N/A'}")
        print(f"Invoice #     : {inv.invoice_number}")
        print(f"Invoice Date  : {inv.invoice_date}")
        print(f"Due Date      : {inv.due_date}")
        print(f"Total Amount  : {inv.currency} {inv.total_amount}")
        print(f"Line Items    : {len(inv.line_items)} items")

    if result.validation_result:
        val = result.validation_result
        print("-" * 65)
        print(f"VALIDATION    : {'PASSED' if val.is_valid else 'FAILED'}")
        if val.errors:
            print("ERRORS:")
            for err in val.errors:
                print(f"  ❌ [{err.rule_name}] {err.message}")
        if val.warnings:
            print("WARNINGS:")
            for warn in val.warnings:
                print(f"  ⚠️  [{warn.rule_name}] {warn.message}")

    if result.error_message:
        print(f"ERROR DETAILS : {result.error_message}")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="AI Invoice Processing Workflow Pipeline Runner")
    parser.add_argument("--file", type=str, help="Path to single invoice PDF file")
    parser.add_argument("--dir", type=str, help="Directory containing invoice PDF files")
    parser.add_argument("--sqlite", action="store_true", help="Use local SQLite database instead of MySQL")

    args = parser.parse_args()

    if not args.file and not args.dir:
        print("Please specify --file <path> or --dir <path>. Use --help for usage details.")
        sys.exit(1)

    # Initialize database
    if args.sqlite:
        sqlite_url = f"sqlite:///{settings.BASE_DIR / 'invoice_workflow.db'}"
        print(f"[DB] Initializing SQLite database at: {sqlite_url}")
        engine = get_engine(sqlite_url)
    else:
        print(f"[DB] Connecting to MySQL database at: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        engine = get_engine()

    init_db(engine)
    session_factory = sessionmaker(bind=engine)

    runner = InvoicePipelineRunner()

    files_to_process = []
    if args.file:
        files_to_process.append(Path(args.file))
    elif args.dir:
        dir_path = Path(args.dir)
        files_to_process.extend(sorted(dir_path.glob("*.pdf")))

    if not files_to_process:
        print("No PDF files found to process.")
        sys.exit(0)

    print(f"Starting pipeline processing for {len(files_to_process)} invoice(s)...\n")

    for file_path in files_to_process:
        with session_factory() as session:
            result = runner.process_file(file_path, db_session=session)
            session.commit()
            print_result_summary(result)


if __name__ == "__main__":
    main()
