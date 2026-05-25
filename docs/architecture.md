# Architecture

---

# 1. Overview

The **Adaptive Document Preparation System** is a production-grade, history-aware adaptive RAG platform built for PDF-based study preparation, intelligent MCQ generation, and interactive evaluation workflows.

This system was designed around a very specific engineering goal:

> proving adaptive preparation behavior across repeated learning sessions — not just building another basic RAG demo.

The platform ingests structured multi-section PDFs, stores raw source files inside isolated object storage, indexes semantic chunk embeddings inside Qdrant, tracks learning history in PostgreSQL, generates validated MCQs using LLMs, evaluates user performance, and dynamically adapts future question generation based on previous mistakes.

The architecture combines:

- FastAPI backend services
- Streamlit presentation layer
- Celery asynchronous execution
- Redis broker orchestration
- PostgreSQL relational tracking
- Qdrant semantic retrieval
- MinIO object storage
- LangGraph workflow orchestration

The system distinguishes runtime behavior using isolated adaptive states:

```text
first relevant run     -> cold_start
returning relevant run -> adaptive
```

---

# Index

1. Overview  
2. Core Architecture Principle  
3. High-Level System Flow  
4. Main Runtime Components  
5. PDF Section Mapping  
6. Deterministic Section-Filtered Retrieval  
7. Embedding Layer  
8. LLM Provider Layer  
9. Prompting Strategy  
10. MCQ Generation  
11. MCQ Validation Layer  
12. Text Normalization  
13. LangGraph Workflow Orchestration  
14. Adaptive Intelligence Layer  
15. Backend-Owned Adaptation Logic  
16. Weak Topic Tracking  
17. Interactive API & Frontend Flow  
18. CLI Evaluation Flow  
19. Scenario A  
20. Scenario B  
21. KB Snapshots  
22. Exported Reviewer Outputs  
23. Testing  
24. API Contract Tests  
25. Recruiter Verification Flow  
26. API Swagger Verification  
27. Architecture Decisions  
28. Current Working Commands  
29. Known Limitations  
30. Summary  

---

# 2. Core Architecture Principle

The platform uses a deliberately separated multi-tier storage model:

```text
MinIO Storage  = Immutable raw PDF source vault
PostgreSQL     = Relational learning history + session tracking
Qdrant         = Semantic retrieval engine only
```

Each layer has a clearly isolated responsibility.

### PostgreSQL handles:
- Session history
- Generated questions
- User answers
- Weak-topic statistics
- Scoring metadata
- KB snapshots
- Adaptive tracking state

### MinIO handles:
- Raw PDF storage
- Immutable binary persistence
- Cross-environment source consistency

### Qdrant handles:
- Semantic vector similarity
- Chunk retrieval
- Section-filtered context search

This separation keeps the platform:
- auditable
- deterministic
- scalable
- reviewer-friendly

---

# 3. High-Level System Flow

```text
[ User Interaction via Streamlit Web UI ]
                                          │
                                          ▼
                             [ FastAPI REST API Gateway ]
                             (Instantly Returns 202 Task)
                                          │
                 ┌────────────────────────┴────────────────────────┐
                 ▼ (Async Broker Push)                             ▼ (Storage Audit)
      [ Redis Message Broker ]                        [ MinIO S3 Object Repository ]
            (Port 6380)                                  (Raw PDF Document Vault)
                 │                                                 │
                 ▼ (Worker Thread Pick)                            ▼ (Source Fetch)
      [ Celery Asynchronous Workers ] ─────────────────────────────┘
       - Fixed-Window Multi-Section Batching
       - Offline Transformers Local Cache
                 │
                 ▼
      [ LangGraph Stateful Workflows ]
       (Retrieval + Adaptation Payloads)
                 │
                 ▼
        [ Qdrant Vector Engine ]
       (Strict Section Partition Filter)
                 │
                 ▼
      [ Upstream LLM Inference Tier ]
        (Groq Llama-3 / Mock Fallback)
                 │
                 ▼
      [ Pydantic Validation & ftfy Cleanup ]
                 │
                 ▼
      [ PostgreSQL Persistence Core ]
       (Bulk db.add_all Relational Flushes)
                 │
                 ▼
      [ Streamlit Performance Rendering ]
       (Human-Readable Snapshots & Explanations)
```

---

# 4. Main Runtime Components

---

## 4.1 FastAPI Backend Gateway

The FastAPI layer acts as the main orchestration gateway.

Responsibilities include:
- validating payloads
- dispatching background tasks
- exposing APIs
- returning async tracking states
- coordinating session persistence

Runs on:

```text
Port 8090
```

### Main Endpoints

```text
GET  /health
GET  /documents/latest/sections
POST /prep/start
POST /prep/submit
GET  /sessions/{session_id}
GET  /kb/snapshot
```

---

## 4.2 MinIO Object Storage Repository

MinIO acts as the immutable raw PDF storage layer.

