# Database Schema

## 1. Overview

PostgreSQL is the source of truth for the Adaptive Document Preparation System.

The database stores:

```text
document metadata
parsed PDF sections
section chunks
prep sessions
generated MCQs
submitted or simulated answers
score results
weak-topic statistics
KB snapshots
adaptation metadata
```

Qdrant is used only for semantic chunk retrieval. It stores embeddings and retrieval metadata, but it does not store the learning history.

The main database design rule is:

```text
PostgreSQL = truth, history, scoring, adaptation, snapshots
Qdrant     = semantic retrieval only
```

---

## 2. Main Tables

The current SQLAlchemy models define these PostgreSQL tables:

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

All primary IDs are UUID strings.

---

## 3. Relationship Summary

```text
documents
  └── sections
        └── chunks

documents
  └── prep_sessions
        └── generated_questions
              └── user_answers

documents
  └── weak_topic_stats

prep_sessions
  └── kb_snapshots
```

More specifically:

```text
documents.id -> sections.document_id
documents.id -> chunks.document_id
sections.id  -> chunks.section_id

documents.id      -> prep_sessions.document_id
prep_sessions.id  -> generated_questions.session_id
documents.id      -> generated_questions.document_id
sections.id       -> generated_questions.section_id

prep_sessions.id       -> user_answers.session_id
generated_questions.id -> user_answers.question_id

documents.id      -> weak_topic_stats.document_id
prep_sessions.id  -> kb_snapshots.session_id
```

Most relationships use cascade deletion so that deleting a document or session also removes dependent child records.

---

## 4. Table: documents

Stores metadata about ingested PDF documents.

### Purpose

This table identifies the source PDF and tracks top-level document metadata.

### Columns

| Column | Type | Required | Purpose |
|---|---|---:|---|
| `id` | `String(36)` | Yes | Primary key UUID |
| `filename` | `String(255)` | Yes | Original PDF filename |
| `title` | `String(255)` | No | Parsed or assigned document title |
| `source_path` | `Text` | Yes | Local/source path of the PDF |
| `total_pages` | `Integer` | Yes | Number of PDF pages |
| `created_at` | `DateTime` | Yes | Record creation timestamp |

### Related tables

```text
documents -> sections
documents -> chunks
documents -> prep_sessions
documents -> generated_questions
documents -> weak_topic_stats
```

---

## 5. Table: sections

Stores parsed PDF sections.

### Purpose

This table maps the structured PDF into section-level study units. Users select sections by `section_number`.

### Columns

| Column | Type | Required | Purpose |
|---|---|---:|---|
| `id` | `String(36)` | Yes | Primary key UUID |
| `document_id` | `ForeignKey(documents.id)` | Yes | Parent document |
| `section_number` | `Integer` | Yes | Human-facing section number |
| `title` | `String(255)` | Yes | Section title |
| `start_page` | `Integer` | Yes | First page of section |
| `end_page` | `Integer` | Yes | Last page of section |
| `text` | `Text` | Yes | Full section text |
| `created_at` | `DateTime` | Yes | Record creation timestamp |

### Related tables

```text
sections -> chunks
sections -> generated_questions
```

### Current section mapping

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

---

## 6. Table: chunks

Stores smaller text chunks created from parsed sections.

### Purpose

Chunks are the bridge between PostgreSQL and Qdrant.

PostgreSQL stores the full chunk text and metadata. Qdrant stores the vector embedding for the same chunk.

### Columns

| Column | Type | Required | Purpose |
|---|---|---:|---|
| `id` | `String(36)` | Yes | Primary key UUID |
| `document_id` | `ForeignKey(documents.id)` | Yes | Parent document |
| `section_id` | `ForeignKey(sections.id)` | Yes | Parent section |
| `section_number` | `Integer` | Yes | Section number for retrieval filtering |
| `chunk_index` | `Integer` | Yes | Chunk order within section |
| `page_number` | `Integer` | No | Source page number if available |
| `text` | `Text` | Yes | Full chunk text |
| `text_preview` | `Text` | Yes | Short preview for retrieval metadata |
| `qdrant_point_id` | `String(64)` | No | Matching Qdrant point ID |
| `created_at` | `DateTime` | Yes | Record creation timestamp |

### Qdrant metadata mirror

Each chunk indexed in Qdrant stores metadata such as:

```text
document_id
section_id
section_number
chunk_id
chunk_index
page_number
text_preview
```

### Retrieval rule

For selected sections such as:

```text
[5, 8]
```

Qdrant retrieval is filtered by `section_number`, and the backend reads the trusted chunk text from PostgreSQL.

---

## 7. Table: prep_sessions

Stores each preparation run.

### Purpose

This table records the session-level result for a prep attempt.

A prep session may be:

```text
cold_start
adaptive
```

### Columns

