# Adaptive Document Preparation System

A production-style adaptive RAG backend for PDF-based study preparation and MCQ generation.

This project ingests a structured multi-section PDF, stores document sections and learning history in PostgreSQL, indexes semantic chunk embeddings in Qdrant, retrieves only user-selected sections, generates MCQs through an LLM, validates structured outputs, scores answers, identifies weak topics, and adapts future question generation based on previous mistakes.

The goal is not only to build a basic RAG system. The main goal is to prove adaptive preparation behavior across repeated study sessions.

---

## Tech Stack

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-REST%20API-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-Knowledge%20Base-4169E1?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Qdrant-Vector%20Store-DC244C" />
  <img src="https://img.shields.io/badge/Redis-Broker%20%26%20Cache-DC382D?logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/Celery-Task%20Queue-3771A1?logo=celery&logoColor=white" />
  <img src="https://img.shields.io/badge/LangGraph-Workflow-1C3C3C" />
  <img src="https://img.shields.io/badge/LangChain-Ecosystem-1C3C3C" />
  <img src="https://img.shields.io/badge/Groq-LLM-orange" />
  <img src="https://img.shields.io/badge/Hugging%20Face-Embeddings-FFD21E?logo=huggingface&logoColor=black" />
  <img src="https://img.shields.io/badge/SentenceTransformers-all--MiniLM--L6--v2-yellow" />
  <img src="https://img.shields.io/badge/PyMuPDF-PDF%20Parsing-green" />
  <img src="https://img.shields.io/badge/SQLAlchemy-ORM-red" />
  <img src="https://img.shields.io/badge/Typer-CLI-purple" />
  <img src="https://img.shields.io/badge/Docker-Services-2496ED?logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Pytest-Tests-0A9EDC?logo=pytest&logoColor=white" />
</p>

---

## Documentation

| File | Purpose |
|---|---|
| `docs/architecture.md` | Hybrid RAG architecture and retrieval flow |
| `docs/database_schema.md` | PostgreSQL schema and KB relationships |
| `docs/adaptation_strategy.md` | Adaptive logic and weak-topic tracking |
| `docs/optional_enhancements.md` | Optional Enhancements |

### Recommended Reading Order

```text
1. docs/architecture.md
2. docs/database_schema.md
3. docs/adaptation_strategy.md
```

---

## Architecture Overview

```text
                           ┌────────────────────┐
                           │  Structured PDF    │
                           │ SLATEFALL_DOSSIER │
                           └─────────┬──────────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │ PyMuPDF PDF Extraction │
                        └─────────┬──────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
        ┌─────────────────────┐     ┌─────────────────────┐
        │ PostgreSQL Storage  │     │ Embedding Pipeline  │
        │ Sections / Sessions │     │ SentenceTransformers│
        └─────────┬───────────┘     └─────────┬───────────┘
                  │                           │
                  ▼                           ▼
        ┌─────────────────────┐     ┌─────────────────────┐
        │ Knowledge History   │     │ Qdrant Vector Store │
        │ Weak Topics         │     │ Semantic Retrieval  │
        └─────────┬───────────┘     └─────────┬───────────┘
                  └─────────────┬─────────────┘
                                ▼
                    ┌────────────────────────┐
                    │     LangGraph Flow     │
                    │ Adaptive RAG Workflow  │
                    └─────────┬──────────────┘
                              ▼
                    ┌────────────────────────┐
                    │   LLM MCQ Generation   │
                    │      Groq / Mock       │
                    └─────────┬──────────────┘
                              ▼
                    ┌────────────────────────┐
                    │ Scoring + Adaptation   │
                    │ Weak Topic Tracking    │
                    └────────────────────────┘
```

---

# Table of Contents

