````markdown
# Architecture

## Overview

The Adaptive Document Preparation System is a backend-driven adaptive RAG application.

It ingests a structured multi-section PDF, stores structured document data and learning history in PostgreSQL, stores semantic chunk embeddings in Qdrant, retrieves only chunks from selected sections, generates MCQs with an LLM, validates generated MCQs, collects or simulates answers, scores sessions, updates weak-topic history, and adapts future question generation based on previous mistakes.

The system is designed for an AI/ML internship take-home assessment where the most important requirement is adaptive intelligence.

---

## Core Architecture Principle

The project uses a hybrid storage architecture.

```text
PostgreSQL = source of truth
Qdrant     = semantic retrieval only
```

PostgreSQL stores all structured data, user history, questions, answers, scores, weak-topic statistics, and KB snapshots.

Qdrant stores vector embeddings for PDF chunks and supports semantic retrieval with strict metadata filtering.

Qdrant is not used as the main Knowledge Base.

---

## High-Level Flow

```text
PDF
  ↓
PDF loader
  ↓
Section parser
  ↓
Chunker
  ↓
PostgreSQL stores documents, sections, and chunks
  ↓
Embedding model creates chunk vectors
  ↓
Qdrant stores vectors with strict metadata
  ↓
User selects one or more sections
  ↓
Retriever fetches only selected-section chunks
  ↓
PostgreSQL history is checked
  ↓
Adaptation payload is built
  ↓
LLM generates MCQs
  ↓
Pydantic validates MCQ output
  ↓
Questions are presented through API or CLI
  ↓
Answers are collected or simulated
  ↓
Scoring is performed
  ↓
Session, questions, answers, score, and weak-topic updates are saved
  ↓
KB snapshot and reviewer JSON outputs are exported
```

---

## Main Components

## 1. FastAPI Backend

FastAPI exposes the REST API for document sections, preparation sessions, answer submission, session history, KB snapshot access, and health checking.

Current important endpoints:

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

Main files:

```text
app/main.py
app/api/routes_health.py
app/api/routes_documents.py
app/api/routes_prep.py
app/api/routes_sessions.py
app/api/routes_kb.py
```

---

## 2. PostgreSQL Knowledge Base

PostgreSQL is the relational source of truth.

It stores:

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

PostgreSQL is responsible for:

- document metadata
- PDF section metadata
- chunk text and previews
- generated questions
- user answers
- correct/wrong results
- session scores
- weak-topic tracking
- adaptation metadata
- human-readable KB snapshots

Main files:

```text
app/db/models.py
app/db/session.py
app/db/repositories/document_repo.py
app/db/repositories/session_repo.py
app/db/repositories/question_repo.py
app/db/repositories/snapshot_repo.py
```

---

## 3. Qdrant Vector Store

Qdrant stores semantic embeddings for PDF chunks.

Each vector point includes strict metadata:

```text
document_id
section_id
section_number
chunk_id
chunk_index
page_number
text_preview
```

Qdrant is used only to retrieve relevant chunks.

It does not store learning history, scores, answers, or user sessions.

Main files:

```text
app/retrieval/embeddings.py
app/retrieval/qdrant_store.py
app/retrieval/retriever.py
```

---

## 4. PDF Ingestion Pipeline

The PDF ingestion pipeline converts the main multi-section PDF corpus into structured sections and chunks.

Flow:

```text
SLATEFALL_DOSSIER.pdf
  ↓
load pages with PyMuPDF
  ↓
detect sections
  ↓
split sections into chunks
  ↓
save document, sections, and chunks in PostgreSQL
  ↓
index chunk embeddings into Qdrant
```

Main files:

```text
app/ingestion/pdf_loader.py
app/ingestion/section_parser.py
app/ingestion/chunker.py
cli/ingest_pdf.py
cli/index_qdrant.py
```

---

## 5. Section Mapping

The PDF parser currently detects 10 sections.

| Section | Title | Pages |
|---|---|---|
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

Scenario B uses the assessment-required repeated section 8:

```text
Iteration 1: sections 5 and 8
Iteration 2: sections 6, 8, and 9
Iteration 3: section 8
```

---

## 6. Deterministic Section-Filtered Retrieval

The retriever must only retrieve chunks from selected sections.

Example:

```text
Selected sections: [5, 8]
```

The retriever applies strict metadata filters so only section 5 and section 8 chunks can be returned.

This prevents:

- out-of-section question generation
- unnecessary hallucination
- random retrieval from the full PDF corpus
- reviewer confusion about where questions came from

Main file:

```text
app/retrieval/retriever.py
```

