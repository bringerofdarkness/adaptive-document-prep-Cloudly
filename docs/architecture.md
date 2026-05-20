# Architecture

## 1. Overview

The **Adaptive Document Preparation System** is a backend-first adaptive RAG application for PDF-based study preparation and MCQ generation.

The system ingests a structured multi-section PDF, stores document data and learning history in PostgreSQL, stores semantic chunk embeddings in Qdrant, retrieves only the user-selected sections, generates MCQs with an LLM, validates generated output, scores answers, updates weak-topic history, and adapts future question generation based on previous mistakes.

The most important architectural goal is not simple retrieval. The main goal is to prove **history-aware adaptive preparation**.

The system distinguishes:

```text
first relevant run     -> cold_start
returning relevant run -> adaptive
```

---

## 2. Core Architecture Principle

The project uses a hybrid storage architecture:

```text
PostgreSQL = source of truth and learning history
Qdrant     = semantic retrieval only
```

PostgreSQL stores all structured data, session history, questions, answers, scores, weak-topic statistics, and KB snapshots.

Qdrant stores only vector embeddings and retrieval metadata for PDF chunks.

Qdrant is not used as the main Knowledge Base. This keeps the system auditable and allows reviewers to verify how adaptive decisions are grounded in real stored session history.

---

## 3. High-Level System Flow

```text
Structured PDF
  ↓
PDF Loader
  ↓
Section Parser
  ↓
Chunker
  ↓
PostgreSQL stores documents, sections, and chunks
  ↓
Embedding model creates chunk vectors
  ↓
Qdrant stores vectors with section metadata
  ↓
User selects one or more sections
  ↓
System checks PostgreSQL for prior prep history
  ↓
Adaptation payload is built
  ↓
Retriever fetches only selected-section chunks from Qdrant
  ↓
LLM generates MCQs section by section
  ↓
MCQ output is normalized and validated
  ↓
Questions are presented through CLI or API
  ↓
Answers are simulated or submitted by user
  ↓
Scoring service marks correct and wrong answers
  ↓
Session, questions, answers, scores, and weak-topic updates are persisted
  ↓
Questions JSON and KB snapshot JSON are exported for reviewer verification
```

---

## 4. Main Runtime Components

### 4.1 FastAPI Backend

FastAPI exposes the REST API for health checks, document section listing, prep session creation, answer submission, session retrieval, and KB snapshots.

Important endpoints:

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

### 4.2 PostgreSQL Knowledge Base

PostgreSQL is the durable source of truth.

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

```text
document metadata
section metadata
chunk text
generated questions
submitted or simulated answers
correct/wrong results
session scores
weak-topic statistics
adaptation metadata
reviewer-readable KB snapshots
```

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

### 4.3 Qdrant Vector Store

Qdrant stores semantic embeddings for PDF chunks.

Each vector point includes retrieval metadata:

```text
document_id
section_id
section_number
chunk_id
chunk_index
page_number
text_preview
```

Qdrant is used only to retrieve relevant chunks. It does not store user answers, scores, sessions, weak topics, or adaptation history.

Main files:

```text
app/retrieval/embeddings.py
app/retrieval/qdrant_store.py
app/retrieval/retriever.py
```

---

### 4.4 PDF Ingestion Pipeline

The ingestion pipeline converts the main PDF corpus into structured sections and chunks.

Flow:

```text
data/SLATEFALL_DOSSIER.pdf
  ↓
load pages with PyMuPDF
  ↓
detect section boundaries
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

## 5. PDF Section Mapping

The current PDF parser detects 10 sections:

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

Scenario B uses the assessment-required repeated section 8:

```text
Iteration 1: sections [5, 8]
Iteration 2: sections [6, 8, 9]
Iteration 3: sections [8]
```

---

## 6. Deterministic Section-Filtered Retrieval

Retrieval is strictly section-filtered.

Example:

```text
Selected sections: [5, 8]
```

The retriever applies Qdrant metadata filters so only chunks from sections 5 and 8 can be returned.

This prevents:

```text
out-of-section question generation
random full-corpus retrieval
unrelated context leakage
reviewer confusion about source grounding
```

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

This model is lightweight and suitable for local development.

The console may show a HuggingFace warning about unauthenticated requests. This is not a failure. Setting `HF_TOKEN` can improve rate limits, but it is not required for normal local execution.

Main file:

```text
app/retrieval/embeddings.py
```

---

## 8. LLM Provider Layer

The LLM layer supports real and mock providers.

Current provider options:

```text
groq
gemini
mock
```

Groq is the primary real LLM provider for MCQ generation.

Mock generation is available for deterministic local testing and for environments where no external LLM key is available.

Provider selection is controlled through `.env`:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
```

or:

```env
LLM_PROVIDER=mock
```

If a Groq or Gemini key is missing, the provider layer raises a clear error and tells the user to set `LLM_PROVIDER=mock` to run without an external LLM key.

