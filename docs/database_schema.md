# Database Schema

## Index

- [1. Overview](#1-overview)
- [2. Storage Tiers & Main Tables](#2-storage-tiers--main-tables)
- [3. Relationship Summary](#3-relationship-summary)
- [4. Table: documents](#4-table-documents)
- [5. Table: sections](#5-table-sections)
- [6. Table: chunks](#6-table-chunks)
- [7. Table: prep_sessions](#7-table-prep_sessions)
- [8. Table: generated_questions](#8-table-generated_questions)
- [9. Table: user_answers](#9-table-user_answers)
- [10. Table: weak_topic_stats](#10-table-weak_topic_stats)
- [11. Table: kb_snapshots](#11-table-kb_snapshots)
- [12. Assessment Query Patterns](#12-assessment-query-patterns)
- [13. Scenario B Database Behavior](#13-scenario-b-database-behavior)
- [14. Why PostgreSQL Instead of JSON Files](#14-why-postgresql-instead-of-json-files)
- [15. Enterprise Hybrid Storage Separation](#15-enterprise-hybrid-storage-separation)
- [16. Files Related to Database](#16-files-related-to-database)
- [17. Summary](#17-summary)

---

# 1. Overview

The **Adaptive Document Preparation System** uses a distributed hybrid storage architecture where each infrastructure layer has a clearly isolated responsibility.

At the center of the system is **PostgreSQL**, which acts as the primary relational transactional database and the main source of truth for all adaptive learning states.

The relational layer stores:

- document metadata
- parsed section boundaries
- chunk references
- adaptive prep sessions
- generated MCQs
- user submissions
- weak-topic analytics
- historical scoring data
- auditable KB snapshots

The system intentionally separates responsibilities across multiple infrastructure tiers:

```text
MinIO Storage  = Immutable raw PDF object vault
PostgreSQL     = Relational history, scoring, analytics, adaptation tracking
Qdrant Store   = Semantic vector embeddings and retrieval only
```

This separation keeps the platform scalable, transparent, and reviewer-friendly.

---

# 2. Storage Tiers & Main Tables

The SQLAlchemy ORM layer currently maps the following tables:

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

All primary keys use UUID-based string identifiers.

---

# 3. Relationship Summary

```text
MinIO Object Storage (raw-dossiers)
            │
            ▼
       documents
            │
            ▼
        sections
            │
            ▼
         chunks

documents
    └── prep_sessions
            └── generated_questions
                    └── user_answers

documents ──► weak_topic_stats
prep_sessions ──► kb_snapshots
```

All major relational dependencies use:

```text
ON DELETE CASCADE
```

This guarantees automatic cleanup of dependent rows whenever root records are removed.

---

# 4. Table: documents

## Purpose

Tracks top-level document metadata and links relational records with the immutable PDF stored inside MinIO object storage.

---

## Columns

| Column | Type | Required | Purpose |
|---|---|---|---|
| id | String(36) | Yes | Primary UUID key |
| filename | String(255) | Yes | Original uploaded filename |
| title | String(255) | No | Human-readable document title |
| source_path | Text | Yes | MinIO object key path |
| total_pages | Integer | Yes | Total PDF page count |
| created_at | DateTime | Yes | Record creation timestamp |

---

# 5. Table: sections

## Purpose

Represents logical document sections used during retrieval and adaptive generation.

The retrieval engine directly filters by `section_number`.

---

## Columns

| Column | Type | Required | Purpose |
|---|---|---|---|
| id | String(36) | Yes | Primary UUID key |
| document_id | ForeignKey(documents.id) | Yes | Parent document reference |
| section_number | Integer | Yes | Human-facing section identifier |
| title | String(255) | Yes | Parsed section title |
| start_page | Integer | Yes | Section starting page |
| end_page | Integer | Yes | Section ending page |
| text | Text | Yes | Full extracted section text |
| created_at | DateTime | Yes | Record timestamp |

---

# 6. Table: chunks

## Purpose

Stores relational tracking metadata corresponding to Qdrant vector payloads.

Each chunk acts as a bridge between:

- PostgreSQL metadata
- Qdrant embeddings
- retrieval audit trails

---

## Columns

| Column | Type | Required | Purpose |
|---|---|---|---|
| id | String(36) | Yes | UUID matching Qdrant payload |
| document_id | ForeignKey(documents.id) | Yes | Parent document |
| section_id | ForeignKey(sections.id) | Yes | Parent section |
| section_number | Integer | Yes | Deterministic retrieval filter |
| chunk_index | Integer | Yes | Chunk ordering index |
| page_number | Integer | No | Source PDF page |
| text | Text | Yes | Full chunk text |
| text_preview | Text | Yes | Sanitized preview snippet |
| qdrant_point_id | String(64) | No | Qdrant vector identifier |
| created_at | DateTime | Yes | Timestamp |

---

# 7. Table: prep_sessions

## Purpose

Tracks adaptive study sessions launched from the Streamlit presentation layer.

This table stores global performance and adaptation state.

---

## Columns

| Column | Type | Required | Purpose |
|---|---|---|---|
| id | String(36) | Yes | Session UUID |
| document_id | ForeignKey(documents.id) | Yes | Parent document |
| mode | String(50) | Yes | `cold_start` or `adaptive` |
| selected_section_numbers | JSON | Yes | Selected sections array |
| score | Float | Yes | Final percentage score |
| total_questions | Integer | Yes | Generated MCQ count |
| correct_count | Integer | Yes | Correct answers |
| wrong_count | Integer | Yes | Incorrect answers |
| adaptation_summary | Text | No | Human-readable adaptive summary |
| adaptation_payload | JSON | No | Internal adaptive metadata |
| created_at | DateTime | Yes | Session timestamp |

---

# 8. Table: generated_questions

## Purpose

Stores validated MCQs generated by the backend orchestration pipeline.

Correct answers remain hidden from the frontend until submission is complete.

---

## Columns

| Column | Type | Required | Purpose |
|---|---|---|---|
| id | String(36) | Yes | Backend-generated UUID |
| session_id | ForeignKey(prep_sessions.id) | Yes | Active session |
| document_id | ForeignKey(documents.id) | Yes | Parent document |
| section_id | ForeignKey(sections.id) | Yes | Source section |
| section_number | Integer | Yes | Section reference |
| topic | String(255) | Yes | Fine-grained topic label |
| difficulty | String(50) | Yes | Difficulty category |
| question_text | Text | Yes | Generated MCQ |
| options | JSON | Yes | A/B/C/D options |
| correct_answer | String(1) | Yes | Correct answer token |
| explanation | Text | Yes | Explanation text |
| adaptation_reason | Text | Yes | Backend-generated adaptive reason |
| source_chunk_ids | JSON | No | Retrieval chunk traceability |
| created_at | DateTime | Yes | Timestamp |

---

## Design Guardrails

### Backend-Owned UUIDs

The LLM never generates database IDs.

All identifiers are created strictly by backend services to avoid collisions or malformed relational states.

---

### Deterministic Adaptation Reasons

`adaptation_reason` is generated by backend logic rather than trusting LLM responses.

Example:

```text
Adaptive question generated for section 8 because previous sessions marked this topic as weak.
```

This keeps adaptation reasoning fully auditable.

---

# 9. Table: user_answers

## Purpose

Stores user submissions captured dynamically from the Streamlit frontend interface.

---

## Columns

| Column | Type | Required | Purpose |
|---|---|---|---|
| id | String(36) | Yes | Primary UUID |
| session_id | ForeignKey(prep_sessions.id) | Yes | Parent session |
| question_id | ForeignKey(generated_questions.id) | Yes | Related question |
| selected_answer | String(1) | Yes | Submitted option |
| correct_answer | String(1) | Yes | Correct answer key |
| is_correct | Boolean | Yes | Binary evaluation result |
| clarification | Text | No | Explanation for incorrect answers |
| created_at | DateTime | Yes | Timestamp |

---

## Bulk Submission Optimization

The frontend sends answers as a unified dictionary payload:

```json
{
  "QUESTION_ID_1": "A",
  "QUESTION_ID_2": "C"
}
```

The backend assembles rows in memory and executes:

```python
db.add_all(answer_rows)
```

This reduces database I/O overhead significantly.

---

# 10. Table: weak_topic_stats

## Purpose

Tracks cumulative weakness analytics across repeated sessions.

This table powers the adaptive intelligence layer.

---

## Columns

| Column | Type | Required | Purpose |
|---|---|---|---|
| id | String(36) | Yes | Primary UUID |
| document_id | ForeignKey(documents.id) | Yes | Parent document |
| section_number | Integer | Yes | Section reference |
| topic | String(255) | Yes | Topic label |
| attempts | Integer | Yes | Total attempts |
| wrong_count | Integer | Yes | Incorrect attempts |
| correct_count | Integer | Yes | Correct attempts |
| weakness_score | Float | Yes | Calculated weakness metric |
| last_seen_at | DateTime | Yes | Last updated timestamp |

---

# 11. Table: kb_snapshots

## Purpose

Maintains auditable snapshots of the knowledge base state after each session.

These snapshots are useful for:

- reviewer verification
- adaptive state tracking
- export auditing
- debugging adaptive behavior

---

## Columns

| Column | Type | Required | Purpose |
|---|---|---|---|
| id | String(36) | Yes | Primary UUID |
| session_id | ForeignKey(prep_sessions.id) | Yes | Related session |
| snapshot_json | JSON | Yes | Serialized KB telemetry |
| created_at | DateTime | Yes | Timestamp |

---

# 12. Assessment Query Patterns

## 12.1 Prior Session Filtering

### Supported Fields

```text
prep_sessions.selected_section_numbers
```

### Used By

```text
app/services/adaptation_service.py
```

The adaptation layer uses historical matches to determine:

```text
cold_start
or
adaptive
```

---

## 12.2 Session-Level Performance Analytics

### Supported Fields

```text
user_answers
generated_questions
```

### Used By

- `GET /sessions/{session_id}`
- Streamlit review screen
- adaptive scoring dashboards

---

## 12.3 Weak Topic Aggregation

### Supported Fields

```text
weak_topic_stats
```

### Index Support

```text
idx_weak_topic_perf_sorting
```

This drives adaptive prompt steering for future sessions.

---

## 12.4 Knowledge Base Snapshot Retrieval

### Supported Fields

```text
kb_snapshots.snapshot_json
```

### Used By

```text
GET /kb/snapshot
```

and Streamlit adaptive telemetry panels.

---

# 13. Scenario B Database Behavior

The schema supports adaptive state transitions across repeated evaluation cycles.

```text
Iteration 1 (Sections 5, 8)
        │
        ▼
mode = cold_start
        │
        ▼
Mistakes logged into weak_topic_stats
        │
        ▼
Iteration 2 (Sections 6, 8, 9)
        │
        ▼
mode = adaptive
        │
        ▼
Historical section 8 weaknesses injected
        │
        ▼
Iteration 3 (Section 8 only)
        │
        ▼
Highly targeted reinforcement generation
```

This is the core adaptive behavior of the system.

---

# 14. Why PostgreSQL Instead of JSON Files

Plain JSON files work well for static logging.

But adaptive preparation systems require:

- relational joins
- indexed lookups
- historical aggregation
- real-time analytics
- scoring calculations
- session filtering
- adaptive state transitions

PostgreSQL enables all of this efficiently while remaining transparent and auditable.

---

# 15. Enterprise Hybrid Storage Separation

The system intentionally separates infrastructure responsibilities across dedicated services.

---

## MinIO Object Storage

Responsible for:

- immutable raw PDFs
- object storage isolation
- distributed file access

---

## PostgreSQL Relational Layer

Responsible for:

- transactional state
- adaptive history
- scoring analytics
- session persistence
- KB snapshots

---

## Qdrant Vector Engine

Responsible for:

- semantic embeddings
- similarity matching
- vector retrieval
- section-filtered searches

---

# 16. Files Related to Database

## ORM Models

```text
app/db/models.py
app/db/session.py
```

---

## Repository Layer

```text
app/db/repositories/session_repo.py
app/db/repositories/document_repo.py
```

---

## Service Layer

```text
app/services/interactive_prep_service.py
```

---

## Database Utility Scripts

```text
cli/reset_db.py
```

---

# 17. Summary

The database architecture was designed to remain:

- transparent
- scalable
- reviewer-friendly
- adaptive
- audit-safe
- production-oriented

By combining PostgreSQL, MinIO, and Qdrant into isolated infrastructure tiers, the system maintains reliable adaptive learning behavior while preserving strict retrieval integrity and complete historical traceability across all study sessions.