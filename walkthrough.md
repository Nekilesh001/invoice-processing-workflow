# Walkthrough - AI Invoice Processing & Verification Platform (Final Complete Project)

We have successfully engineered and delivered a production-ready **AI Invoice Processing & Verification Platform** in Python 3.11, transitioning from Andrew Ng's baseline deterministic workflow to a full **Agentic AI Architecture** with FastAPI REST services, Tesseract OCR fallback, and MySQL persistence.

## Summary of All Completed Milestones

### Milestone 0: Environment Inspection & `.venv` Setup
- Verified Python 3.11.9 (`C:\Users\NEKILESH\AppData\Local\Programs\Python\Python311\python.exe`).
- Verified local Tesseract OCR v5.5.0 binary (`C:\Program Files\Tesseract-OCR\tesseract.exe`).
- Verified local MySQL Server 8.0 (`MySQL80` service running).
- Created clean `.venv` environment and verified version isolation.

### Milestone 1: Project Foundation & Synthetic Invoice Generator
- Installed core dependencies (`pymupdf`, `pytesseract`, `pillow`, `pydantic`, `sqlalchemy`, `pymysql`, `openai`, `reportlab`, `pytest`).
- Configured Pydantic Settings in [app/config.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/config.py) and environment files ([.env.example](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/.env.example) & [.env](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/.env)).
- Built synthetic invoice generator ([scripts/generate_synthetic_invoices.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/scripts/generate_synthetic_invoices.py)) creating 5 test PDF scenarios (`invoice_001` through `invoice_006`).

### Milestone 2: Document Pipeline (Native PDF Text + Tesseract OCR Fallback)
- Created text cleaner ([app/extraction/cleaner.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/extraction/cleaner.py)).
- Created document extraction engine ([app/extraction/extractor.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/extraction/extractor.py)) with PyMuPDF text extraction, character quality threshold checks, 300 DPI rendering, and `pytesseract` OCR fallback.

### Milestone 3: Pydantic Invoice Schemas & System Prompt
- Built typed Pydantic models ([app/schemas/invoice.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/schemas/invoice.py)) with `Decimal` monetary precision, `date` fields, and nested line items.
- Built pipeline container models ([app/schemas/processing.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/schemas/processing.py)).
- Created versioned system prompt ([app/prompts/invoice_extraction_v1.txt](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/prompts/invoice_extraction_v1.txt)).

### Milestone 4: LLM Abstraction & Invoice Extraction Service
- Built OpenAI-compatible LLM client ([app/llm/client.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/llm/client.py)) targeting `glm-4.7-flash:latest` with JSON mode enforcement.
- Created `InvoiceExtractionService` ([app/services/extraction_service.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/services/extraction_service.py)).

### Milestone 5: Deterministic Business Validation Engine
- Built `InvoiceValidator` ([app/validation/validator.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/validation/validator.py)) enforcing 7 deterministic Python business checks (completeness, grand total arithmetic, line items sum, line item math, date sanity, non-negative amounts, and amount due boundaries).

### Milestone 6: Relational MySQL Database Architecture & Repositories
- Built Declarative ORM models ([app/database/models.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/database/models.py)) for master vendors, customers, invoices, line items, validation records, processing runs, and review tasks.
- Built `InvoiceRepository` ([app/database/repositories/invoice_repository.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/database/repositories/invoice_repository.py)) with transactional persistence and vendor + invoice_number duplicate checking.

### Milestone 7: Deterministic End-to-End Pipeline & CLI Tool
- Created pipeline orchestrator ([app/services/pipeline_runner.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/services/pipeline_runner.py)).
- Created CLI runner tool ([scripts/process_invoice.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/scripts/process_invoice.py)).

### Milestone 8: Agentic AI Layer (Tools, PO Lookup, & Autonomous Routing)
- Built agent domain verification tools ([app/agents/tools.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/agents/tools.py)): `lookup_vendor`, `lookup_purchase_order`, `check_duplicate_invoice`, `create_review_task`.
- Built autonomous decision agent ([app/agents/invoice_agent.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/agents/invoice_agent.py)) evaluating PO authorized amounts vs invoice totals and routing to `AUTO_PROCESS` or `HUMAN_REVIEW` with an audit log.

### Milestone 9: FastAPI Web Server & Human Review REST Endpoints
- Built FastAPI application ([app/main.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/main.py)) with Swagger UI docs at `/docs` and healthcheck `/health`.
- Built REST API endpoints ([app/api/endpoints/invoices.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/api/endpoints/invoices.py) & [app/api/endpoints/reviews.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/app/api/endpoints/reviews.py)) supporting invoice PDF uploads and human review task approvals/rejections.

### Milestone 10: Evaluation Framework, Production README & GitHub Push
- Created evaluation benchmark tool ([scripts/evaluate_pipeline.py](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/scripts/evaluate_pipeline.py)).
- Authored production [README.md](file:///d:/ONE_DATA/DeepLearning.AI/agentic-ai-hands-on/invoice_workflow/README.md) with Mermaid workflow diagrams and deployment guides.
- Pushed all commits to GitHub: [https://github.com/Nekilesh001/invoice-processing-workflow](https://github.com/Nekilesh001/invoice-processing-workflow).

---

## Verification Summary

### Automated Test Suite (`pytest`)
Ran `.\.venv\Scripts\pytest`:
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 33 items

tests\integration\test_pipeline.py ...                                   [  9%]
tests\unit\test_agent.py ....                                            [ 21%]
tests\unit\test_api.py ....                                              [ 33%]
tests\unit\test_config.py .                                              [ 36%]
tests\unit\test_database.py ....                                         [ 48%]
tests\unit\test_extraction.py ....                                       [ 60%]
tests\unit\test_llm_service.py ...                                       [ 69%]
tests\unit\test_schemas.py ...                                           [ 78%]
tests\unit\test_synthetic_invoice.py ..                                  [ 84%]
tests\unit\test_validation.py .....                                      [100%]

============================= 33 passed in 1.61s ==============================
```

### Evaluation Benchmark Performance
Ran `.\.venv\Scripts\python scripts/evaluate_pipeline.py`:
```text
DOCUMENT                            | METHOD     | CHARS  | TIME(ms) | STATUS
----------------------------------------------------------------------
invoice_001_normal.pdf              | native_pdf | 713    | 4.1      | SUCCESS
invoice_002_missing_due_date.pdf    | native_pdf | 442    | 2.3      | SUCCESS
invoice_003_missing_vendor.pdf      | native_pdf | 309    | 1.7      | SUCCESS
invoice_004_invalid_total.pdf       | native_pdf | 338    | 1.3      | SUCCESS
invoice_006_scanned_invoice.pdf     | ocr        | 353    | 350.2    | SUCCESS
----------------------------------------------------------------------
Native PDF Extractions    : 80.0%
Tesseract OCR Fallbacks   : 20.0%
Average Extraction Latency: 71.94 ms
```