Main files:

```text
app/llm/providers.py
app/llm/prompts.py
app/llm/mcq_generator.py
```

---

## 9. Prompting Strategy

Before MCQ generation, the system builds a compact prompt containing:

```text
selected section number
retrieved chunks
questions per section
adaptation mode
weak topics
previous wrong questions
mastered questions to avoid
```

The system does not send the full raw session history to the LLM. Instead, it sends a compact adaptation payload.

This keeps prompts smaller, safer, and more reliable.

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

It generates structured MCQs section by section.

Each MCQ contains:

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

Important design decisions:

```text
The backend generates question_id values.
The LLM is not trusted to generate database primary keys.
The backend owns adaptation_reason based on real history.
The LLM generates question content, not adaptation metadata.
```

This prevents duplicate IDs and prevents the LLM from falsely claiming adaptive behavior during cold-start runs.

The generator also uses section-level retry logic. If the LLM under-generates or returns invalid structure, the system retries before failing.

Main file:

```text
app/llm/mcq_generator.py
```

---

## 11. MCQ Validation Layer

Generated MCQs are normalized and validated before they are saved or returned.

Validation checks include:

```text
exactly 4 options
options must be A, B, C, D
correct answer must be A, B, C, or D
question must belong only to selected sections
topic must be non-empty
explanation must be non-empty
adaptation_reason must be non-empty
question count per selected section must match the request
duplicate question text is handled
extra LLM questions are truncated safely
missing questions cause controlled validation failure
Pydantic schema validation
```

Validation files:

```text
app/llm/output_parser.py
app/schemas/question.py
```

---

## 12. Text Normalization

LLM and PDF text can sometimes contain broken Unicode or mojibake.

Example:

```text
Broken:  Cuartel ValparaÃ­so
Correct: Cuartel Valparaíso
```

The project uses `ftfy` to normalize user-facing text.

This is intentionally not a hardcoded word-specific replacement.

Text normalization applies to:

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

## LangGraph Workflow Orchestration

The CLI preparation flow is orchestrated with LangGraph.

LangGraph is used because the prep flow is not a single function call. It is a multi-step stateful workflow where each step depends on the previous step:

```text
load document and history
retrieve selected-section chunks
generate MCQs
simulate answers
score answers
persist session
export outputs
```

The graph makes the preparation flow easier to inspect, test, and extend.

### Workflow Nodes

The graph currently uses these nodes:

```text
load_document_and_history
retrieve_selected_section_chunks
generate_questions
simulate_and_score_answers
persist_session
```

### Workflow State

The LangGraph state carries the main runtime objects:

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

### Why LangGraph Is Used

LangGraph is useful here because the system needs to preserve and pass state across multiple backend steps:

```text
selected sections -> retrieved chunks -> MCQs -> answers -> score -> persisted session -> adaptive history
```

It also makes the adaptive workflow clearer:

```text
previous PostgreSQL history
  ↓
adaptation payload
  ↓
retrieval and generation
  ↓
scoring
  ↓
new history for future adaptive runs
```

This is especially important for Scenario B, where iteration 2 and iteration 3 depend on the history created by earlier iterations.

### Main Files

```text
app/workflow/state.py
app/workflow/nodes.py
app/workflow/prep_graph.py
app/services/prep_service.py
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

The adaptive layer uses historical wrong answers to identify weak topics. Future questions can then focus more on weak sections and avoid excessive repetition of mastered questions.

Main file:

```text
app/services/adaptation_service.py
```

---

## 15. Backend-Owned Adaptation Reason

The final `adaptation_reason` is controlled by the backend, not the LLM.

Examples:

```text
Cold-start coverage question generated from the selected section because no prior relevant learning history exists.

Returning-run question generated using previous session history without a section-specific weak topic.

Adaptive question generated for section 8 because prior session history marks this section as weak.
```

This makes the output safer and more explainable.

For Scenario B:

```text
Iteration 1:
mode = cold_start
adaptation_reason = cold-start coverage

Iteration 2:
section 6 = returning-run, no section-specific weakness
section 8 = adaptive weak-section reason

Iteration 3:
section 8 = adaptive weak-section reason
```

---

## 16. Weak Topic Tracking

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

Weakness score is computed from previous performance.

This allows the system to detect which topics need more practice in returning runs.

Main file:

```text
app/db/repositories/session_repo.py
```

---

## 17. Interactive API Flow

The interactive API supports real user answers.

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

Output includes:

```text
session_id
document_id
mode
selected_sections
total_questions
adaptation_summary
questions
options
adaptation_reason
```

Important:

```text
/prep/start does not expose correct_answer.
/prep/start does not expose explanation.
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

Output includes:

