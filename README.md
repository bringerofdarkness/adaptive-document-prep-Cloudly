# Adaptive Document Preparation System

A backend-driven adaptive RAG system for PDF-based preparation and MCQ generation.

This project ingests a structured multi-section PDF, stores document sections and chunks in PostgreSQL, indexes chunks in Qdrant for deterministic section-filtered retrieval, generates MCQs with an LLM, validates structured MCQ output, collects or simulates answers, scores preparation sessions, stores full learning history, identifies weak topics, and adapts future question generation based on previous mistakes.

---

## Current Status

This project is currently in the **core working stage**.

The main assessment backbone is working:

- PDF ingestion works.
- Section extraction works.
- PostgreSQL persistence works.
- Qdrant indexing works.
- Strict selected-section retrieval works.
- Groq-based MCQ generation works.
- Mock fallback generation works.
- LangGraph orchestration works.
- Scenario A runs successfully.
- Scenario B runs successfully.
- Scenario B demonstrates adaptive behavior.
- KB snapshot JSON files are exported.
- Questions JSON files are exported.
- FastAPI routes are available.
- `/prep/start` works.
- `/prep/submit` works.
- Basic tests pass.

The project is not fully final yet. Remaining work includes cleanup, stronger API tests, encoding normalization, final Dockerfile, documentation files, structured logging, and final README polish.

---

## Repository

```text
https://github.com/bringerofdarkness/adaptive-document-prep-Cloudly
```

---

## Local Project Root

```text
F:\Self Project\adaptive-document-prep
```

---

## Project Goal

The goal is to build a production-style AI/ML internship take-home project called **Adaptive Document Preparation System**.

The system should:

1. Ingest a multi-section PDF.
2. Allow a user to select one or more sections.
3. Retrieve only chunks from the selected sections.
4. Generate MCQs from those sections using an LLM.
5. Validate MCQ output strictly.
6. Collect real or simulated answers.
7. Score the preparation session.
8. Show correct answers and clarifications for wrong answers.
9. Persist complete session history in PostgreSQL.
10. Detect weak topics from previous wrong answers.
11. Adapt future question generation based on historical weak areas.
12. Export reviewer-ready Scenario A and Scenario B outputs.

The most important feature is **adaptive intelligence**.

The system must distinguish:

```text
first-time run  -> cold_start
returning run   -> adaptive
```

---

## Final Project Pitch

This project is a production-style adaptive RAG backend that ingests a structured PDF, stores section chunks in Qdrant for deterministic section-filtered retrieval, stores all sessions and learning history in PostgreSQL, generates MCQs through an LLM, validates structured outputs, scores user answers, identifies weak topics over time, and uses LangGraph to adapt future question generation based on previous mistakes while exporting reviewer-ready Scenario B outputs.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| Workflow orchestration | LangGraph |
| LLM provider | Groq primary, mock fallback |
| Optional LLM provider | Gemini scaffold |
| PDF parsing | PyMuPDF |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector database | Qdrant |
| Structured Knowledge Base | PostgreSQL |
| ORM | SQLAlchemy |
| CLI | Typer |
| Testing | Pytest |
| Containerization | Docker Compose |
| Optional UI later | Streamlit |

---

## Architecture Philosophy

The project uses a hybrid storage architecture.

### PostgreSQL

PostgreSQL is the source of truth.

It stores:

- documents
- sections
- chunks
- prep sessions
- generated questions
- submitted answers
- correct/wrong results
- scores
- weak-topic statistics
- adaptation metadata
- KB snapshots

### Qdrant

Qdrant is used only for semantic retrieval.

It stores vector embeddings of chunks with metadata:

```text
document_id
section_id
section_number
chunk_id
chunk_index
page_number
text_preview
```

Qdrant is not used as the main Knowledge Base.

The design rule is:

```text
PostgreSQL = truth and history
Qdrant     = semantic retrieval
```

This prevents the vector database from becoming an unreliable source of session truth.

---

## Project Structure

