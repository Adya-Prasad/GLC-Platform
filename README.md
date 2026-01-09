# GLC Platform - Green Lending & Compliance Framework


🌿 **Hackathon Project** | Green Loan Principles Compliance Platform

---
# TODO
1. to check in other ide to check it is working or not on all device
2. create and publish a build
3. Deploy it
---

## Overview

GLC Platform automates Green Loan Principles (GLP) compliance for borrowers and lenders. It implements:

- **Borrower Onboarding**: ESG questionnaire + document upload
- **Document Ingestion**: Text extraction, chunking, embedding, FAISS indexing
- **GLP Rule Engine**: Use of Proceeds mapping, DNSH checklist, KPI/SPT calibration
- **ESG Scoring**: Composite scoring with completeness, verifiability, GLP alignment
- **Lender Dashboard**: Application review, verification, portfolio management

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, SQLite
- **NLP/ML**: Sentence-Transformers, HuggingFace Transformers, FAISS
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
- **PDF Processing**: pdfminer.six, PyPDF2, WeasyPrint

## Quick Start

### 1. Create Conda Environment

```bash
conda create --prefix .\.conda_env python=3.12 -y
conda activate .\.conda_env
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Access the Platform

- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Tech Stack
| Layer | Technology |
|-------|------------|
| Backend | Python 3.12 + FastAPI |
| Database | SQLite via SQLAlchemy ORM `glc_data.db` |
| Vector Search | FAISS `faiss-cpu` with sentence-transformers/all-MiniLM-L6-v2 embeddings |
| NLP/AI | HuggingFace `deepset/roberta-base-squad2` for QA, `google/flan-t5-small` for RAG |
| PDF Processing | `pdfminer.six` with OCR fallback |
| Frontend | Vanilla JavaScript ES Modules + TailwindCSS |


### Quick Reference Table
| Feature | File | Key Methods |
|---------|------|-------------|
| GLP Categories | app/core/config.py | GLP_CATEGORIES list |
| DNSH Criteria | app/core/config.py | DNSH_CRITERIA dict |
| Carbon Indicators | app/core/config.py | CARBON_LOCKIN_INDICATORS list |
| Use of Proceeds | app/services/esg_framework.py | `validate_use_of_proceeds()` |
| All 6 DNSH Checks | app/services/esg_framework.py | `assess_dnsh()`, `_check_*()` methods |
| Carbon Lock-in | app/services/esg_framework.py | `assess_carbon_lockin()` |
| Overall Eligibility | app/services/esg_framework.py | `assess_glp_eligibility()` |
| Scoring Integration | app/services/scoring.py | `calculate_dnsh_penalty()`, `calculate_carbon_penalty()` |
| Pipeline Integration | app/services/ingestion.py | `run_ingestion()` |





## License

MIT License - Hackathon Demo Project
