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

| Layer | Technology | Purpose |
|---|---|---|
| Backend API | FastAPI | REST API, Swagger testing, interactive prep flow |
| Workflow orchestration | LangGraph | Stateful CLI workflow for loading history, retrieving chunks, generating MCQs, scoring answers, persisting sessions, and supporting adaptive Scenario B |
| Relational Knowledge Base | PostgreSQL | Documents, sections, chunks, sessions, answers, weak topics, and KB snapshots |
| Vector retrieval | Qdrant | Semantic retrieval over PDF chunks with strict section filtering |
| Embeddings | SentenceTransformers model: `all-MiniLM-L6-v2` | Converts PDF chunks into vectors before storing/searching them in Qdrant |
| LLM provider | Groq | Real MCQ generation with free/developer-friendly API access |
| Optional LLM provider | Gemini scaffold | Alternative provider path if configured |
| Local fallback | Mock provider | Deterministic local testing without external LLM key |
| PDF parsing | PyMuPDF | PDF page loading and text extraction |
| ORM | SQLAlchemy | Database models and persistence layer |
| CLI | Typer | Scenario A, Scenario B, ingestion, indexing, and evaluation commands |
| Testing | Pytest | Validation, scoring, and API contract tests |
| Container services | Docker Compose | PostgreSQL and Qdrant runtime services |
| Text cleanup | ftfy | Unicode/mojibake cleanup for LLM and PDF text |

---
## Documentation

For deeper technical review, see the documentation files below.

| File | Purpose |
|---|---|
| [Architecture](docs/architecture.md) | Hybrid RAG architecture, LangGraph workflow, retrieval flow, API flow, and component responsibilities |
| [Database Schema](docs/database_schema.md) | PostgreSQL schema, table relationships, Knowledge Base query patterns, weak-topic storage, and KB snapshot design |
| [Adaptation Strategy](docs/adaptation_strategy.md) | Cold-start vs adaptive logic, weak-topic tracking, Scenario B behavior, backend-owned adaptation reasons, and history-aware generation |

Recommended reading order:

```text
1. docs/architecture.md
2. docs/database_schema.md
3. docs/adaptation_strategy.md
```
---

## Index
 
