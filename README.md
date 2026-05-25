# Adaptive Document Preparation System

<p align="center">
  <b>Production-Style Adaptive RAG Backend for PDF-Based Study Preparation & MCQ Generation</b>
</p>

<p align="center">
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

## Overview

A production-style adaptive RAG backend designed for structured PDF-based study preparation and intelligent MCQ generation.

This system:

- Ingests structured multi-section PDFs
- Stores relational learning history in PostgreSQL
- Stores semantic chunk embeddings in Qdrant
- Retrieves only user-selected sections
- Generates MCQs through an LLM
- Validates structured outputs
- Scores answer submissions
- Tracks weak topics over time
- Adapts future question generation using historical performance

The primary goal is not just retrieval-augmented generation — it is demonstrating **adaptive preparation behavior across repeated study sessions**.

---

# Documentation

<table>
<tr>
<th align="left">File</th>
<th align="left">Purpose</th>
</tr>

<tr>
<td>

<a href="docs/architecture.md">Architecture</a>

</td>
<td>
Hybrid RAG architecture and retrieval flow
</td>
</tr>

<tr>
<td>

<a href="docs/database_schema.md">Database Schema</a>

</td>
<td>
PostgreSQL schema and KB relationships
</td>
</tr>

<tr>
<td>

<a href="docs/adaptation_strategy.md">Adaptation Strategy</a>

</td>
<td>
Adaptive logic and weak-topic tracking
</td>
</tr>

<tr>
<td>

<a href="docs/optional_enhancements.md">Optional Enhancements</a>

</td>
<td>
Optional enhancements and scalability ideas
</td>
</tr>

</table>

---

## Recommended Reading Order

```text
1. docs/architecture.md
2. docs/database_schema.md
3. docs/adaptation_strategy.md
```

---

## Recommended Reading Order

```text
1. docs/architecture.md
2. docs/database_schema.md
3. docs/adaptation_strategy.md
```

---

## Recommended Reading Order

```text
1. docs/architecture.md
2. docs/database_schema.md
3. docs/adaptation_strategy.md
```

---

# Architecture Overview

```text
                           ┌────────────────────┐
                           │   Structured PDF   │
                           │ SLATEFALL_DOSSIER  │
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
  - [Overview](#overview)
- [Documentation](#documentation)
  - [Recommended Reading Order](#recommended-reading-order)
  - [Recommended Reading Order](#recommended-reading-order-1)
  - [Recommended Reading Order](#recommended-reading-order-2)
- [Architecture Overview](#architecture-overview)
- [Table of Contents](#table-of-contents)
- [1. Project Highlights](#1-project-highlights)
  - [Features](#features)
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
  - [Step 1 — Reset Database](#step-1--reset-database)
  - [Step 2 — Clear Qdrant Collection](#step-2--clear-qdrant-collection)
  - [Step 3 — Ingest PDF](#step-3--ingest-pdf)
  - [Step 4 — Index Embeddings](#step-4--index-embeddings)
  - [Step 5 — Verify Counts](#step-5--verify-counts)
- [9. Run Evaluation Scenarios](#9-run-evaluation-scenarios)
  - [9.1 Run Scenario A](#91-run-scenario-a)
  - [9.2 Run Scenario B](#92-run-scenario-b)
  - [9.3 Run Full Evaluation](#93-run-full-evaluation)
- [10. Verify Output Counts](#10-verify-output-counts)
- [11. Run Tests](#11-run-tests)
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
- [22. Project Speciality](#22-project-speciality)
- [23. Known Limitations](#23-known-limitations)
  - [LLM Non-Determinism](#llm-non-determinism)
  - [Cold Starts](#cold-starts)
- [24. Output Commit Strategy](#24-output-commit-strategy)
- [25. Suggested Project Verification Flow](#25-suggested-project-verification-flow)
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

This project implements the complete adaptive prep pipeline required by the assessment.

## Features

- User selects one or more PDF sections to study
- System checks previous prep history
- Strict selected-section retrieval
- MCQ generation per selected section
- Question delivery without exposing answers
- Batch answer submission
- Session scoring
- Weak-topic tracking
- Adaptive future question generation
- Scenario A and Scenario B export generation

---

## Core Adaptive Logic

```text
first-time relevant run -> cold_start
returning relevant run  -> adaptive
```

---

# 2. Current Verified Status

Core backend functionality is fully operational.

## Verified Features

```text
PDF ingestion                              Passed
10-section extraction                      Passed
PostgreSQL persistence                     Passed
Qdrant indexing                            Passed
Strict selected-section retrieval          Passed
Groq MCQ generation                        Passed
Mock fallback generation                   Passed
N=5 Scenario A/B generation                Passed
Backend-owned adaptation metadata          Passed
LLM retry reliability                      Improved
MCQ validation                             Passed
Scenario A                                 Passed
Scenario B                                 Passed
KB snapshot export                         Passed
FastAPI Swagger flow                       Passed
/prep/start                                Passed
/prep/task/{task_id}                       Passed
/prep/submit                               Passed
/sessions/{session_id}                     Passed
/kb/snapshot                               Passed
Automated tests                            6 passed
```

---

## Latest Verified Adaptive Runs

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

---

## Required Services

```text
PostgreSQL (Port 5433)
Qdrant (Port 16433)
Redis (Port 6380)
```

All services run through Docker Compose.

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

# If the global `python` command is not configured on your PC
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
py -m venv .venv
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

Configure your API key:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
```