Instead of depending on local file paths, source PDFs are stored inside object buckets:

```text
raw-dossiers
```

Benefits:
- environment isolation
- safer ingestion workflows
- cleaner deployment portability
- reviewer reproducibility

---

## 4.3 PostgreSQL Knowledge Base

The relational backbone of the platform.

Runs on:

```text
Port 5433
```

Stores:
- prep sessions
- generated questions
- user answers
- weak-topic statistics
- adaptation metadata
- snapshots

Performance-oriented indexes were added for adaptive lookups:

```text
idx_weak_topic_perf_sorting
idx_gen_questions_doc_section
```

---

## 4.4 Qdrant Vector Store

Qdrant powers semantic retrieval.

Runs on:

```text
Port 16433
```

Stores:
- chunk embeddings
- metadata payloads
- section identifiers
- topic labels

Payload metadata allows deterministic filtering:

```text
section_number
topic
chunk_id
```

---

## 4.5 Celery Asynchronous Worker Pool

Heavy workflows are fully decoupled from the HTTP request cycle.

Powered by:
- Celery
- Redis broker
- background worker threads

Runs on:

```text
Redis Port 6380
```

This prevents:
- request blocking
- HTTP timeouts
- synchronous LLM bottlenecks

---

## 4.6 Streamlit Presentation Interface

The Streamlit layer provides the interactive user-facing experience.

Runs on:

```text
Port 8501
```

Responsibilities:
- section selection
- session launching
- answer submission
- question rendering
- score visualization

The interface isolates answer state using:

```python
st.session_state
```

This avoids:
- malformed submissions
- stale answer collisions
- HTTP 422 payload failures

---

## 4.7 PDF Ingestion Pipeline

```text
data/SLATEFALL_DOSSIER.pdf
                │
                ▼
        MinIO Raw Storage
                │
                ▼
      PyMuPDF Text Extraction
                │
                ▼
 PostgreSQL + Qdrant Parallel Sync
```

The ingestion pipeline:
- extracts section boundaries
- chunks content
- persists metadata
- generates embeddings
- indexes vectors

---

# 5. PDF Section Mapping

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

# 6. Deterministic Section-Filtered Retrieval

Retrieval is intentionally strict.

If a user selects:

```text
[5, 8]
```

the backend pushes explicit metadata filters directly into Qdrant.

This guarantees:
- zero cross-section contamination
- bounded semantic retrieval
- deterministic evaluation integrity

The vector engine never searches globally outside selected sections.

---

# 7. Embedding Layer

The platform uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Features:
- lightweight inference
- local execution
- deterministic embedding generation
- efficient vector dimensions

The embedding layer runs fully offline after model caching.

---

# 8. LLM Provider Layer

Supported providers:

```text
groq
gemini
mock
```

Primary production provider:

```text
Groq llama3-8b-8192
```

Temperature:

```text
0.2
```

The low-temperature setup improves:
- JSON consistency
- schema stability
- validation reliability

---

# 9. Prompting Strategy

Prompt payloads are intentionally compact.

Instead of dumping raw historical logs, the system injects:
- weak-topic summaries
- failure statistics
- selected context chunks
- adaptation metadata

This keeps:
- token usage lower
- prompts cleaner
- generation faster
- retrieval more focused

---

# 10. MCQ Generation

Questions are generated section-by-section.

The backend owns:
- question IDs
- metadata
- persistence state

The LLM only generates:
- question text
- options
- explanations
- correct answers

This separation avoids:
- ID collisions
- malformed schemas
- duplicated records

---

# 11. MCQ Validation Layer

Every generated object is validated before persistence.

Validation rules include:

- Exactly 4 options
- Strict A/B/C/D structure
- Correct-answer validation
- Retry-on-invalid-generation logic

The validation layer is one of the most important stability safeguards in the platform.

---

# 12. Text Normalization

PDF extraction frequently introduces mojibake corruption:

```text
Cuartel ValparaÃ­so
```

The system routes all extracted text through:

```text
ftfy
```

Result:

```text
Cuartel Valparaíso
```

This significantly improves:
- embedding quality
- retrieval accuracy
- UI readability

---

# 13. LangGraph Workflow Orchestration

The adaptive evaluation engine is orchestrated using LangGraph.

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

This workflow becomes especially important during Scenario B runs where previous session history directly influences future generation behavior.

---

# 14. Adaptive Intelligence Layer

The platform continuously analyzes historical performance.

### No history:
```text
cold_start
```

### Existing weakness history:
```text
adaptive
```

Adaptive runs inject:
- weak topics
- historical failures
- section difficulty trends

directly into prompt orchestration.

---

# 15. Backend-Owned Adaptation Logic

Adaptation metadata is generated by backend logic — not by the LLM.

This improves:
- auditability
- reproducibility
- reviewer trust

### Example

```text
Cold-start coverage question generated because no prior history exists.
```

```text
Adaptive question generated because section 8 previously showed weakness patterns.
```