- [Adaptive Document Preparation System](#adaptive-document-preparation-system)
  - [Tech Stack](#tech-stack)
  - [Documentation](#documentation)
  - [Index](#index)
  - [1. Project Highlights](#1-project-highlights)
  - [2. Current Verified Status](#2-current-verified-status)
  - [3. Repository](#3-repository)
  - [4. Prerequisites](#4-prerequisites)
  - [5. Fresh Setup on a New PC](#5-fresh-setup-on-a-new-pc)
    - [5.1 Clone the repository](#51-clone-the-repository)
    - [5.2 Create and activate a virtual environment](#52-create-and-activate-a-virtual-environment)
    - [5.3 Install dependencies](#53-install-dependencies)
    - [5.4 Create `.env`](#54-create-env)
  - [6. Environment Variables](#6-environment-variables)
  - [7. Start Docker Services](#7-start-docker-services)
  - [9. Run Evaluation Scenarios](#9-run-evaluation-scenarios)
    - [9.1 Run Scenario A only](#91-run-scenario-a-only)
    - [9.2 Run Scenario B only](#92-run-scenario-b-only)
    - [9.3 Run full evaluation](#93-run-full-evaluation)
  - [10. Verify Output Counts](#10-verify-output-counts)
  - [11. Run Tests](#11-run-tests)
    - [11.2 Run Celery Background Workers](#112-run-celery-background-workers)
  - [12. Run the FastAPI Server](#12-run-the-fastapi-server)
  - [13. API Usage](#13-api-usage)
    - [13.1 Health check](#131-health-check)
    - [13.2 List latest document sections](#132-list-latest-document-sections)
    - [13.3 Start a prep session](#133-start-a-prep-session)
      - [13.3.2 Track Worker Task Generation Status](#1332-track-worker-task-generation-status)
    - [13.4 Submit answers](#134-submit-answers)
    - [13.5 Retrieve a session](#135-retrieve-a-session)
    - [13.6 Retrieve KB snapshot](#136-retrieve-kb-snapshot)
  - [14. PDF Section Mapping](#14-pdf-section-mapping)
  - [15. Architecture Summary](#15-architecture-summary)
    - [Ingestion Architecture](#ingestion-architecture)
    - [Prep-Time Architecture](#prep-time-architecture)
  - [16. LangGraph Workflow](#16-langgraph-workflow)
    - [Workflow Nodes](#workflow-nodes)
    - [Workflow State](#workflow-state)
    - [Why LangGraph Matters](#why-langgraph-matters)
  - [17. Knowledge Base Design](#17-knowledge-base-design)
    - [Why PostgreSQL Is Used](#why-postgresql-is-used)
    - [Why Qdrant Is Separate](#why-qdrant-is-separate)
  - [18. Adaptation Strategy](#18-adaptation-strategy)
  - [19. LLM and Model Choice](#19-llm-and-model-choice)
    - [Primary LLM: Groq](#primary-llm-groq)
    - [Mock fallback](#mock-fallback)
    - [Why not only Gemini?](#why-not-only-gemini)
    - [Why not only Ollama/local LLM?](#why-not-only-ollamalocal-llm)
    - [Why not only HuggingFace generation?](#why-not-only-huggingface-generation)
  - [20. MCQ Validation](#20-mcq-validation)
  - [21. Encoding Cleanup](#21-encoding-cleanup)
  - [22. Project Speciality](#22-project-speciality)
  - [23. Known Limitations](#23-known-limitations)
    - [LLM non-determinism](#llm-non-determinism)
    - [First run can be slow](#first-run-can-be-slow)
    - [HuggingFace token warning](#huggingface-token-warning)
    - [API mode depends on existing history](#api-mode-depends-on-existing-history)
    - [No frontend](#no-frontend)
    - [Docker scope](#docker-scope)
  - [24. Output Commit Strategy](#24-output-commit-strategy)
  - [25. Suggested Recruiter Verification Flow](#25-suggested-recruiter-verification-flow)
    - [25.1 Start services](#251-start-services)
    - [25.2 Reset and rebuild the KB](#252-reset-and-rebuild-the-kb)
    - [25.3 Run full evaluation](#253-run-full-evaluation)
    - [25.4 Verify final Scenario B result](#254-verify-final-scenario-b-result)
    - [25.5 Run tests](#255-run-tests)
    - [25.6 Run API](#256-run-api)
  - [26. Project Structure](#26-project-structure)
  - [27. Useful Commands](#27-useful-commands)
  - [28. Development Note](#28-development-note)
  - [29. Final Project Pitch](#29-final-project-pitch)

---

## 1. Project Highlights

This project implements the complete prep flow required by the assessment:

1. User selects one or more PDF sections to study.
2. The system checks prior prep history for those sections.
3. The system retrieves only chunks from the selected sections.
4. The system generates `N` MCQs per selected section.
5. The system presents questions without exposing correct answers.
6. The user or simulation submits answers.
7. The system scores the session.
8. Wrong answers receive the correct answer and a concise clarification.
9. The session is persisted to PostgreSQL.
10. Weak topics are updated from wrong answers.
11. Future runs adapt question generation based on stored history.
12. Scenario A and Scenario B outputs are exported for reviewer inspection.

The most important feature is adaptive intelligence:

```text
first-time relevant run -> cold_start
returning relevant run  -> adaptive
```

---

## 2. Current Verified Status

Core backend functionality is working.

Verified items:

```text
PDF ingestion                         Passed
10-section extraction                  Passed
PostgreSQL persistence                 Passed
Qdrant indexing                        Passed
Strict selected-section retrieval      Passed
Groq MCQ generation                    Passed
Mock fallback generation               Passed
N=5 Scenario A/B generation            Passed
Backend-owned adaptation metadata      Passed
LLM retry reliability                  Improved
MCQ validation                         Passed
Scenario A                             Passed
Scenario B                             Passed
KB snapshot export                     Passed
FastAPI Swagger flow                   Passed
/prep/start                            Passed
/prep/submit                           Passed
/sessions/{session_id}                 Passed
/kb/snapshot                           Passed
Automated tests                        6 passed
```

Latest verified Scenario B behavior with `5` questions per selected section:

```text
Scenario B iteration 1 | sections [5, 8]    | mode=cold_start | score=50.0
Scenario B iteration 2 | sections [6, 8, 9] | mode=adaptive   | score=66.67
Scenario B iteration 3 | sections [8]       | mode=adaptive   | score=0.0
```

---

## 3. Repository

```text
https://github.com/bringerofdarkness/adaptive-document-prep-Cloudly
```

---

## 4. Prerequisites

Recommended environment:

```text
Python 3.13+
Docker Desktop
Windows PowerShell or compatible terminal
Groq API key for real LLM generation
```

Required services:

```text
PostgreSQL
Qdrant
Redis (Port 6380)
```

These services are started through Docker Compose.

---

## 5. Fresh Setup on a New PC

### 5.1 Clone the repository

```powershell
git clone https://github.com/bringerofdarkness/adaptive-document-prep-Cloudly.git
cd adaptive-document-prep-Cloudly
```

### 5.2 Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 5.3 Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5.4 Create `.env`

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Then edit `.env` and set your Groq API key:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
```

For deterministic local testing without an external LLM, use:

```env
LLM_PROVIDER=mock
```

Do not commit `.env`.

---

## 6. Environment Variables

Example `.env` values:

```env
APP_NAME=Adaptive Document Preparation System
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

# Asynchronous Worker & Cache Layer Configurations
REDIS_HOST=localhost
REDIS_PORT=6380
REDIS_DB=0
CELERY_BROKER_URL=redis://localhost:6380/0
CELERY_RESULT_BACKEND=redis://localhost:6380/0

# Isolation Mode for Local Embeddings
HF_HUB_OFFLINE=1
```

Local FastAPI is normally run on port `18000`:

```text
[http://127.0.0.1:18000/docs](<http://127.0.0.1:18000/docs](http://127.0.0.1:18000/docs>)
```

---

## 7. Start Docker Services

Start PostgreSQL and Qdrant:

```powershell
docker compose up -d
```

Check containers:

```powershell
docker ps
```

Expected containers:

```text
adaptive_doc_postgres
adaptive_doc_qdrant
adaptive_doc_redis_6380
```

Check PostgreSQL:

```powershell
docker exec adaptive_doc_postgres pg_isready -U postgres -d adaptive_doc_prep
```

Check Qdrant:

```powershell
Invoke-RestMethod [http://127.0.0.1:16433/healthz](http://127.0.0.1:16433/healthz)
```

Expected Qdrant result:

```text
healthz check passed
```
Check Redis connection status and availability:
```powershell
.\.venv\Scripts\python.exe -c "import redis; r = redis.Redis(host='localhost', port=6380, db=0); print('Redis Live:', r.ping())"
```
Expected Redis result:

```text
Redis Live: True

---

## 8. Prepare the Knowledge Base

The main PDF is expected at:

```text
data/SLATEFALL_DOSSIER.pdf
```

Reset database tables:

```powershell
python -m cli.reset_db reset
```

Ingest the PDF into PostgreSQL:

```powershell
python -m cli.ingest_pdf
```

Expected ingestion result:

```text
Pages: 50
Sections: 10
Chunks: 101
```

Index chunks into Qdrant:

```powershell
python -m cli.index_qdrant
```

Expected indexing result:

```text
Chunks to index: 101
Qdrant indexing complete.
```

---

## 9. Run Evaluation Scenarios

The assessment requires exported outputs for Scenario A and Scenario B.

The final verified output scale is:

```text
5 questions per selected section
```

### 9.1 Run Scenario A only

Scenario A runs a cold-start prep over two sections.

```powershell
python -m cli.run_scenario_a --questions-per-section 5
```

Expected result:

```text
Scenario A complete | mode=cold_start | score=50.0
```

Generated files:

```text
outputs/scenario_a/questions_scenario_a.json
outputs/scenario_a/kb_snapshot_scenario_a.json
```

### 9.2 Run Scenario B only

Scenario B is the main adaptive proof.

```powershell
python -m cli.run_scenario_b --questions-per-section 5
```

Scenario B uses the assessment-required section sequence:

```text
Iteration 1: sections [5, 8]
Iteration 2: sections [6, 8, 9]
Iteration 3: sections [8]
```

Expected result:

```text
Scenario B iteration 1 complete | mode=cold_start | score=50.0
Scenario B iteration 2 complete | mode=adaptive   | score=66.67
Scenario B iteration 3 complete | mode=adaptive   | score=0.0
```

Generated files:

```text
outputs/scenario_b_iter1/questions_iter1.json
outputs/scenario_b_iter1/kb_snapshot_iter1.json

outputs/scenario_b_iter2/questions_iter2.json
outputs/scenario_b_iter2/kb_snapshot_iter2.json

outputs/scenario_b_iter3/questions_iter3.json
outputs/scenario_b_iter3/kb_snapshot_iter3.json
```

### 9.3 Run full evaluation

```powershell
python -m cli.run_evaluation --questions-per-section 5
```

Expected result:

```text
Running Scenario A...
Scenario A complete | mode=cold_start | score=50.0

Running Scenario B...
Scenario B iteration 1 complete | mode=cold_start | score=50.0
Scenario B iteration 2 complete | mode=adaptive | score=66.67
Scenario B iteration 3 complete | mode=adaptive | score=0.0

Evaluation complete. Outputs are available under the outputs directory.
```

---

## 10. Verify Output Counts

After running full evaluation with `--questions-per-section 5`, the expected question counts are:

```text
Scenario A:              10 questions
Scenario B iteration 1:  10 questions
Scenario B iteration 2:  15 questions
Scenario B iteration 3:   5 questions
```

PowerShell checks:

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

## 11. Run Tests

Run the automated test suite:

```powershell
python -m pytest tests
```

Latest verified result:

```text
6 passed
```

Current tests cover:

```text
MCQ validation
Out-of-selected-section rejection
Invalid question distribution rejection
Scoring logic
/prep/start API contract
/prep/submit API contract
```
### 11.2 Run Celery Background Workers

```powershell
python -m pytest tests
```

---

## 12. Run the FastAPI Server

Start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 18000
```

Open Swagger:

```text
http://127.0.0.1:18000/docs
```

Available endpoints:

```text
GET  /health
GET  /documents/latest/sections
GET  /documents/{document_id}/sections
POST /prep/start
POST /prep/submit
GET  /sessions
GET  /sessions/{session_id}
GET  /kb/snapshot
```

---

## 13. API Usage

### 13.1 Health check

```text
GET /health
```

Expected response:

```json
{
  "status": "ok",
  "service": "Adaptive Document Preparation System",
  "environment": "local"
}
```

### 13.2 List latest document sections

```text
GET /documents/latest/sections
```

This returns all extracted PDF sections with page ranges and chunk counts.

The current PDF exposes 10 sections.

### 13.3 Start a prep session

```text
POST /prep/start
```

Request:

```json
{
  "selected_section_numbers": [5, 8],
  "questions_per_section": 1
}
```

Important behavior:

```text
/prep/start returns questions and options.
It does not expose correct_answer.
It does not expose explanation.
```

Example response shape:

```json
{
  "task_id": "9f194adb-409b-476a-a2e3-b368e5bd0159",
  "status": "QUEUED",
  "message": "Adaptive generation pipeline initiated successfully in background thread workers."
}
```
#### 13.3.2 Track Worker Task Generation Status
```text
GET /prep/tasks/{task_id}
```

Request:

```json
{
  "task_id": "9f194adb-409b-476a-a2e3-b368e5bd0159",
  "status": "SUCCESS",
  "session_id": "2f85a094-bb62-4aae-968f-6dfd70941eb8",
  "total_questions": 6,
  "selected_sections": [5, 8]
}
```

Example response shape:

```json
{
    "task_id": "a6f92a4e-4edc-41d2-9539-985bcd445c72",
  "status": "SUCCESS",
  "result": {
    "session_id": "4063d76e-13e0-4296-aec7-231139f555f7",
    "document_id": "33283ea0-348f-44e1-9bbf-b20f381ebd57",
    "mode": "adaptive",
    "selected_sections": [
      1,
      2
    ],
    "total_questions": 2,
    "adaptation_summary": "Adaptive run: prior history found, but no repeated weak topics yet. Generate fresh coverage while avoiding mastered repetition.",
    "questions": [
      {
        "question_id": "a8c9878e-585b-4302-a1a1-650340c05abe",
        "section_number": 1,
        "topic": "Physical Description",
        "difficulty": "easy",
        "question": "What is the height of the subject?",
        "options": {
          "A": "1.68 m",
          "B": "1.70 m",
          "C": "1.72 m",
          "D": "1.75 m"
        },
        "adaptation_reason": "Returning-run question generated using previous session history without a section-specific weak topic."
      },
      {
        "question_id": "1103d9a6-259c-4833-a74f-14178d763262",
        "section_number": 2,
        "topic": "Sensory Deprivation",
        "difficulty": "medium",
        "question": "What is the effect of visual occlusion for more than 40 minutes?",
        "options": {
          "A": "Permanent power suppression",
          "B": "Transient power suppression",
          "C": "No effect on power",
          "D": "Increased power"
        },
        "adaptation_reason": "Returning-run question generated using previous session history without a section-specific weak topic."
      }
    ]
  }
}
}
```

### 13.4 Submit answers

```text
POST /prep/submit
```

Request format:

```json
{
  "session_id": "session-id",
  "answers": {
    "question-id-1": "A",
    "question-id-2": "B"
  }
}
```

Important behavior:

```text
/prep/submit scores the session.
/prep/submit returns correct_answer after submission.
/prep/submit returns clarification for wrong answers.
```

Example response shape:

```json
{
  "session_id": "session-id",
  "score": 50,
  "total_questions": 2,
  "correct_count": 1,
  "wrong_count": 1,
  "results": [
    {
      "question_id": "question-id",
      "section_number": 8,
      "topic": "Operational Territory",
      "selected_answer": "B",
      "correct_answer": "A",
      "is_correct": false,
      "clarification": "The primary operational base is Cuartel Valparaíso."
    }
  ]
}
```

### 13.5 Retrieve a session

```text
GET /sessions/{session_id}
```

This returns:

```text
session metadata
selected sections
score
correct and wrong counts
adaptation payload
weak topics
previous wrong question texts
mastered question texts
question-level results
user answers
correct answers
explanations
adaptation reasons
```

### 13.6 Retrieve KB snapshot

```text
GET /kb/snapshot
```

This returns a human-readable snapshot of the top 5 most recent sessions, including question-level history and weak-topic statistics.

This endpoint supports the assessment requirement that reviewers can verify the stored history behind adaptive prompting.

---

## 14. PDF Section Mapping

The current PDF parser detects these sections:

| Section | Title | Pages |
|---:|---|---:|
| 1 | Identity, Background, and Public Status | 1-4 |
| 2 | Powers, Abilities, and Documented Limits | 4-11 |
| 3 | Origin and Key Historical Events | 11-15 |
| 4 | Equipment, Gear, and Specialized Technology | 15-22 |
| 5 | Operational Tactics and Combat Doctrine | 22-25 |
| 6 | Allies, Networks, and Known Affiliations | 25-30 |
| 7 | Adversaries and Documented Threats | 30-36 |
| 8 | Known Bases, Safehouses, and Operational Territory | 36-39 |
| 9 | Case Files: Documented Engagements and Incidents | 39-43 |
| 10 | Glossary, Codenames, and Reference Tables | 43-50 |

Users can select one or more sections from this list.

---

## 15. Architecture Summary

The system uses a **hybrid-storage adaptive RAG architecture**: PostgreSQL stores the auditable source of truth and learning history, Qdrant stores semantic PDF chunk embeddings for selected-section retrieval, and LangGraph orchestrates the multi-step CLI preparation workflow that turns prior history into adaptive MCQ generation.

The design separates three responsibilities clearly:

```text
PostgreSQL = source of truth, learning history, scoring, adaptation, KB snapshots
Qdrant     = semantic retrieval over PDF chunks
LangGraph  = orchestration layer for the multi-step prep workflow
```

This separation is important because the project is not only retrieving PDF text. It is also storing learning history and using that history to adapt future question generation.

### Ingestion Architecture

```text
SLATEFALL_DOSSIER.pdf
 |
 |-- PyMuPDF loader
 |     reads PDF pages
 |
 |-- Section parser
 |     detects structured sections 1-10
 |
 |-- Chunker
 |     splits section text into retrievable chunks
 |
 |-- PostgreSQL
 |     stores document, section, and chunk records
 |
 |-- Embedding model
 |     creates semantic vectors for chunks
 |
 |-- Qdrant
       stores chunk embeddings with section metadata filters
```

PostgreSQL keeps the original structured document data. Qdrant only stores semantic vectors and retrieval metadata.

### Prep-Time Architecture

```text
User-selected sections
 |
 |-- PostgreSQL history lookup
 |     checks previous sessions involving selected sections
 |
 |-- Adaptation service
 |     builds cold_start or adaptive payload
 |
 |-- Qdrant retrieval
 |     retrieves only chunks from selected sections
 |
 |-- LLM MCQ generation
 |     generates questions from retrieved section context
 |
 |-- Validation layer
 |     enforces 4 options, correct answer, explanation, section validity, and N questions per section
 |
 |-- Scoring service
 |     marks correct and wrong answers
 |
 |-- PostgreSQL persistence
 |     stores session, questions, answers, score, and weak-topic updates
 |
 |-- Snapshot/export layer
       writes questions JSON and KB snapshot JSON for reviewer verification
```

The most important architectural rule is:

```text
The vector store retrieves knowledge.
The relational database proves learning history.
The workflow layer connects the full adaptive process.
```

Qdrant does not store session truth, scores, answers, or weak topics. It only supports retrieval. PostgreSQL stores the auditable learning history required for adaptation.

For deeper architecture details, see:

```text
docs/architecture.md
```

---

## 16. LangGraph Workflow

The CLI preparation flow uses **LangGraph** to orchestrate the end-to-end adaptive prep pipeline.

LangGraph is used because the prep flow is stateful and multi-step. Each step depends on the previous step, and the final result must preserve a clear chain from selected sections to retrieval, generation, scoring, persistence, and future adaptation.

### Workflow Nodes

```text
load_document_and_history
retrieve_selected_section_chunks
generate_questions
simulate_and_score_answers
persist_session
```

### Workflow State

The graph carries important runtime state across the full pipeline:

```text
db
document
selected_section_numbers
questions_per_section
simulation_strategy
adaptation_payload
retrieved_chunks
mcq_set
answer_map
scoring_payload
session
result
```

### Why LangGraph Matters

LangGraph makes the adaptive workflow explicit:

```text
previous PostgreSQL history
 |
 |-- adaptation payload
 |
 |-- selected-section retrieval
 |
 |-- MCQ generation
 |
 |-- scoring
 |
 |-- persisted new history
 |
 |-- future adaptive runs
```

This is especially important for Scenario B. Iteration 2 and iteration 3 depend on the history created by earlier iterations. LangGraph keeps this process structured instead of hiding it inside one large function.

Main files:

```text
app/workflow/state.py
app/workflow/nodes.py
app/workflow/prep_graph.py
app/services/prep_service.py
```

---


## 17. Knowledge Base Design

PostgreSQL is the system’s Knowledge Base for learning history.

It supports the assessment-required query patterns:

```text
Given selected section IDs, retrieve prior prep sessions involving those sections.
Given a session, retrieve question-level right/wrong results.
Identify topics/questions answered incorrectly across multiple sessions.
Retrieve a KB snapshot at the end of a session.
```

Main persisted entities:

```text
documents
sections
chunks
prep_sessions
generated_questions
user_answers
weak_topic_stats
kb_snapshots
```

### Why PostgreSQL Is Used

PostgreSQL is used because adaptation requires structured, queryable history.

The system needs to know:

```text
which sections were selected
which questions were asked
which answers were correct or wrong
which topics became weak
which sessions are relevant to the next run
what the KB looked like after each iteration
```

This is why PostgreSQL is treated as the source of truth.

### Why Qdrant Is Separate

Qdrant is optimized for semantic retrieval, not relational learning history.

The system uses Qdrant to find relevant chunks from selected sections, but it uses PostgreSQL to prove and explain adaptive behavior.

For schema details and access patterns, see:

```text
docs/database_schema.md
```

---

## 18. Adaptation Strategy

Adaptation is built from stored PostgreSQL history.

The adaptation service creates:

```text
is_returning_run
mode
relevant_prior_session_count
weak_topics
mastered_question_texts
previous_wrong_question_texts
summary
```

Mode rules:

```text
No relevant prior history -> cold_start
Relevant prior history    -> adaptive
```

Backend-owned adaptation metadata is used in final MCQ outputs.

This is intentional:

```text
The LLM generates question content.
The backend owns adaptation_reason based on real history.
```

This prevents the model from falsely claiming weak-topic adaptation during cold-start runs.

Example final behavior:

```text
Scenario B iteration 1:
mode = cold_start
adaptation_reason = Cold-start coverage question generated from the selected section because no prior relevant learning history exists.

Scenario B iteration 2:
section 6 = returning-run question without section-specific weakness
section 8 = adaptive question because section 8 is weak

Scenario B iteration 3:
section 8 = adaptive weak-section questions
```

For full adaptation details, see:

```text
docs/adaptation_strategy.md
```

---

## 19. LLM and Model Choice

### Primary LLM: Groq

Groq is used as the primary hosted LLM provider because:

```text
It is fast for development and evaluation.
It has a free/developer-friendly access path.
It works well for structured JSON-style MCQ generation.
It avoids requiring reviewers to run a local GPU model.
```

Configured with:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
```

### Mock fallback

A mock provider is included because:

```text
It allows deterministic local testing.
It allows tests to run without external API calls.
It helps validate the backend flow independently of LLM availability.
```

Configured with:

```env
LLM_PROVIDER=mock
```

### Why not only Gemini?

Gemini support is scaffolded as optional, but Groq is the primary provider to keep the final evaluation path simple and fast.

### Why not only Ollama/local LLM?

A local LLM would reduce external API dependency, but it would make reviewer setup heavier because model downloads and local hardware performance vary widely.

### Why not only HuggingFace generation?

The project already uses HuggingFace sentence-transformer embeddings locally. For MCQ generation, hosted LLM inference through Groq gives better response speed and quality for this project.

---

## 20. MCQ Validation

The backend does not blindly trust LLM output.

Validation checks include:

```text
exactly 4 options
options must be A, B, C, D
correct answer must be A, B, C, or D
non-empty topic
non-empty explanation
non-empty adaptation_reason
only selected-section questions
expected number of questions per section
duplicate question text handling
Pydantic schema validation
```

Validation files:

```text
app/llm/output_parser.py
app/schemas/question.py
```

If the LLM under-generates or returns malformed questions, the system retries section-level generation before failing.

---

## 21. Encoding Cleanup

LLM and PDF text can sometimes contain mojibake, for example:

```text
Cuartel ValparaÃ­so
```

The expected cleaned form is:

```text
Cuartel Valparaíso
```

The project uses `ftfy` for general Unicode/mojibake cleanup.

This is intentionally not a hardcoded word-specific replacement.

---

## 22. Project Speciality

The project is stronger than a basic RAG demo because it includes:

```text
real PDF ingestion
real section extraction
PostgreSQL source-of-truth storage
Qdrant vector retrieval
strict section-filtered retrieval
LLM-generated MCQs
strict output validation
session scoring
weak-topic tracking
adaptive future generation
Scenario B proof of adaptation
FastAPI interactive flow
reviewer-ready JSON outputs
KB snapshots with recent session history
```

The most important proof is Scenario B:

```text
Iteration 1 creates weakness in section 8.
Iteration 2 detects section 8 weakness while also handling sections 6 and 9.
Iteration 3 focuses only on section 8 and remains adaptive.
```

---

## 23. Known Limitations

### LLM non-determinism

Groq output can vary between runs. The backend mitigates this through:

```text
compact prompts
section-by-section generation
strict validation
retry logic
backend-owned adaptation metadata
```

Still, very poor LLM responses can fail validation.

### First run can be slow

The first API or evaluation run may take several minutes because:

```text
the embedding model may load into memory
the LLM generates many questions
Scenario A/B with N=5 generates 40 total MCQs
```

This is expected.

### HuggingFace token warning

The console may show:

```text
Warning: You are sending unauthenticated requests to the HF Hub.
```

This is not a failure. The embedding model still loads. Setting `HF_TOKEN` may improve rate limits.

### API mode depends on existing history

If the database already contains Scenario B or API sessions, `/prep/start` may return:

```text
mode = adaptive
```

This is expected.

For a clean cold-start API test, reset the database first.

### No frontend

A frontend is not included because the assessment asks for:

```text
CLI-runnable system
REST APIs
exported evaluation outputs
```

Swagger is used for API interaction.

### Docker scope

Docker Compose is used for PostgreSQL and Qdrant services. The FastAPI app can be run locally through Uvicorn. If the Dockerfile is used for the API, verify environment variables and service hostnames before deployment.

---

## 24. Output Commit Strategy

The `outputs/` directory is intentionally useful for reviewers.

It contains generated Scenario A and Scenario B artifacts so reviewers can inspect structural correctness immediately after cloning.

Important output files:

```text
outputs/scenario_a/questions_scenario_a.json
outputs/scenario_a/kb_snapshot_scenario_a.json

outputs/scenario_b_iter1/questions_iter1.json
outputs/scenario_b_iter1/kb_snapshot_iter1.json

outputs/scenario_b_iter2/questions_iter2.json
outputs/scenario_b_iter2/kb_snapshot_iter2.json

outputs/scenario_b_iter3/questions_iter3.json
outputs/scenario_b_iter3/kb_snapshot_iter3.json
```

Reviewers can regenerate these files using:

```powershell
python -m cli.run_evaluation --questions-per-section 5
```

---

## 25. Suggested Recruiter Verification Flow

A reviewer can verify the project as follows.

### 25.1 Start services

```powershell
docker compose up -d
```

### 25.2 Reset and rebuild the KB

```powershell
python -m cli.reset_db reset
python -m cli.ingest_pdf
python -m cli.index_qdrant
```

### 25.3 Run full evaluation

```powershell
python -m cli.run_evaluation --questions-per-section 5
```

### 25.4 Verify final Scenario B result

Expected:

```text
Scenario B iteration 1 complete | mode=cold_start | score=50.0
Scenario B iteration 2 complete | mode=adaptive | score=66.67
Scenario B iteration 3 complete | mode=adaptive | score=0.0
```

### 25.5 Run tests

```powershell
python -m pytest tests
```

Expected:

```text
6 passed
```

### 25.6 Run API

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 18000
```

Open:

```text
http://127.0.0.1:18000/docs
```

Test:

```text
GET /health
GET /documents/latest/sections
POST /prep/start
POST /prep/submit
GET /sessions/{session_id}
GET /kb/snapshot
```

---

## 26. Project Structure

Short structure summary:

```text
app/
  api/          FastAPI route modules
  core/         settings, logging, exceptions
  db/           SQLAlchemy models, session, repositories
  ingestion/    PDF loading, section parsing, chunking
  retrieval/    embeddings, Qdrant indexing, retrieval
  llm/          providers, prompts, generation, validation
  workflow/     LangGraph state, nodes, graph
  services/     business logic services
  schemas/      Pydantic request/response schemas

cli/
  reset_db.py
  ingest_pdf.py
  index_qdrant.py
  run_scenario_a.py
  run_scenario_b.py
  run_evaluation.py

docs/
  architecture.md
  database_schema.md
  adaptation_strategy.md

outputs/
  scenario_a/
  scenario_b_iter1/
  scenario_b_iter2/
  scenario_b_iter3/

tests/
  test_mcq_validation.py
  test_prep_api.py
  test_prep_flow.py
```

A more detailed project structure can be added in:

```text
docs/project_structure.md
```

---

## 27. Useful Commands

Start services:

```powershell
docker compose up -d
```

Reset database:

```powershell
python -m cli.reset_db reset
```

Ingest PDF:

```powershell
python -m cli.ingest_pdf
```

Index Qdrant:

```powershell
python -m cli.index_qdrant
```

Run Scenario A:

```powershell
python -m cli.run_scenario_a --questions-per-section 5
```

Run Scenario B:

```powershell
python -m cli.run_scenario_b --questions-per-section 5
```

Run full evaluation:

```powershell
python -m cli.run_evaluation --questions-per-section 5
```

Run tests:

```powershell
python -m pytest tests
```

Run API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 18000
```

Open Swagger:

```text
http://127.0.0.1:18000/docs
```

---

## 28. Development Note

This project was independently implemented and validated by the project author. AI tools were used as supplementary assistants for brainstorming, debugging support, documentation refinement, and reviewing implementation decisions.

All final architecture choices, code changes, testing, validation, and repository maintenance were reviewed and owned by the project author.

**AI Tools:** ChatGPT, Google Gemini

---

## 29. Final Project Pitch

This project is a production-style adaptive RAG backend that ingests a structured PDF, stores section chunks in Qdrant for deterministic section-filtered retrieval, stores all learning history in PostgreSQL, generates MCQs through an LLM, validates structured outputs, scores answers, identifies weak topics over time, and adapts future question generation based on previous mistakes while exporting reviewer-ready Scenario A and Scenario B outputs.