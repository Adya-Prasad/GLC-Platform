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
- **Report Generation**: JSON/PDF GLP investor reports

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
| Use of Proceeds | app/services/glp_rules.py | `validate_use_of_proceeds()` |
| All 6 DNSH Checks | app/services/glp_rules.py | `assess_dnsh()`, `_check_*()` methods |
| Carbon Lock-in | app/services/glp_rules.py | `assess_carbon_lockin()` |
| Overall Eligibility | app/services/glp_rules.py | `assess_glp_eligibility()` |
| Scoring Integration | app/services/scoring.py | `calculate_dnsh_penalty()`, `calculate_carbon_penalty()` |
| Pipeline Integration | app/services/ingestion.py | `run_ingestion()` |


## API Endpoints

### Borrower Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/borrower/apply` | Create loan application |
| POST | `/api/v1/borrower/{id}/documents` | Upload documents |
| POST | `/api/v1/borrower/{id}/submit_for_ingestion` | Submit for processing |
| GET | `/api/v1/borrower/applications` | List my applications |

### Lender Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/lender/applications` | List all applications |
| GET | `/api/v1/lender/application/{id}` | Get application details |
| POST | `/api/v1/lender/application/{id}/verify` | Approve/Reject |
| GET | `/api/v1/lender/portfolio/summary` | Portfolio metrics |

### Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ingest/run/{id}` | Run document ingestion |
| GET | `/api/v1/report/application/{id}` | Generate GLP report |
| POST | `/api/v1/external_review/{id}/request` | Generate audit package |
| GET | `/api/v1/audit` | View audit trail |

## Project Structure

```
glp-sentinel/
├── app/
│   ├── main.py              # FastAPI app & routers
│   ├── api/
│   │   ├── borrower.py      # Borrower endpoints
│   │   ├── lender.py        # Lender endpoints
│   │   └── admin.py         # Admin endpoints
│   ├── core/
│   │   ├── config.py        # Configuration
│   │   └── auth.py          # Mock authentication
│   ├── models/
│   │   ├── db.py            # SQLAlchemy setup
│   │   ├── orm_models.py    # Database models
│   │   └── schemas.py       # Pydantic schemas
│   ├── services/
│   │   ├── nlp.py           # NLP/embedding service
│   │   ├── rag.py           # RAG retrieval
│   │   ├── glp_rules.py     # GLP compliance rules
│   │   ├── scoring.py       # ESG scoring engine
│   │   ├── ingestion.py     # Document ingestion
│   │   └── report.py        # Report generation
│   ├── utils/
│   │   ├── faiss_index.py   # Vector indexing
│   │   ├── pdf_text.py      # PDF extraction
│   │   └── storage.py       # File storage
│   └── data/
│       └── sector_baselines.csv
├── static/
│   ├── index.html           # Frontend UI
│   └── app.js               # Frontend application
├── requirements.txt
└── README.md
```

## GLP Compliance Features

### 1. Use of Proceeds Validation
- Maps project descriptions to GLP eligible categories
- Detects green indicators and red flags
- Classifies into 10 GLP categories

### 2. DNSH Assessment
Checks 6 EU Taxonomy criteria:
- Climate change mitigation
- Climate change adaptation
- Water and marine resources
- Circular economy
- Pollution prevention
- Biodiversity protection

### 3. Carbon Lock-in Risk
- Identifies fossil fuel infrastructure indicators
- Assesses transition risk
- Recommends mitigation strategies

### 4. ESG Scoring
Composite score (0-100) based on:
- Data completeness (20%)
- Verifiability (25%)
- GLP alignment (25%)
- DNSH penalty (up to -30%)
- Carbon lock-in penalty (up to -20%)

### 5. KPI/SPT Calibration
- Compares targets against sector baselines
- Calculates ambition scores
- Flags targets as ambitious or not

## Sample API Request

```json
POST /api/v1/borrower/apply
{
  "org_name": "ACME Renewables Ltd",
  "project_name": "Wind Farm X",
  "sector": "Renewable Energy",
  "location": "Spain",
  "project_type": "New",
  "amount_requested": 120000000,
  "currency": "EUR",
  "use_of_proceeds": "Construction and installation of 100MW wind turbines",
  "scope1_tco2": 25000,
  "scope2_tco2": 10000,
  "scope3_tco2": 5000,
  "baseline_year": 2023
}
```

## Demo Notes

- **No real authentication**: Click "Enter as Borrower" or "Enter as Lender" to login
- **Mock NLP models**: Works without GPU, uses fallback extractors
- **SQLite database**: Single file `glp_sentinel.db`

## License

MIT License - Hackathon Demo Project