| Column | Type | Required | Purpose |
|---|---|---:|---|
| `id` | `String(36)` | Yes | Primary key UUID |
| `document_id` | `ForeignKey(documents.id)` | Yes | Document used for prep |
| `mode` | `String(50)` | Yes | `cold_start` or `adaptive` |
| `selected_section_numbers` | `JSON` | Yes | List of selected section numbers |
| `score` | `Float` | Yes | Final session score |
| `total_questions` | `Integer` | Yes | Number of questions in session |
| `correct_count` | `Integer` | Yes | Number of correct answers |
| `wrong_count` | `Integer` | Yes | Number of wrong answers |
| `adaptation_summary` | `Text` | No | Human-readable adaptation summary |
| `adaptation_payload` | `JSON` | No | Full adaptation context used for generation |
| `created_at` | `DateTime` | Yes | Record creation timestamp |

### Related tables

```text
prep_sessions -> generated_questions
prep_sessions -> user_answers
prep_sessions -> kb_snapshots
```

### Example selected sections

Scenario B uses:

```text
Iteration 1: [5, 8]
Iteration 2: [6, 8, 9]
Iteration 3: [8]
```

---

## 8. Table: generated_questions

Stores generated MCQs.

### Purpose

This table stores every generated question, its options, correct answer, explanation, section reference, source chunks, and adaptation reason.

### Columns

| Column | Type | Required | Purpose |
|---|---|---:|---|
| `id` | `String(36)` | Yes | Primary key UUID generated by backend |
| `session_id` | `ForeignKey(prep_sessions.id)` | Yes | Parent prep session |
| `document_id` | `ForeignKey(documents.id)` | Yes | Source document |
| `section_id` | `ForeignKey(sections.id)` | Yes | Source section |
| `section_number` | `Integer` | Yes | Source section number |
| `topic` | `String(255)` | Yes | Question topic |
| `difficulty` | `String(50)` | Yes | Difficulty label |
| `question_text` | `Text` | Yes | MCQ question text |
| `options` | `JSON` | Yes | MCQ options A/B/C/D |
| `correct_answer` | `String(1)` | Yes | Correct answer key |
| `explanation` | `Text` | Yes | Explanation or clarification basis |
| `adaptation_reason` | `Text` | Yes | Backend-owned adaptation reason |
| `source_chunk_ids` | `JSON` | No | Source chunk UUIDs used for grounding |
| `created_at` | `DateTime` | Yes | Record creation timestamp |

### Important design decision

The backend generates `question_id` values.

The LLM is not trusted to generate database primary keys. This prevents duplicate IDs and avoids making model output responsible for database identity.

### Adaptation reason

The final `adaptation_reason` is owned by the backend, not the LLM.

Examples:

```text
Cold-start coverage question generated from the selected section because no prior relevant learning history exists.

Returning-run question generated using previous session history without a section-specific weak topic.

Adaptive question generated for section 8 because prior session history marks this section as weak.
```

---

## 9. Table: user_answers

Stores submitted or simulated answers.

### Purpose

This table stores question-level answer results for each prep session.

Answers may come from:

```text
simulated CLI scenario runs
real interactive API submissions
```

### Columns

| Column | Type | Required | Purpose |
|---|---|---:|---|
| `id` | `String(36)` | Yes | Primary key UUID |
| `session_id` | `ForeignKey(prep_sessions.id)` | Yes | Parent prep session |
| `question_id` | `ForeignKey(generated_questions.id)` | Yes | Answered question |
| `selected_answer` | `String(1)` | Yes | User or simulated answer |
| `correct_answer` | `String(1)` | Yes | Correct answer key |
| `is_correct` | `Boolean` | Yes | Whether selected answer is correct |
| `clarification` | `Text` | No | Clarification for wrong answers |
| `created_at` | `DateTime` | Yes | Record creation timestamp |

### Query use

This table supports:

```text
retrieve question-level right/wrong results
show correct answers after submission
build weak-topic statistics
generate session history
build KB snapshots
```

---

## 10. Table: weak_topic_stats

Stores topic-level learning performance over time.

### Purpose

This table allows the system to identify weak topics and adapt future question generation.

### Columns

| Column | Type | Required | Purpose |
|---|---|---:|---|
| `id` | `String(36)` | Yes | Primary key UUID |
| `document_id` | `ForeignKey(documents.id)` | Yes | Source document |
| `section_number` | `Integer` | Yes | Section number |
| `topic` | `String(255)` | Yes | Topic label |
| `attempts` | `Integer` | Yes | Total attempts for topic |
| `wrong_count` | `Integer` | Yes | Number of wrong answers |
| `correct_count` | `Integer` | Yes | Number of correct answers |
| `weakness_score` | `Float` | Yes | Computed weakness score |
| `last_seen_at` | `DateTime` | Yes | Last update timestamp |

### Weakness score

The weakness score represents how weak a topic is based on answer history.

A simple interpretation:

```text
higher wrong_count and lower correct_count -> stronger weakness
```

Scenario B uses this to keep section 8 weak across iterations.

---

## 11. Table: kb_snapshots

Stores human-readable KB snapshots.

### Purpose

This table persists reviewer-readable snapshots of recent learning history.