- [Adaptive Document Preparation System](#adaptive-document-preparation-system)
  - [Tech Stack](#tech-stack)
  - [Documentation](#documentation)
    - [Recommended Reading Order](#recommended-reading-order)
  - [Architecture Overview](#architecture-overview)
- [Table of Contents](#table-of-contents)
- [1. Project Highlights](#1-project-highlights)
    - [Core Adaptive Logic](#core-adaptive-logic)
- [2. Current Verified Status](#2-current-verified-status)
  - [Verified Features](#verified-features)
    - [Latest Verified Adaptive Runs](#latest-verified-adaptive-runs)
- [3. Repository](#3-repository)
- [4. Prerequisites](#4-prerequisites)
  - [Recommended Environment](#recommended-environment)
  - [Required Services](#required-services)
- [5. Fresh Setup on a New PC](#5-fresh-setup-on-a-new-pc)
  - [5.1 Clone the Repository](#51-clone-the-repository)
  - [5.2 Create and Activate a Virtual Environment](#52-create-and-activate-a-virtual-environment)
    - [Windows PowerShell](#windows-powershell)
    - [macOS / Linux](#macos--linux)
  - [5.3 Install Dependencies](#53-install-dependencies)
  - [5.4 Create `.env`](#54-create-env)
    - [Windows PowerShell](#windows-powershell-1)
    - [macOS / Linux](#macos--linux-1)
    - [Optional Deterministic Local Testing](#optional-deterministic-local-testing)
- [6. Environment Variables](#6-environment-variables)
- [7. Start Docker Services](#7-start-docker-services)
  - [Verify Services](#verify-services)
    - [PostgreSQL](#postgresql)
    - [Qdrant](#qdrant)
    - [Redis](#redis)
- [8. Prepare the Knowledge Base (Idempotent Setup)](#8-prepare-the-knowledge-base-idempotent-setup)
  - [Step 1 — Reset Relational Tables](#step-1--reset-relational-tables)
  - [Step 2 — Clear Qdrant Collection](#step-2--clear-qdrant-collection)
  - [Step 3 — Ingest PDF Structure](#step-3--ingest-pdf-structure)
    - [Expected Output](#expected-output)
  - [Step 4 — Index Embeddings into Qdrant](#step-4--index-embeddings-into-qdrant)
    - [Expected Output](#expected-output-1)
  - [Step 5 — Verify Point Counts](#step-5--verify-point-counts)
- [9. Run Evaluation Scenarios](#9-run-evaluation-scenarios)
  - [9.1 Run Scenario A Only](#91-run-scenario-a-only)
    - [Generated Files](#generated-files)
  - [9.2 Run Scenario B Only](#92-run-scenario-b-only)
    - [Generated Files](#generated-files-1)
  - [9.3 Run Full Evaluation](#93-run-full-evaluation)
- [10. Verify Output Counts](#10-verify-output-counts)
    - [Expected Counts](#expected-counts)
- [11. Run Tests](#11-run-tests)
    - [Latest Status](#latest-status)
- [12. Run Async Workers \& Backend Server](#12-run-async-workers--backend-server)
  - [12.1 Run Celery Worker](#121-run-celery-worker)
  - [12.2 Run FastAPI Server](#122-run-fastapi-server)
- [13. API Usage \& Real-Time DB Verification](#13-api-usage--real-time-db-verification)
  - [13.1 Health Check](#131-health-check)
  - [13.2 List Latest Document Sections](#132-list-latest-document-sections)
  - [13.3 Start a Prep Session](#133-start-a-prep-session)
    - [Response Example](#response-example)
  - [13.4 Track Worker Task Status](#134-track-worker-task-status)
  - [13.5 PostgreSQL Session Verification](#135-postgresql-session-verification)
  - [13.6 Submit Batch Answers](#136-submit-batch-answers)
  - [13.7 Verify Final Database State](#137-verify-final-database-state)
    - [Verify Session Updates](#verify-session-updates)
    - [Audit Question Schema](#audit-question-schema)
  - [13.8 Retrieve KB Snapshot](#138-retrieve-kb-snapshot)
- [14. PDF Section Mapping](#14-pdf-section-mapping)
- [15. Architecture Summary](#15-architecture-summary)
  - [Ingestion Architecture](#ingestion-architecture)
  - [Prep-Time Architecture](#prep-time-architecture)
- [16. LangGraph Workflow](#16-langgraph-workflow)
- [17. Knowledge Base Design](#17-knowledge-base-design)
- [18. Adaptation Strategy](#18-adaptation-strategy)
  - [Cold Start](#cold-start)
  - [Adaptive](#adaptive)
- [19. LLM and Model Choice](#19-llm-and-model-choice)
  - [Primary Engine](#primary-engine)
  - [Mock Framework](#mock-framework)
- [20. MCQ Validation](#20-mcq-validation)
- [21. Encoding Cleanup](#21-encoding-cleanup)
    - [Example](#example)
- [22. Project Speciality](#22-project-speciality)
- [23. Known Limitations](#23-known-limitations)
  - [LLM Non-Determinism](#llm-non-determinism)
  - [Cold Starts](#cold-starts)
- [24. Output Commit Strategy](#24-output-commit-strategy)
- [25. Suggested Recruiter Verification Flow](#25-suggested-recruiter-verification-flow)
- [26. Project Structure](#26-project-structure)
- [27. Useful Commands](#27-useful-commands)
  - [Service Boot](#service-boot)
  - [Database Purge](#database-purge)
  - [Pipeline Processing](#pipeline-processing)
  - [Workers \& API](#workers--api)
- [28. Development Note](#28-development-note)
  - [AI Tools Used](#ai-tools-used)
- [29. Final Project Pitch](#29-final-project-pitch)
  - [License](#license)

---

# 1. Project Highlights

This project implements the complete prep flow required by the assessment:

- User selects one or more PDF sections to study.
- The system checks prior prep history for those sections.
- The system retrieves only chunks from the selected sections.
- The system generates **N MCQs per selected section**.
- The system presents questions without exposing correct answers.
- The user or simulation submits answers.
- The system scores the session.
- Wrong answers receive correct answers and concise clarification.
- The session is persisted to PostgreSQL.
- Weak topics are updated from wrong answers.
- Future runs adapt question generation based on stored history.
- Scenario A and Scenario B outputs are exported for reviewer inspection.

### Core Adaptive Logic

```text
first-time relevant run -> cold_start
returning relevant run  -> adaptive
```

---

# 2. Current Verified Status

Core backend functionality is fully operational.

## Verified Features

```text
PDF ingestion                         Passed
10-section extraction                 Passed
PostgreSQL persistence                Passed
Qdrant indexing                       Passed
Strict selected-section retrieval     Passed
Groq MCQ generation                   Passed
Mock fallback generation              Passed
N=5 Scenario A/B generation           Passed
Backend-owned adaptation metadata     Passed
LLM retry reliability                 Improved
MCQ validation                        Passed
Scenario A                            Passed
Scenario B                            Passed
KB snapshot export                    Passed
FastAPI Swagger flow                  Passed
/prep/start                           Passed
/prep/task/{task_id}                  Passed
/prep/submit                          Passed
/sessions/{session_id}                Passed
/kb/snapshot                          Passed
Automated tests                       6 passed
```

### Latest Verified Adaptive Runs

```text
Scenario B iteration 1 | sections [5, 8]    | mode=cold_start | score=50.0
Scenario B iteration 2 | sections [6, 8, 9] | mode=adaptive   | score=66.67
Scenario B iteration 3 | sections [8]       | mode=adaptive   | score=0.0
```

---

# 3. Repository

```bash
https://github.com/bringerofdarkness/adaptive-document-prep-Cloudly
```

---

# 4. Prerequisites

## Recommended Environment

```text
Python 3.13+
Docker Desktop
Windows PowerShell or compatible terminal
Groq API key for real LLM generation
```

## Required Services

```text
PostgreSQL (Port 5433)
Qdrant (Port 16433)
Redis (Port 6380)
```

These services are started through Docker Compose.

---

# 5. Fresh Setup on a New PC

## 5.1 Clone the Repository

```powershell
git clone https://github.com/bringerofdarkness/adaptive-document-prep-Cloudly.git

cd adaptive-document-prep-Cloudly
```

---

## 5.2 Create and Activate a Virtual Environment

### Windows PowerShell

```powershell
python -m venv .venv

.\.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python -m venv .venv

source .venv/bin/activate
```

---

## 5.3 Install Dependencies

```powershell
python -m pip install --upgrade pip

python -m pip install -r requirements.txt
```

---

## 5.4 Create `.env`

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### macOS / Linux

```bash
cp .env.example .env
```

Then configure your Groq API key:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
```

### Optional Deterministic Local Testing

```env
LLM_PROVIDER=mock
```

> Never commit `.env`.

---

# 6. Environment Variables

```env
APP_NAME="Adaptive Document Preparation System"
APP_ENV=local

POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=adaptive_doc_prep
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

QDRANT_HOST=localhost
QDRANT_PORT=16433
QDRANT_COLLECTION=slatefall_chunks

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=

# Async Worker & Cache Layer
REDIS_HOST=localhost
REDIS_PORT=6380
REDIS_DB=0

CELERY_BROKER_URL=redis://localhost:6380/0
CELERY_RESULT_BACKEND=redis://localhost:6380/0

# Isolation Mode
HF_HUB_OFFLINE=1
```

---

# 7. Start Docker Services

```powershell
docker compose up -d
```

Check containers:

```powershell
docker ps
```

Expected services:

```text
adaptive_doc_postgres
adaptive_doc_qdrant
adaptive_doc_redis_6380
```

## Verify Services

### PostgreSQL

```powershell
docker exec adaptive_doc_postgres pg_isready -U postgres -d adaptive_doc_prep
```

### Qdrant

```powershell
Invoke-RestMethod http://127.0.0.1:16433/healthz
```

### Redis

```powershell
python -c "import redis; r = redis.Redis(host='localhost', port=6380, db=0); print('Redis Live:', r.ping())"
```

---

# 8. Prepare the Knowledge Base (Idempotent Setup)

The main PDF must exist at:

```text
data/SLATEFALL_DOSSIER.pdf
```

## Step 1 — Reset Relational Tables

```powershell
python -m cli.reset_db reset
```

---

## Step 2 — Clear Qdrant Collection

```powershell
Invoke-RestMethod -Uri http://localhost:16433/collections/slatefall_chunks -Method Delete
```

---

## Step 3 — Ingest PDF Structure

```powershell
python -m cli.ingest_pdf
```

### Expected Output

```text
Pages: 50
Sections: 10
Chunks: 101
```

---

## Step 4 — Index Embeddings into Qdrant

```powershell
python -m cli.index_qdrant
```

### Expected Output

```text
Chunks to index: 101
Qdrant indexing complete.
```

---

## Step 5 — Verify Point Counts

```powershell
Invoke-RestMethod -Uri http://localhost:16433/collections/slatefall_chunks
```

Ensure:

```text
points_count = 101
```

---

# 9. Run Evaluation Scenarios

The assessment requires exported outputs for both Scenario A and Scenario B.

---

## 9.1 Run Scenario A Only

```powershell
python -m cli.run_scenario_a --questions-per-section 5
```

### Generated Files

```text
outputs/scenario_a/questions_scenario_a.json
outputs/scenario_a/kb_snapshot_scenario_a.json
```

---

## 9.2 Run Scenario B Only

```powershell
python -m cli.run_scenario_b --questions-per-section 5
```

### Generated Files

```text
outputs/scenario_b_iter1/questions_iter1.json
outputs/scenario_b_iter1/kb_snapshot_iter1.json

outputs/scenario_b_iter2/questions_iter2.json
outputs/scenario_b_iter2/kb_snapshot_iter2.json

outputs/scenario_b_iter3/questions_iter3.json
outputs/scenario_b_iter3/kb_snapshot_iter3.json
```

---

## 9.3 Run Full Evaluation

```powershell
python -m cli.run_evaluation --questions-per-section 5
```

---

# 10. Verify Output Counts

```powershell
(Get-Content outputs\scenario_a\questions_scenario_a.json | ConvertFrom-Json).questions.Count

(Get-Content outputs\scenario_b_iter1\questions_iter1.json | ConvertFrom-Json).questions.Count

(Get-Content outputs\scenario_b_iter2\questions_iter2.json | ConvertFrom-Json).questions.Count

(Get-Content outputs\scenario_b_iter3\questions_iter3.json | ConvertFrom-Json).questions.Count
```

### Expected Counts

```text
10
10
15
5
```

---

# 11. Run Tests

```powershell
python -m pytest tests
```

### Latest Status

```text
6 passed
```

---

# 12. Run Async Workers & Backend Server

Open two separate terminals with active virtual environments.

---

## 12.1 Run Celery Worker

```powershell
celery -A app.background.worker.celery_app worker --loglevel=info -P solo
```

---

## 12.2 Run FastAPI Server

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 18000
```

Swagger UI:

```text
http://127.0.0.1:18000/docs
```

---

# 13. API Usage & Real-Time DB Verification

---

## 13.1 Health Check

```http
GET /health
```

---

## 13.2 List Latest Document Sections

```http
GET /documents/latest/sections
```

---

## 13.3 Start a Prep Session

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:18000/prep/start `
-Method Post `
-ContentType "application/json" `
-Body '{"selected_section_numbers": [5, 8], "questions_per_section": 5}'
```

### Response Example

```json
{
  "task_id": "6e007c87-d6db-44c4-96ba-6191764abca1",
  "status": "QUEUED",
  "message": "Adaptive generation pipeline initiated successfully in background thread workers."
}
```

---

## 13.4 Track Worker Task Status

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:18000/prep/task/6e007c87-d6db-44c4-96ba-6191764abca1
```

---

## 13.5 PostgreSQL Session Verification

```powershell
docker exec -it adaptive_doc_postgres psql -U postgres -d adaptive_doc_prep -c "SELECT id, mode, score, total_questions, selected_section_numbers FROM prep_sessions ORDER BY created_at DESC LIMIT 1;"
```

---

## 13.6 Submit Batch Answers

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:18000/prep/submit `
-Method Post `
-ContentType "application/json" `
-Body '{
  "session_id": "YOUR_SESSIONS_UUID_HERE",
  "answers": {
    "QUESTION_ID_1": "A",
    "QUESTION_ID_2": "B"
  }
}'
```

---

## 13.7 Verify Final Database State

### Verify Session Updates

```powershell
docker exec -it adaptive_doc_postgres psql -U postgres -d adaptive_doc_prep -c "SELECT id, score, correct_count, wrong_count FROM prep_sessions ORDER BY created_at DESC LIMIT 1;"
```

### Audit Question Schema

```powershell
docker exec -it adaptive_doc_postgres psql -U postgres -d adaptive_doc_prep -c "SELECT section_number, topic, difficulty, question_text, correct_answer FROM generated_questions LIMIT 2;"
```

> Press `q` to exit pager view.

---

## 13.8 Retrieve KB Snapshot

```http
GET /kb/snapshot
```

Returns a human-readable snapshot of the latest learning sequences.

---

# 14. PDF Section Mapping

| Section | Title | Pages |
|---|---|---|
| 1 | Identity, Background, and Public Status | 1–4 |
| 2 | Powers, Abilities, and Documented Limits | 4–11 |
| 3 | Origin and Key Historical Events | 11–15 |
| 4 | Equipment, Gear, and Specialized Technology | 15–22 |
| 5 | Operational Tactics and Combat Doctrine | 22–25 |
| 6 | Allies, Networks, and Known Affiliations | 25–30 |
| 7 | Adversaries and Documented Threats | 30–36 |
| 8 | Known Bases, Safehouses, and Operational Territory | 36–39 |
| 9 | Case Files: Documented Engagements and Incidents | 39–43 |
| 10 | Glossary, Codenames, and Reference Tables | 43–50 |

---

# 15. Architecture Summary

```text
PostgreSQL = Historical state, scoring, weak-topic tracking
Qdrant     = Section-filtered semantic retrieval
LangGraph  = Adaptive orchestration workflow
```

## Ingestion Architecture

```text
SLATEFALL_DOSSIER.pdf
        │
        ▼
PyMuPDF Page Extractor
        │
        ▼
Section Splitter
        │
        ├──► PostgreSQL Storage
        │
        └──► SentenceTransformers
                     │
                     ▼
               Qdrant Vector Store
```

## Prep-Time Architecture

```text
Target Selection
        │
        ▼
History Lookup
        │
        ▼
Qdrant Retrieval
        │
        ▼
LLM MCQ Generation
        │
        ▼
Pydantic Validation
        │
        ▼
Scoring + Persistence
```

---

# 16. LangGraph Workflow

```text
load_document_and_history
        │
        ▼
retrieve_selected_section_chunks
        │
        ▼
generate_questions
        │
        ▼
simulate_and_score_answers
        │
        ▼
persist_session
```

This guarantees deterministic tracking across adaptive Scenario B iterations.

---

# 17. Knowledge Base Design

Relational modeling handles historical performance indexing over semantic retrieval.

This allows:

- Weak-topic aggregation
- Historical session tracking
- Adaptive analytics
- Snapshot exports
- Reviewer-auditable persistence

---

# 18. Adaptation Strategy

## Cold Start

```text
No prior history exists for selected sections.
```

## Adaptive

```text
Previous mistakes and weak topics influence new question generation.
```

The backend explicitly owns adaptation metadata generation instead of delegating trust to LLM outputs.

---

# 19. LLM and Model Choice

## Primary Engine

```text
Groq Cloud Hosted API
```

Chosen for:

- Fast inference
- Strong JSON adherence
- Lightweight deployment requirements

## Mock Framework

Deterministic mock generation exists for:

- Offline testing
- Unit testing
- CI-safe execution

---

# 20. MCQ Validation

Validation pipeline guarantees:

- Exactly 4 answer choices
- Strict A/B/C/D schema
- Section-boundary enforcement
- Retry-on-invalid-generation behavior

---

# 21. Encoding Cleanup

The project uses `ftfy` normalization to repair mojibake parsing artifacts.

### Example

```text
Cuartel ValparaÃ­so
```

becomes

```text
Cuartel Valparaíso
```

---

# 22. Project Speciality

The main engineering focus is proving measurable adaptivity.

Scenario B demonstrates:

```text
failure in earlier sessions
            ↓
weak-topic persistence
            ↓
adaptive prompt steering
            ↓
targeted follow-up evaluation
```

---

# 23. Known Limitations

## LLM Non-Determinism

Minor output variance may occur across environments.

Mitigation:

```text
Low temperature configuration
Strict schema validation
Retry enforcement
```

---

## Cold Starts

Initial model loads may briefly delay first-run execution.

---

# 24. Output Commit Strategy

The `outputs/` directory stores reviewer-ready execution artifacts.

This avoids forcing reviewers to immediately rebuild the entire stack.

---

# 25. Suggested Recruiter Verification Flow

```powershell
# Start Services
docker compose up -d

# Reset & Rebuild State
python -m cli.reset_db reset
python -m cli.ingest_pdf
python -m cli.index_qdrant

# Run Tests
python -m pytest tests

# Execute Full Evaluation
python -m cli.run_evaluation --questions-per-section 5

# Start Backend
celery -A app.background.worker.celery_app worker --loglevel=info -P solo

python -m uvicorn app.main:app --host 127.0.0.1 --port 18000
```

---

# 26. Project Structure

```text
app/
├── api/           FastAPI route modules
├── core/          settings, logging, exceptions
├── db/            SQLAlchemy models, repositories
├── ingestion/     PDF parsing and chunking
├── retrieval/     Embeddings and Qdrant retrieval
├── llm/           Providers, prompts, validation
├── background/    Celery worker logic
├── workflow/      LangGraph graph orchestration
├── services/      Business logic
└── schemas/       Pydantic request/response schemas

cli/               CLI execution scripts
docs/              Architecture and strategy docs
outputs/           Scenario outputs and KB snapshots
tests/             Automated tests
```

---

# 27. Useful Commands

## Service Boot

```powershell
docker compose up -d
```

---

## Database Purge

```powershell
python -m cli.reset_db reset
```

---

## Pipeline Processing

```powershell
python -m cli.ingest_pdf

python -m cli.index_qdrant

python -m cli.run_evaluation --questions-per-section 5
```

---

## Workers & API

```powershell
celery -A app.background.worker.celery_app worker --loglevel=info -P solo

python -m uvicorn app.main:app --host 127.0.0.1 --port 18000
```

---

# 28. Development Note

This project was independently implemented and validated by the project author.

AI tools were used as supplementary assistants for:

- Brainstorming
- Debugging support
- Documentation refinement
- Reviewing implementation decisions

All final architectural decisions, implementation logic, testing, validation, and repository maintenance were reviewed and owned by the project author.

## AI Tools Used

- ChatGPT
- Google Gemini

---

# 29. Final Project Pitch

This project is a production-style adaptive RAG backend that:

- Ingests structured PDFs
- Stores semantic chunks in Qdrant
- Maintains learning history in PostgreSQL
- Generates MCQs using LLMs
- Validates structured outputs
- Scores answers
- Tracks weak topics over time
- Adapts future question generation based on previous mistakes
- Exports reviewer-ready Scenario A and Scenario B outputs

The project demonstrates deterministic adaptive preparation behavior across repeated study sessions while maintaining strict retrieval boundaries, persistence guarantees, and audit-ready evaluation outputs.

---


## License

This project is intended for educational, research, and engineering portfolio demonstration purposes.