import sys
import time
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database.connection import Base
from app.extraction.extractor import DocumentExtractor
from app.validation.validator import InvoiceValidator
from app.schemas.processing import ProcessingStatus


def run_evaluation():
    sample_dir = settings.BASE_DIR / "data" / "sample_invoices"
    pdf_files = sorted(sample_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No sample invoice PDFs found in {sample_dir}")
        return

    print("=" * 70)
    print(" AI INVOICE PROCESSING PLATFORM — EVALUATION BENCHMARK SUITE ")
    print("=" * 70)
    print(f"Evaluating {len(pdf_files)} synthetic test document(s)...\n")

    extractor = DocumentExtractor()
    validator = InvoiceValidator()

    total_docs = len(pdf_files)
    native_count = 0
    ocr_count = 0
    valid_count = 0
    invalid_count = 0
    total_chars = 0
    durations = []

    print(f"{'DOCUMENT':<35} | {'METHOD':<10} | {'CHARS':<6} | {'TIME(ms)':<8} | {'STATUS'}")
    print("-" * 70)

    for pdf_path in pdf_files:
        start_time = time.perf_counter()
        try:
            res = extractor.extract(pdf_path)
            duration_ms = res.extraction_time_ms
            durations.append(duration_ms)
            total_chars += res.character_count

            if res.extraction_method == "native_pdf":
                native_count += 1
            else:
                ocr_count += 1

            status_str = "SUCCESS"
            print(f"{pdf_path.name:<35} | {res.extraction_method:<10} | {res.character_count:<6} | {duration_ms:<8.1f} | {status_str}")
        except Exception as e:
            print(f"{pdf_path.name:<35} | {'ERROR':<10} | {'0':<6} | {'0.0':<8} | FAILED ({str(e)})")

    avg_latency = sum(durations) / len(durations) if durations else 0.0
    ocr_rate = (ocr_count / total_docs) * 100 if total_docs > 0 else 0.0

    print("-" * 70)
    print("\nBENCHMARK METRICS SUMMARY")
    print("-" * 40)
    print(f"Total Documents Evaluated : {total_docs}")
    print(f"Native PDF Extractions    : {native_count} ({(native_count/total_docs)*100:.1f}%)")
    print(f"Tesseract OCR Fallbacks   : {ocr_count} ({ocr_rate:.1f}%)")
    print(f"Total Characters Extracted: {total_chars}")
    print(f"Average Extraction Latency: {avg_latency:.2f} ms")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_evaluation()