---

# 16. Weak Topic Tracking

Weakness updates occur immediately after scoring.

Core repository operation:

```python
_update_weak_topic_stat(
    db=db,
    topic=question.topic,
    is_correct=is_correct
)
```

The database continuously updates:
- wrong counts
- weakness scores
- topic frequency

This drives future adaptive behavior.

---

# 17. Interactive API & Frontend Flow

### Session Start

```text
POST /prep/start
```

The frontend sends:
- selected sections
- question counts

The backend:
- launches Celery tasks
- retrieves context
- generates MCQs
- hides correct answers

---

### Interactive Evaluation

Users answer through Streamlit forms.

Only:
```text
A / B / C / D
```

tokens are submitted.

---

### Batch Submission

```text
POST /prep/submit
```

The backend:
- bulk persists answers
- scores responses
- updates weak topics
- returns explanations

---

# 18. CLI Evaluation Flow

The project includes reproducible CLI evaluation flows.

```powershell
python -m cli.run_scenario_a --questions-per-section 5

python -m cli.run_scenario_b --questions-per-section 5

python -m cli.run_evaluation --questions-per-section 5
```

---

# 19. Scenario A

Scenario A validates:
- cold-start generation
- standard retrieval
- baseline scoring behavior

Outputs are exported under:

```text
outputs/scenario_a/
```

---

# 20. Scenario B

Scenario B validates adaptive behavior across repeated runs.

### Iteration 1
```text
Sections: [5, 8]
Mode: cold_start
```

### Iteration 2
```text
Sections: [6, 8, 9]
Mode: adaptive
```

### Iteration 3
```text
Sections: [8]
Mode: adaptive
```

The platform progressively targets previously weak sections.

---

# 21. KB Snapshots

Snapshot exports compile:
- scores
- weakness statistics
- session metadata
- adaptive states

These exports make reviewer validation easier.

---

# 22. Exported Reviewer Outputs

Generated artifacts are automatically exported under:

```text
outputs/
```

This allows reviewers to inspect:
- generated questions
- adaptive history
- session states
- KB snapshots

without rebuilding the full stack immediately.

---

# 23. Testing

Automated validation suite:

```powershell
python -m pytest tests
```

Current status:

```text
6 passed
```

---

# 24. API Contract Tests

API validation ensures:
- hidden answer keys before submission
- strict schema enforcement
- correct response contracts
- deterministic payload structures

---

# 25. Recruiter Verification Flow

```powershell
# Start Services
docker compose up -d

# Reset State
python -m cli.reset_db reset

# Rebuild Knowledge Base
python -m cli.ingest_pdf
python -m cli.index_qdrant

# Run Evaluation
python -m cli.run_evaluation --questions-per-section 5

# Launch Worker
python -m celery -A app.core.celery_app.celery_app worker --loglevel=info -P threads

# Launch API
python -m uvicorn app.main:app --host 127.0.0.1 --port 8090

# Launch Frontend
streamlit run app_ui.py
```

---

# 26. API Swagger Verification

Swagger UI:

```text
http://127.0.0.1:8090/docs
```

---

# 27. Architecture Decisions

### No Authentication Layer
Authentication was intentionally excluded to prioritize:
- adaptive logic
- retrieval engineering
- orchestration workflows

---

### Decoupled Presentation Tier

Streamlit remains isolated from:
- database logic
- retrieval orchestration
- scoring logic

---

### Bulk Persistence Strategy

Answer submissions use:
```python
db.add_all()
```

This reduces:
- database write overhead
- transaction fragmentation
- excessive commit operations

---

# 28. Current Working Commands

```powershell
# Start Services
docker compose up -d

# Reset Database
python -m cli.reset_db reset

# Ingestion
python -m cli.ingest_pdf

# Vector Indexing
python -m cli.index_qdrant

# Worker
python -m celery -A app.core.celery_app.celery_app worker --loglevel=info -P threads

# API
python -m uvicorn app.main:app --host 127.0.0.1 --port 8090

# Frontend
streamlit run app_ui.py
```

---

# 29. Known Limitations

## LLM Non-Determinism

Inference behavior may vary slightly across runs.

Mitigation:
- low temperature
- strict validation
- retry handling
- fallback mock generation

---

## Cache State Resets

To fully restore cold-start behavior:

```powershell
python -m cli.reset_db reset
```

must be executed before rerunning evaluations.

---

# 30. Summary

The Adaptive Document Preparation System combines:

- MinIO object isolation
- PostgreSQL historical tracking
- Qdrant semantic retrieval
- Celery asynchronous execution
- LangGraph orchestration
- Streamlit visualization
- FastAPI backend APIs

to create a fully testable, reviewer-friendly adaptive RAG platform.

The architecture focuses heavily on:
- deterministic adaptive behavior
- strict retrieval boundaries
- persistence guarantees
- reproducible evaluation workflows
- production-style orchestration patterns

rather than simple one-shot LLM question generation.