---

## Optional Deterministic Local Testing

```env
LLM_PROVIDER=mock
```

> Never commit `.env`.

---

# 6. Environment Variables

```env
APP_NAME="Adaptive Document Preparation System"
APP_ENV=local
API_HOST=0.0.0.0
API_PORT=8000

POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=adaptive_doc_prep
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

QDRANT_HOST=localhost
QDRANT_PORT=16433
QDRANT_COLLECTION=slatefall_chunks

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

LLM_PROVIDER=mock
GEMINI_API_KEY=
GROQ_API_KEY=

# Redis & Celery Message Broker Configurations
REDIS_HOST=localhost
REDIS_PORT=6380
REDIS_DB=0
CELERY_BROKER_URL=redis://localhost:6380/0
CELERY_RESULT_BACKEND=redis://localhost:6380/0

# Algorithmic Retrieval Engineering Boundaries
QDRANT_SCORE_THRESHOLD=0.75   zx
```

---

# 7. Start Docker Services

```powershell
docker compose up -d
```

---

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

PDF location:

```text
data/SLATEFALL_DOSSIER.pdf
```

---

## Step 1 — Reset Database

```powershell
python -m cli.reset_db reset
```

---

## Step 2 — Clear Qdrant Collection

```powershell
Invoke-RestMethod -Uri http://localhost:16433/collections/slatefall_chunks -Method Delete
```

---

## Step 3 — Ingest PDF

```powershell
python -m cli.ingest_pdf
```

Expected:

```text
Pages: 50
Sections: 10
Chunks: 101
```

---

## Step 4 — Index Embeddings

```powershell
python -m cli.index_qdrant
```

Expected:

```text
Chunks to index: 101
Qdrant indexing complete.
```

---

## Step 5 — Verify Counts

```powershell
Invoke-RestMethod -Uri http://localhost:16433/collections/slatefall_chunks `
| Select-Object -ExpandProperty result `
| Select-Object status, points_count
```

Expected:

```text
status points_count
------ ------------
green           101
```

---

# 9. Run Evaluation Scenarios

---

## 9.1 Run Scenario A

```powershell
python -m cli.run_scenario_a --questions-per-section 5
```

Generated:

```text
outputs/scenario_a/questions_scenario_a.json
outputs/scenario_a/kb_snapshot_scenario_a.json
```

---

## 9.2 Run Scenario B

```powershell
python -m cli.run_scenario_b --questions-per-section 5
```

Generated:

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

Expected:

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

Expected:

```text
6 passed
```

---

# 12. Run Async Workers & Backend Server