---

## 7. Embedding Layer

The embedding model converts chunk text into vectors for Qdrant.

Current embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

This is lightweight and suitable for local development.

The project can later switch to:

```text
BAAI/bge-small-en-v1.5
```

if stronger retrieval quality is needed.

Main file:

```text
app/retrieval/embeddings.py
```

---

## 8. LLM Provider Layer

The LLM layer supports real and mock providers.

Current providers:

```text
groq
mock
```

Groq is used for real MCQ generation.

Mock is used for deterministic local development and testing.

The provider is controlled through:

```env
LLM_PROVIDER=groq
```

or:

```env
LLM_PROVIDER=mock
```

Main files:

```text
app/llm/providers.py
app/llm/prompts.py
app/llm/mcq_generator.py
```

---

## 9. Prompting Strategy

Before question generation, the system builds a compact prompt containing:

- selected section numbers
- retrieved chunks
- questions per section
- adaptive context
- weak topics
- previous wrong questions
- mastered questions to avoid

The system does not send a huge raw history dump to the LLM.

Instead, it sends a compact adaptation payload.

This keeps prompts smaller, more controlled, and more reviewer-friendly.

Main file:

```text
app/llm/prompts.py
```

---

## 10. MCQ Generation

The MCQ generator receives:

```text
retrieved_chunks
selected_section_numbers
questions_per_section
adaptation_payload
```

It generates structured MCQs.

Each MCQ includes:

```text
question_id
section_id
section_number
topic
difficulty
question
options
correct_answer
explanation
adaptation_reason
source_chunk_ids
```

Important design decision:

```text
The backend generates question_id values.
The LLM is not trusted to generate database primary keys.
```

This prevents duplicate primary key errors caused by repeated LLM-generated IDs.

Main file:

```text
app/llm/mcq_generator.py
```

---

## 11. MCQ Validation Layer

Generated MCQs are normalized and validated before they are saved or returned.

Validation checks:

```text
exactly 4 options
options must be A, B, C, D
correct answer must be A, B, C, or D
question must belong to selected sections only
topic must be non-empty
explanation must be non-empty
adaptation_reason must be non-empty
question count per selected section must match the request
duplicate question text is handled
extra LLM questions are truncated safely
missing questions cause a controlled validation error
```

Main files:

```text
app/llm/output_parser.py
app/schemas/question.py
```

---

## 12. Text Normalization

LLM output can occasionally contain broken Unicode or mojibake.

Example:

```text
Broken:  Cuartel ValparaÃ­so
Correct: Cuartel Valparaíso
```

The project uses the `ftfy` library to normalize user-facing text.

This avoids hardcoded character replacement maps.

Text normalization is applied to:

```text
question text
option text
topic
explanation
adaptation_reason
API response text
```

Main files:

```text
app/llm/output_parser.py
app/services/interactive_prep_service.py
```

---

## 13. LangGraph Workflow

The CLI preparation flow is orchestrated with LangGraph.

Workflow steps:

```text
1. Load latest document and history
2. Build adaptation payload
3. Retrieve selected-section chunks
4. Generate MCQs
5. Simulate answers
6. Score answers
7. Persist session, questions, answers, and weak-topic updates
```

Graph state includes:

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

Main files:

```text
app/workflow/state.py
app/workflow/nodes.py
app/workflow/prep_graph.py
```

---

## 14. Adaptive Intelligence Layer

The adaptive layer checks previous sessions before generating new questions.

It builds an adaptation payload with:

```text
mode
is_returning_run
relevant_prior_session_count
weak_topics
mastered_question_texts
previous_wrong_question_texts
summary
```

Mode rules:

```text
No relevant previous session -> cold_start
Relevant history found       -> adaptive
```

The adaptive layer uses historical wrong answers to identify weak topics.

Future questions focus more on weak topics and avoid excessive repetition of mastered questions.

Main file:

```text
app/services/adaptation_service.py
```

---

## 15. Weak Topic Tracking

Weak topics are updated from wrong answers.

The weak-topic table tracks:

```text
document_id
section_number
topic
attempts
wrong_count
correct_count
weakness_score
```

The weakness score is computed from previous performance.

This allows the system to know which topics need more practice in returning runs.

Main file:

```text
app/db/repositories/session_repo.py
```

---

## 16. Interactive API Flow

The interactive API flow supports real user answers.

### Start preparation

Endpoint:

```text
POST /prep/start
```

Input:

```json
{
  "selected_section_numbers": [5, 8],
  "questions_per_section": 1
}
```

Output:

```text
session_id
document_id
mode
selected_sections
total_questions
adaptation_summary
questions
```

Important:

```text
/prep/start does not expose correct_answer.
```

### Submit answers

Endpoint:

```text
POST /prep/submit
```

Input:

```json
{
  "session_id": "session-id",
  "answers": {
    "question-id-1": "A",
    "question-id-2": "B"
  }
}
```

Output:

```text
score
total_questions
correct_count
wrong_count
results
correct_answer
clarification for wrong answers
```

Main files:

```text
app/api/routes_prep.py
app/services/interactive_prep_service.py
app/db/repositories/session_repo.py
app/schemas/prep.py
```

---

## 17. CLI Evaluation Flow

The CLI flow supports reviewer evaluation scenarios.

Available commands:

```powershell
python -m cli.run_scenario_a --questions-per-section 2
python -m cli.run_scenario_b --questions-per-section 2
python -m cli.run_evaluation --questions-per-section 2
```

Scenario A demonstrates cold-start behavior.

Scenario B demonstrates adaptive behavior across repeated section 8 usage.

Main files:

```text
cli/run_scenario_a.py
cli/run_scenario_b.py
cli/run_evaluation.py
```

---

## 18. Scenario A

Scenario A runs a cold-start prep over two sections.

Expected output:

```text
Scenario A complete | session=... | mode=cold_start | score=50.0
```

Output files:

```text
outputs/scenario_a/questions_scenario_a.json
outputs/scenario_a/kb_snapshot_scenario_a.json
```

---

## 19. Scenario B

Scenario B is the main adaptive evaluation scenario.

It runs:

```text
Iteration 1: sections 5 and 8
Iteration 2: sections 6, 8, and 9
Iteration 3: section 8
```

Expected output:

```text
Scenario B iteration 1 complete | ... | mode=cold_start | score=50.0
Scenario B iteration 2 complete | ... | mode=adaptive | score=66.67
Scenario B iteration 3 complete | ... | mode=adaptive | score=0.0
```

Why the scores happen:

```text
Iteration 1:
sections = [5, 8]
2 questions per section
total = 4
section 8 is simulated weak
2 correct, 2 wrong
score = 50.0

Iteration 2:
sections = [6, 8, 9]
2 questions per section
total = 6
section 8 is simulated weak
4 correct, 2 wrong
score = 66.67

Iteration 3:
sections = [8]
2 questions total
section 8 is simulated weak
0 correct, 2 wrong
score = 0.0
```

Required output files:

```text
outputs/scenario_b_iter1/questions_iter1.json
outputs/scenario_b_iter1/kb_snapshot_iter1.json

outputs/scenario_b_iter2/questions_iter2.json
outputs/scenario_b_iter2/kb_snapshot_iter2.json

outputs/scenario_b_iter3/questions_iter3.json
outputs/scenario_b_iter3/kb_snapshot_iter3.json
```

---

## 20. KB Snapshots

KB snapshots are exported after each evaluation run.

They include enough information for reviewers to verify:

```text
session_id
selected sections
questions asked
user answers
correct answers
wrong answers
score
weak topics
adaptation summary
timestamp
recent session history
```

Main file:

```text
app/services/snapshot_service.py
```

---

## 21. Exported Reviewer Outputs

Questions and KB snapshots are exported into the `outputs/` directory.

Scenario B expected structure:

```text
outputs/
  scenario_b_iter1/
    questions_iter1.json
    kb_snapshot_iter1.json

  scenario_b_iter2/
    questions_iter2.json
    kb_snapshot_iter2.json

  scenario_b_iter3/
    questions_iter3.json
    kb_snapshot_iter3.json
```

These files are important because they provide reviewer-visible evidence of:

```text
generated questions
adaptation reasons
answers
scores
weak-topic tracking
session history
```

---

## 22. Testing

Current tests cover:

```text
MCQ validation
out-of-selected-section rejection
question distribution validation
scoring logic
/prep/start API contract
/prep/submit API contract
```

Run tests:

```powershell
python -m pytest tests
```

Current expected result:

```text
6 passed
```

Test files:

```text
tests/test_mcq_validation.py
tests/test_prep_flow.py
tests/test_prep_api.py
```

---

## 23. API Contract Tests

The API contract tests verify:

```text
/prep/start returns questions and options
/prep/start does not expose correct_answer
/prep/start does not expose explanation
/prep/submit returns score
/prep/submit returns correct_answer
/prep/submit returns clarification for wrong answers
```

This allows recruiters to verify API behavior without relying only on Swagger manual testing.

---

## 24. Recruiter Verification Flow