```text
adaptive-document-prep/
  app/
    main.py

    api/
      routes_documents.py
      routes_health.py
      routes_kb.py
      routes_prep.py
      routes_sessions.py

    core/
      config.py
      exceptions.py
      logging.py

    db/
      models.py
      session.py
      repositories/
        document_repo.py
        question_repo.py
        session_repo.py
        snapshot_repo.py

    ingestion/
      pdf_loader.py
      section_parser.py
      chunker.py

    retrieval/
      embeddings.py
      qdrant_store.py
      retriever.py

    llm/
      providers.py
      prompts.py
      mcq_generator.py
      output_parser.py

    workflow/
      state.py
      nodes.py
      prep_graph.py

    services/
      adaptation_service.py
      interactive_prep_service.py
      prep_service.py
      question_export_service.py
      scoring_service.py
      snapshot_service.py

    schemas/
      document.py
      prep.py
      question.py
      session.py

  cli/
    ingest_pdf.py
    index_qdrant.py
    reset_db.py
    run_evaluation.py
    run_scenario_a.py
    run_scenario_b.py

  data/
    SLATEFALL_DOSSIER.pdf
    intern_assessment_brief.pdf

  outputs/
    scenario_a/
    scenario_b_iter1/
    scenario_b_iter2/
    scenario_b_iter3/

  tests/
    test_mcq_validation.py
    test_prep_flow.py

  docs/
    architecture.md
    database_schema.md
    adaptation_strategy.md

  docker-compose.yml
  Dockerfile
  requirements.txt
  .env.example
  README.md
  pyproject.toml
```

---

## Environment Setup

### 1. Create and activate virtual environment

```powershell
cd "F:\Self Project\adaptive-document-prep"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Create `.env`

```powershell
Copy-Item .env.example .env
```

Example `.env`:

```env
APP_NAME=Adaptive Document Preparation System
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

LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=
```

For deterministic local testing without Groq:

```env
LLM_PROVIDER=mock
```

Do not commit `.env`.

---

## Docker Services

Start PostgreSQL and Qdrant:

```powershell
docker compose up -d
```

Check containers:

```powershell
docker ps
```

Expected project containers:

```text
adaptive_doc_postgres
adaptive_doc_qdrant
```

Verify PostgreSQL:

```powershell
docker exec adaptive_doc_postgres pg_isready -U postgres -d adaptive_doc_prep
```

Expected:

```text
/var/run/postgresql:5432 - accepting connections
```

Verify Qdrant:

```powershell
Invoke-RestMethod http://127.0.0.1:16433/healthz
```

Expected:

```text
healthz check passed
```

---

## Database Setup

Reset database tables:

```powershell
python -m cli.reset_db reset
```

Expected:

```text
Dropping existing tables...
Creating tables...
Database reset complete.
```

---

## PDF Ingestion

The main PDF corpus should be located at:

```text
data/SLATEFALL_DOSSIER.pdf
```

Run ingestion:

```powershell
python -m cli.ingest_pdf
```

Expected:

```text
Ingested document_id: ...
Pages: 50
Sections: 10
Chunks: 101
```

Index chunks into Qdrant:

```powershell
python -m cli.index_qdrant
```

Expected:

```text
Latest document_id: ...
Chunks to index: 101
Qdrant indexing complete.
```

---

## PDF Section Mapping

The PDF parser currently detects 10 sections:

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

## Retrieval Behavior

Retrieval is deterministic and section-filtered.

If the selected sections are:

```text
[5, 8]
```

then the retriever only retrieves chunks from sections 5 and 8.

This prevents out-of-section MCQ generation.

Qdrant filtering uses metadata such as:

```text
document_id
section_number
```

The vector database returns chunk IDs and metadata, while full chunk text is read back from PostgreSQL.

---

## MCQ Format

Each MCQ follows this structure:

```json
{
  "question_id": "backend-generated UUID",
  "section_id": "section UUID",
  "section_number": 8,
  "topic": "Safehouses",
  "difficulty": "medium",
  "question": "What is the primary operational base of the asset?",
  "options": {
    "A": "Option A",
    "B": "Option B",
    "C": "Option C",
    "D": "Option D"
  },
  "correct_answer": "A",
  "explanation": "Concise explanation",
  "adaptation_reason": "Weak topic: Safehouses",
  "source_chunk_ids": ["chunk UUID"]
}
```

Important implementation decision:

```text
The backend generates question_id values.
The LLM is not trusted to generate database primary keys.
```

This fixed duplicate primary key errors caused by repeated LLM-generated IDs.

---

## MCQ Validation

The system validates:

- exactly 4 options
- options must be A, B, C, D
- correct answer must be A, B, C, or D
- non-empty topic
- non-empty explanation
- non-empty adaptation reason
- no out-of-selected-section questions
- expected number of questions per selected section
- duplicate question text detection

Validation files:

```text
app/llm/output_parser.py
app/schemas/question.py
```

---

## LLM Provider

The active real LLM provider is Groq.

Provider implementation:

```text
app/llm/providers.py
```

Groq is configured through:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
```