Open two terminals.

---

## 12.1 Run Celery Worker

```powershell
$env:PYTHONPATH="."

celery -A app.core.celery_app.celery_app worker --loglevel=info -P solo
```

---

## 12.2 Run FastAPI Server

```powershell
$env:PYTHONPATH="."

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
-Body '{
  "selected_section_numbers": [5, 8],
  "questions_per_section": 5
}'
```


---

## Response Example

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
Invoke-RestMethod -Uri http://127.0.0.1:18000/prep/task/Your-Task-ID
```

---

## 13.5 PostgreSQL Session Verification

```powershell
docker exec -it adaptive_doc_postgres psql -U postgres -d adaptive_doc_prep `
-c "SELECT id, mode, score, total_questions, selected_section_numbers FROM prep_sessions ORDER BY created_at DESC LIMIT 1;"
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
docker exec -it adaptive_doc_postgres psql -U postgres -d adaptive_doc_prep `
-c "SELECT id, score, correct_count, wrong_count FROM prep_sessions ORDER BY created_at DESC LIMIT 1;"
```

### Audit Question Schema

```powershell
docker exec -it adaptive_doc_postgres psql -U postgres -d adaptive_doc_prep `
-c "SELECT section_number, topic, difficulty, question_text, correct_answer FROM generated_questions LIMIT 2;"
```

---

## 13.8 Retrieve KB Snapshot

```http
GET /kb/snapshot
```

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

---

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

---

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

---

# 17. Knowledge Base Design

Relational modeling enables:

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

---

## Adaptive

```text
Previous mistakes and weak topics influence future question generation.
```

The backend explicitly owns adaptation metadata generation rather than delegating trust to LLM outputs.

---

# 19. LLM and Model Choice

## Primary Engine

```text
Groq Cloud Hosted API
```

Benefits:

- Fast inference
- Strong JSON adherence
- Lightweight deployment requirements

---

## Mock Framework

Used for:

- Offline testing
- Unit testing
- CI-safe execution

---

# 20. MCQ Validation

Validation guarantees:

- Exactly 4 answer choices
- Strict A/B/C/D schema
- Section-boundary enforcement
- Retry-on-invalid-generation behavior

---

# 21. Encoding Cleanup

The project uses `ftfy` normalization to repair mojibake artifacts.

Example:

```text
Cuartel ValparaÃ­so
```

becomes:

```text
Cuartel Valparaíso
```

---

# 22. Project Speciality

Main engineering contribution:

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

Minor variance may occur across environments.

Mitigated using:

```text
Low temperature configuration
Strict schema validation
Retry enforcement
```

---

## Cold Starts

Initial model loads may delay first-run execution slightly.

---

# 24. Output Commit Strategy

The `outputs/` directory stores reviewer-ready execution artifacts for rapid evaluation.

---

# 25. Suggested Project Verification Flow

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

# Start Worker
$env:PYTHONPATH="."
celery -A app.core.celery_app.celery_app worker --loglevel=info -P solo

# Start API (Separate Terminal)
$env:PYTHONPATH="."
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
$env:PYTHONPATH="."

celery -A app.core.celery_app.celery_app worker --loglevel=info -P solo

$env:PYTHONPATH="."

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

All final architecture, implementation, testing, validation, and maintenance decisions were reviewed and owned by the project author.

---

## AI Tools Used

- ChatGPT
- Google Gemini

---

# 29. Final Project Pitch

This project demonstrates a production-style adaptive RAG backend that:

- Ingests structured PDFs
- Stores semantic embeddings in Qdrant
- Maintains learning history in PostgreSQL
- Generates MCQs using LLMs
- Validates structured outputs
- Scores answer submissions
- Tracks weak topics
- Adapts future question generation
- Exports reviewer-ready Scenario outputs

The system demonstrates deterministic adaptive preparation behavior across repeated study sessions while maintaining strict retrieval boundaries, persistence guarantees, and audit-ready evaluation outputs.

---

# License

This project is intended for educational, research, and engineering portfolio demonstration purposes.