A recruiter should be able to verify the project with this flow:

### 1. Start services

```powershell
docker compose up -d
```

### 2. Reset database

```powershell
python -m cli.reset_db reset
```

### 3. Ingest PDF

```powershell
python -m cli.ingest_pdf
```

### 4. Index Qdrant

```powershell
python -m cli.index_qdrant
```

### 5. Run evaluation

```powershell
python -m cli.run_evaluation --questions-per-section 2
```

### 6. Check Scenario B outputs

```powershell
Get-ChildItem outputs\scenario_b_iter1
Get-ChildItem outputs\scenario_b_iter2
Get-ChildItem outputs\scenario_b_iter3
```

### 7. Check adaptive evidence

```powershell
Get-Content outputs\scenario_b_iter2\questions_iter2.json | Select-String "adaptation_reason"
Get-Content outputs\scenario_b_iter3\questions_iter3.json | Select-String "adaptation_reason"
```

### 8. Run tests

```powershell
python -m pytest tests
```

### 9. Run API

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 18000
```

Open Swagger:

```text
http://127.0.0.1:18000/docs
```

---

## 25. API Swagger Verification

In Swagger, test:

```text
POST /prep/start
```

Example request:

```json
{
  "selected_section_numbers": [5, 8],
  "questions_per_section": 1
}
```

Expected:

```text
questions are returned
options are returned
correct_answer is hidden
adaptation_reason is visible
```

Then test:

```text
POST /prep/submit
```

Expected:

```text
score is returned
correct_answer is returned after submission
clarification is returned for wrong answers
```

---

## 26. Known Architecture Decisions

### No Authentication

Authentication and authorization are intentionally excluded.

The assessment focuses on:

```text
PDF ingestion
section extraction
retrieval
MCQ generation
scoring
history persistence
adaptive behavior
reviewer outputs
```

### Backend First

The project prioritizes:

```text
FastAPI
CLI
PostgreSQL
Qdrant
LangGraph
JSON outputs
tests
```

A UI is optional and should only be added after the backend is complete.

### Qdrant Is Not the Knowledge Base

Qdrant stores embeddings only.

PostgreSQL stores truth, history, answers, scores, and adaptation data.

### LLM Output Is Not Trusted Blindly

The system validates and normalizes LLM output before persistence.

Backend-generated UUIDs are used for question IDs.

---

## 27. Current Working Commands

```powershell
docker compose up -d
```

```powershell
python -m cli.reset_db reset
```

```powershell
python -m cli.ingest_pdf
```

```powershell
python -m cli.index_qdrant
```

```powershell
python -m cli.run_scenario_a --questions-per-section 2
```

```powershell
python -m cli.run_scenario_b --questions-per-section 2
```

```powershell
python -m cli.run_evaluation --questions-per-section 2
```

```powershell
python -m pytest tests
```

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 18000
```

---

## 28. Current Verified Status

The following are currently verified:

```text
Docker services run
PostgreSQL works
Qdrant works
PDF ingestion works
Qdrant indexing works
Strict selected-section retrieval works
Groq generation works
Mock fallback works
MCQ validation works
LangGraph workflow works
Scenario A works
Scenario B works
Scenario B adaptive behavior works
/prep/start works
/prep/submit works
Swagger verification works
Pytest suite passes
Clean-code audit removed obsolete CLI helpers
Groq API key is not hardcoded
Local absolute paths are not hardcoded in app/cli/tests
```

---

## 29. Remaining Work

Remaining implementation and polish tasks:

```text
Add docs/database_schema.md
Add docs/adaptation_strategy.md
Finalize Dockerfile
Finalize README.md
Add structured logging
Review output JSON commit strategy
Add more integration tests if time allows
Run final clean-code audit
Run final recruiter verification from a fresh reset
Push final GitHub checkpoint
```

---

## 30. Future Optional Work

Optional features after the assessment core is complete:

```text
Streamlit UI
manual answer UI
session dashboard
weak-topic visualization
question review screen
section selector UI
export report as PDF
support more PDFs
support multiple users
support local Ollama fallback
```

These should not be prioritized before the backend assessment requirements are fully polished.

---

## Summary

The architecture is backend-first and assessment-focused.

The system already demonstrates the key requirement:

```text
cold_start first run
adaptive returning runs
history-aware question generation
weak-topic focus
section-filtered retrieval
PostgreSQL-backed Knowledge Base
Qdrant-backed semantic retrieval
reviewer-ready Scenario B outputs
```

The project is progressing toward a clean production-style AI backend rather than a UI-first demo.
````