Mock fallback is available through:

```env
LLM_PROVIDER=mock
```

The mock provider is useful for deterministic local testing and CI-style tests.

---

## Prompt and Token Management

Groq free-tier token limits caused request-size failures earlier.

Fixes implemented:

- compact context chunks
- reduced chunk character length
- reduced number of context chunks
- compact adaptation payload
- reduced max tokens
- section-by-section LLM generation
- validation retry

This keeps requests smaller and more reliable.

---

## LangGraph Workflow

The preparation flow is modeled as a LangGraph graph.

Workflow nodes:

1. Load latest document and prior history.
2. Build adaptation payload.
3. Retrieve selected-section chunks.
4. Generate MCQs.
5. Simulate or collect answers.
6. Score answers.
7. Persist session and weak-topic updates.

Files:

```text
app/workflow/state.py
app/workflow/nodes.py
app/workflow/prep_graph.py
```

Graph state includes:

```text
selected_section_numbers
retrieved_chunks
adaptation_payload
mcq_set
answers
score
session
result
```

---

## Adaptive Logic

Adaptive logic is implemented in:

```text
app/services/adaptation_service.py
```

The adaptation service checks PostgreSQL history and builds:

```text
is_returning_run
mode
relevant_prior_session_count
weak_topics
mastered_question_texts
previous_wrong_question_texts
summary
```

Modes:

```text
cold_start = no relevant prior history
adaptive   = prior history found for selected sections
```

Weak topics are updated from wrong answers.

Example adaptation reasons:

```text
Weak topic: Safehouses
Prioritized weak topic: Operational Territory
Avoided close repeat of mastered question
```

---

## Scenario A

Scenario A runs a cold-start prep over two sections.

Command:

```powershell
python -m cli.run_scenario_a --questions-per-section 2
```

Expected:

```text
Scenario A complete | session=... | mode=cold_start | score=50.0
```

Output files:

```text
outputs/scenario_a/questions_scenario_a.json
outputs/scenario_a/kb_snapshot_scenario_a.json
```

---

## Scenario B

Scenario B is the main adaptive evaluation scenario.

Command:

```powershell
python -m cli.run_scenario_b --questions-per-section 2
```

Expected behavior:

```text
Scenario B iteration 1 complete | ... | mode=cold_start | score=50.0
Scenario B iteration 2 complete | ... | mode=adaptive | score=66.67
Scenario B iteration 3 complete | ... | mode=adaptive | score=0.0
```

Why these scores happen:

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

## Unified Evaluation Command

Run Scenario A and Scenario B together:

```powershell
python -m cli.run_evaluation --questions-per-section 2
```

Expected:

```text
Running Scenario A...
Scenario A complete | ... | mode=cold_start | score=50.0
Running Scenario B...
Scenario B iteration 1 complete | ... | mode=cold_start | score=50.0
Scenario B iteration 2 complete | ... | mode=adaptive | score=66.67
Scenario B iteration 3 complete | ... | mode=adaptive | score=0.0
Evaluation complete. Outputs are available under the outputs directory.
```

---

## FastAPI API

Run API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 18000
```

Swagger:

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

## Interactive API Flow

### Start a prep session

Endpoint:

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

Expected response:

```json
{
  "session_id": "...",
  "document_id": "...",
  "mode": "adaptive",
  "selected_sections": [5, 8],
  "total_questions": 2,
  "adaptation_summary": "...",
  "questions": [
    {
      "question_id": "...",
      "section_number": 5,
      "topic": "...",
      "difficulty": "medium",
      "question": "...",
      "options": {
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
      },
      "adaptation_reason": "..."
    }
  ]
}
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

Request:

```json
{
  "session_id": "session-id",
  "answers": {
    "question-id-1": "A",
    "question-id-2": "B"
  }
}
```

Expected response:

```json
{
  "session_id": "...",
  "score": 50.0,
  "total_questions": 2,
  "correct_count": 1,
  "wrong_count": 1,
  "results": [
    {
      "question_id": "...",
      "section_number": 8,
      "topic": "Safehouses",
      "selected_answer": "B",
      "correct_answer": "A",
      "is_correct": false,
      "clarification": "..."
    }
  ]
}
```

Important:

```text
/prep/submit exposes correct_answer and clarification after answer submission.
```

---

## Latest API Test Observation

Latest `/prep/start` test worked:

```text
session_id generated
document_id returned
mode returned as adaptive
questions returned
options returned
correct_answer hidden
adaptation_reason visible
```

Known issue from latest API response:

```text
"Cuartel ValparaÃ­so" appears instead of "Cuartel Valparaíso"
```

This is an encoding/mojibake cleanup issue and should be fixed before final submission.

---

## Tests

Run tests:

```powershell
python -m pytest tests
```

Current result:

```text
4 passed
```

Current tests cover:

- valid MCQ payload validation
- out-of-selected-section rejection
- invalid question distribution rejection
- scoring logic

Test files:

```text
tests/test_mcq_validation.py
tests/test_prep_flow.py
```

---

## Current Recruiter Audit Status

Current pass items:

```text
Docker services running
Code compile passes
Pytest passes
Scenario A outputs generated
Scenario B outputs generated
Scenario B iteration 1 = cold_start
Scenario B iteration 2 = adaptive
Scenario B iteration 3 = adaptive
KB snapshots generated
questions JSON generated
adaptation_reason visible
FastAPI Swagger available
/prep/start works
/prep/submit works
```

Current unfinished items:

```text
Encoding cleanup for mojibake text such as ValparaÃ­so
More tests for API interactive flow
Cleanup old naming if run_mock_prep_session still exists anywhere
Final Dockerfile
Final README polish
docs/architecture.md
docs/database_schema.md
docs/adaptation_strategy.md
Structured logging
Final GitHub cleanup
```

---

## Known Issues

### 1. Encoding issue

Some LLM output may contain mojibake:

```text
Cuartel ValparaÃ­so
```

Expected:

```text
Cuartel Valparaíso
```

Fix area:

```text
app/llm/output_parser.py
```

The output normalization layer should clean common mojibake patterns before persistence and response.

### 2. Existing database history affects API mode

If previous Scenario B or API sessions exist, `/prep/start` may return:

```text
mode = adaptive
```

This is expected.

For a fresh cold-start API test, prep history must be cleared first.

### 3. LLM non-determinism

Groq output may vary. The backend validation layer protects against many malformed outputs, but very poor LLM output may still fail.

### 4. HF token warning

The console may show:

```text
Warning: You are sending unauthenticated requests to the HF Hub.
```

This is not a failure. The embedding model still loads.

---

## Commands That Currently Work

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
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 18000
```

---

## Recruiter Verification Flow

A recruiter should be able to check the project like this.

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

### 5. Run full evaluation

```powershell
python -m cli.run_evaluation --questions-per-section 2
```

### 6. Confirm Scenario B outputs

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
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 18000
```

Open:

```text
http://127.0.0.1:18000/docs
```

---

## Immediate Next Implementation Plan

### Step 1: Fix encoding cleanup

Fix mojibake issue:

```text
ValparaÃ­so -> Valparaíso
```

Likely location:

```text
app/llm/output_parser.py
```

Ensure cleanup applies to:

- question text
- option text
- explanation
- topic
- adaptation_reason

### Step 2: Add interactive API tests

Add tests for:

```text
POST /prep/start
POST /prep/submit
```

Test expectations:

- `/prep/start` does not return correct_answer
- `/prep/start` returns options
- `/prep/submit` returns score
- `/prep/submit` returns correct_answer
- `/prep/submit` returns clarification for wrong answers
- duplicate submit should fail

### Step 3: Clean old names

Search for:

```text
run_mock_prep_session
```

Rename to:

```text
run_prep_session
```

if still present.

### Step 4: Improve documentation files

Add:

```text
docs/architecture.md
docs/database_schema.md
docs/adaptation_strategy.md
```

### Step 5: Finalize Dockerfile

Make sure reviewer can run the API cleanly.

### Step 6: Add structured logging

Add logs for:

```text
session_id
selected_sections
mode
retrieved_chunk_count
llm_provider
score
weak_topic_count
```

### Step 7: Final README polish

After implementation is stable, rewrite the final README for submission.

---

## Git Workflow

Use frequent push workflow:

```powershell
git status
git add .
git commit -m "Meaningful checkpoint message"
git push
```

Important:

```text
Do not commit .env.
Do not commit API keys.
Do not commit unnecessary temporary files.
```

---

## Current Recommended Next Action

Do not add new large features immediately.

First finish the current interactive API cleanup:

1. Fix encoding issue.
2. Run Scenario B again.
3. Test `/prep/start`.
4. Test `/prep/submit`.
5. Add API tests.
6. Push stable checkpoint.

After that, continue with documentation and final polish.