```text
score
total_questions
correct_count
wrong_count
results
selected_answer
correct_answer
is_correct
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

## 18. CLI Evaluation Flow

The CLI flow supports reviewer evaluation scenarios.

Current final-scale commands use `5` questions per selected section:

```powershell
python -m cli.run_scenario_a --questions-per-section 5
python -m cli.run_scenario_b --questions-per-section 5
python -m cli.run_evaluation --questions-per-section 5
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

## 19. Scenario A

Scenario A runs a cold-start prep over two sections.

Expected output:

```text
Scenario A complete | mode=cold_start | score=50.0
```

Output files:

```text
outputs/scenario_a/questions_scenario_a.json
outputs/scenario_a/kb_snapshot_scenario_a.json
```

With `--questions-per-section 5`, Scenario A generates 10 questions.

---

## 20. Scenario B

Scenario B is the main adaptive evaluation scenario.

It runs:

```text
Iteration 1: sections [5, 8]
Iteration 2: sections [6, 8, 9]
Iteration 3: sections [8]
```

Expected output:

```text
Scenario B iteration 1 complete | mode=cold_start | score=50.0
Scenario B iteration 2 complete | mode=adaptive   | score=66.67
Scenario B iteration 3 complete | mode=adaptive   | score=0.0
```

With `--questions-per-section 5`, the expected counts are:

```text
Iteration 1: 2 sections × 5 = 10 questions
Iteration 2: 3 sections × 5 = 15 questions
Iteration 3: 1 section  × 5 = 5 questions
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

## 21. KB Snapshots

KB snapshots are exported after evaluation runs.

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
adaptation payload
timestamp
recent session history
```

The snapshot endpoint and exported JSON files are designed to support the assessment requirement that the reviewer can verify history-backed adaptation.

Main file:

```text
app/services/snapshot_service.py
```

---

## 22. Exported Reviewer Outputs

Questions and KB snapshots are exported into the `outputs/` directory.

Scenario B structure:

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

These files provide reviewer-visible evidence of:

```text
generated questions
adaptation reasons
answers
scores
weak-topic tracking
session history
cold_start vs adaptive behavior
```

---

## 23. Testing

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

## 24. API Contract Tests

The API contract tests verify:

```text
/prep/start returns questions and options
/prep/start does not expose correct_answer
/prep/start does not expose explanation
/prep/submit returns score
/prep/submit returns correct_answer
/prep/submit returns clarification for wrong answers
```

This helps verify API behavior without relying only on manual Swagger testing.

---

## 25. Recruiter Verification Flow

A reviewer can verify the project with this flow:

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
python -m cli.run_evaluation --questions-per-section 5
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

## 26. API Swagger Verification

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
explanation is hidden
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

Also test:

```text
GET /sessions/{session_id}
GET /kb/snapshot
```

These prove that session history and KB snapshot retrieval work through the API.

---

## 27. Architecture Decisions

### No Authentication

Authentication and authorization are intentionally excluded because the assessment focuses on:

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
CLI
FastAPI
PostgreSQL
Qdrant
LangGraph
JSON outputs
tests
```

A frontend is not required by the assessment.

### Qdrant Is Not the Knowledge Base

Qdrant stores embeddings only.

PostgreSQL stores truth, history, answers, scores, and adaptation data.

### LLM Output Is Not Trusted Blindly

The system validates and normalizes LLM output before persistence.

Backend-generated UUIDs are used for question IDs.

Backend-owned adaptation reasons are used for final output consistency.

---

## 28. Current Working Commands

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
python -m cli.run_scenario_a --questions-per-section 5
```

```powershell
python -m cli.run_scenario_b --questions-per-section 5
```

```powershell
python -m cli.run_evaluation --questions-per-section 5
```

```powershell
python -m pytest tests
```

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 18000
```

---

## 29. Known Limitations

### LLM non-determinism

Groq output can vary between runs. The backend mitigates this through validation, compact prompts, section-by-section generation, retry logic, and backend-owned adaptation metadata.

### First run can be slow

The first evaluation or API request can take several minutes because the embedding model may load and the LLM must generate multiple MCQs.

### No frontend

A frontend is not included because the assessment asks for a CLI-runnable system, REST APIs, and exported evaluation outputs.

### API mode depends on history

If previous sessions exist, `/prep/start` may return `adaptive`. Reset the database for a clean cold-start run.

### External LLM key

Groq is used with a free/developer key. To run without an external LLM key, set:

```env
LLM_PROVIDER=mock
```

---

## 30. Summary

The architecture is backend-first and assessment-focused.

The system demonstrates:

```text
cold_start first run
adaptive returning runs
history-aware question generation
weak-topic focus
section-filtered retrieval
PostgreSQL-backed Knowledge Base
Qdrant-backed semantic retrieval
reviewer-ready Scenario B outputs
FastAPI interactive prep flow
```

The project is designed as a production-style adaptive RAG backend rather than a UI-first demo.