A KB snapshot helps reviewers verify that:

```text
history is being stored
questions and answers are persisted
weak topics are tracked
adaptation is grounded in previous sessions
```

### Columns

| Column | Type | Required | Purpose |
|---|---|---:|---|
| `id` | `String(36)` | Yes | Primary key UUID |
| `session_id` | `ForeignKey(prep_sessions.id)` | Yes | Session associated with snapshot |
| `snapshot_json` | `JSON` | Yes | Human-readable snapshot payload |
| `created_at` | `DateTime` | Yes | Snapshot creation timestamp |

### Snapshot contents

Snapshots include:

```text
snapshot_created_at
current_session_id
recent_session_count
recent_sessions
session scores
selected sections
questions asked
user answers
correct answers
wrong answers
clarifications
adaptation payloads
weak topics
```

The snapshot design supports the assessment requirement:

```text
Retrieve a snapshot of the KB state at the end of any given session.
```

---

## 12. Assessment Query Patterns

The assessment requires the KB to support specific query patterns.

### 12.1 Given a set of section IDs, retrieve prior prep sessions involving those sections

Supported by:

```text
prep_sessions.selected_section_numbers
prep_sessions.document_id
```

Used by:

```text
app/services/adaptation_service.py
```

Purpose:

```text
detect cold_start vs adaptive
find relevant prior sessions
build adaptation payload
```

---

### 12.2 Given a session, retrieve question-level right/wrong results

Supported by:

```text
prep_sessions
generated_questions
user_answers
```

Used by:

```text
GET /sessions/{session_id}
```

Purpose:

```text
show question text
show selected answer
show correct answer
show is_correct
show explanation or clarification
```

---

### 12.3 Identify topics/questions answered incorrectly across multiple sessions

Supported by:

```text
user_answers
generated_questions.topic
generated_questions.section_number
weak_topic_stats
```

Used by:

```text
app/db/repositories/session_repo.py
app/services/adaptation_service.py
```

Purpose:

```text
compute weak topics
guide adaptive generation
prioritize repeated mistakes
```

---

### 12.4 Retrieve a snapshot of the KB state at the end of a session

Supported by:

```text
kb_snapshots
```

Used by:

```text
app/services/snapshot_service.py
GET /kb/snapshot
scenario output exports
```

Purpose:

```text
provide reviewer-visible evidence of stored history and adaptive grounding
```

---

## 13. Scenario B Database Behavior

Scenario B proves that the schema supports adaptive history.

### Iteration 1

```text
selected sections = [5, 8]
mode = cold_start
score = 50.0
section 8 answers are simulated wrong
weak_topic_stats begins tracking section 8 weaknesses
```

### Iteration 2

```text
selected sections = [6, 8, 9]
mode = adaptive
score = 66.67
section 8 is recognized as weak from iteration 1
section 6 and 9 are returning-run context but not weak-specific
```

### Iteration 3

```text
selected sections = [8]
mode = adaptive
score = 0.0
only weak section 8 is selected
all section 8 questions are adaptive weak-section questions
```

The database stores all generated questions, answers, scores, weak topics, and snapshots for each iteration.

---

## 14. Why PostgreSQL Instead of Only JSON Files

PostgreSQL is used because the system needs queryable structured history.

The project must support:

```text
session lookup by selected sections
question-level result retrieval
weak-topic aggregation
snapshot generation
future adaptive prompting
```

Plain JSON files would be enough for static outputs, but they would be weaker for history-aware adaptive behavior.

---

## 15. Why Qdrant Is Separate from PostgreSQL

PostgreSQL is excellent for structured history and relational queries.

Qdrant is better for vector similarity search.

The separation keeps responsibilities clean:

```text
PostgreSQL:
  truth
  history
  sessions
  answers
  scores
  weak topics
  snapshots

Qdrant:
  vector embeddings
  semantic retrieval
  selected-section filtering
```

This hybrid design makes the system both queryable and retrieval-capable.

---

## 16. Files Related to Database

Database models:

```text
app/db/models.py
```

Database session/engine:

```text
app/db/session.py
```

Repositories:

```text
app/db/repositories/document_repo.py
app/db/repositories/session_repo.py
app/db/repositories/question_repo.py
app/db/repositories/snapshot_repo.py
```

Reset command:

```text
cli/reset_db.py
```

Ingestion command:

```text
cli/ingest_pdf.py
```

Scenario persistence flow:

```text
app/services/prep_service.py
app/workflow/nodes.py
app/workflow/prep_graph.py
```

Interactive API persistence flow:

```text
app/services/interactive_prep_service.py
app/api/routes_prep.py
```

---

## 17. Summary

The database design satisfies the assessment’s Knowledge Base requirements.

It supports:

```text
section-based prior session retrieval
session-level and question-level history
correct/wrong answer storage
weak-topic detection
adaptive generation context
reviewer-readable KB snapshots
Scenario A and Scenario B output generation
```

The schema is intentionally simple, auditable, and suitable for a production-style backend assessment project.