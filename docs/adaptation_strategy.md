# Adaptation Strategy

## 1. Overview

The Adaptive Document Preparation System is designed to prove history-aware preparation behavior.

The system does not only generate questions from selected PDF sections. It also checks previous preparation history, identifies weak topics, and adapts future MCQ generation based on earlier mistakes.

The core adaptation requirement is:

```text
first relevant run     -> cold_start
returning relevant run -> adaptive
```

This behavior is most clearly demonstrated in Scenario B:

```text
Iteration 1: sections [5, 8]    -> cold_start
Iteration 2: sections [6, 8, 9] -> adaptive
Iteration 3: sections [8]       -> adaptive
```

The repeated use of section 8 allows the reviewer to verify that previous wrong answers influence later generation.

---

## 2. Adaptation Goal

The adaptation layer exists to answer these questions before MCQ generation:

```text
Has the learner studied these selected sections before?
Which topics were answered incorrectly?
Which questions or topics appear mastered?
Which previous wrong questions should influence the next run?
Should this run be cold_start or adaptive?
```

The goal is to make future questions more useful by focusing on weak areas and avoiding excessive repetition of mastered content.

---

## 3. Main Design Rule

The system uses PostgreSQL as the source of truth for adaptation.

```text
PostgreSQL = learning history and adaptation source
LLM        = question content generator
Backend    = adaptation metadata owner
```

The LLM is not trusted to decide whether a question is adaptive or cold-start.

The backend owns the final `adaptation_reason` field because only the backend has reliable access to the actual stored history.

---

## 4. Adaptation Inputs

The adaptation service receives:

```text
database session
document_id
selected_section_numbers
```

It checks PostgreSQL history for previous prep sessions related to the selected sections.

Important tables:

```text
prep_sessions
generated_questions
user_answers
weak_topic_stats
```

Main file:

```text
app/services/adaptation_service.py
```

---

## 5. Adaptation Payload

Before question generation, the system builds an adaptation payload.

The payload contains:

```text
is_returning_run
mode
relevant_prior_session_count
weak_topics
mastered_question_texts
previous_wrong_question_texts
summary
```

Example cold-start payload:

```json
{
  "is_returning_run": false,
  "mode": "cold_start",
  "relevant_prior_session_count": 0,
  "weak_topics": [],
  "mastered_question_texts": [],
  "previous_wrong_question_texts": [],
  "summary": "Cold-start run: no prior relevant history found."
}
```

Example adaptive payload:

```json
{
  "is_returning_run": true,
  "mode": "adaptive",
  "relevant_prior_session_count": 1,
  "weak_topics": [
    {
      "section_number": 8,
      "topic": "Operational Territory",
      "attempts": 1,
      "wrong_count": 1,
      "correct_count": 0,
      "weakness_score": 1.0
    }
  ],
  "mastered_question_texts": [],
  "previous_wrong_question_texts": [
    "What is the primary operational base of the asset?"
  ],
  "summary": "Adaptive run: prior history found. Focus more on weak topics and avoid excessive repetition of mastered questions."
}
```

---

## 6. Mode Detection

The mode is selected using prior relevant history.

### Cold Start

A run is `cold_start` when no prior relevant history is found for the selected sections.

```text
No relevant previous session -> cold_start
```

Cold-start generation focuses on baseline coverage of the selected section content.

### Adaptive

A run is `adaptive` when previous relevant history exists.

```text
Relevant previous session exists -> adaptive
```

Adaptive generation uses weak topics, previous wrong questions, and mastered question history to guide the next MCQ set.

---

## 7. Relevant Prior Session Logic

A prior session is relevant when it belongs to the same document and overlaps with the currently selected sections.

Example:

```text
Current selected sections: [6, 8, 9]

Previous session sections: [5, 8]

Overlap: section 8

Result: previous session is relevant
```

This is why Scenario B iteration 2 becomes adaptive after iteration 1.

---

## 8. Weak Topic Detection

Weak topics are tracked in PostgreSQL through `weak_topic_stats`.

The table records:

```text
document_id
section_number
topic
attempts
wrong_count
correct_count
weakness_score
last_seen_at
```

When a learner answers incorrectly, the system updates the weak topic statistics.

A topic becomes weak when wrong answers accumulate.

A simplified interpretation:

```text
more wrong answers -> higher weakness_score
more correct answers -> lower weakness_score
```

The adaptation service uses these stats to choose topics that should receive more focus in later runs.

---

## 9. Mastered Question Tracking

The system also stores and retrieves previously correct questions.

These are used as mastered question references.

Purpose:

```text
avoid excessive repetition
preserve question variety
prevent repeated easy questions
```

This does not mean the system never asks similar concepts again. It means the prompt is informed by what the learner already answered correctly.

---

## 10. Previous Wrong Question Tracking

Previous wrong question texts are included in the adaptation payload.

Purpose:

```text
show the LLM what the learner struggled with
encourage future questions around weak areas
improve continuity across sessions
```

This supports the assessment requirement:

```text
Incorporate historical context from prior sessions into prompts to improve question relevance and continuity.
```

---

## 11. Prompt-Level Adaptation

The MCQ prompt includes compact adaptation context.

The prompt receives:

```text
selected section numbers
retrieved chunks
questions per section
mode
weak topics
mastered question texts
previous wrong question texts
adaptation summary
```

The prompt does not receive the full raw database history.

Instead, it receives a compact adaptation payload so generation remains controlled and token-efficient.

Main file:

```text
app/llm/prompts.py
```

---

## 12. Backend-Owned Adaptation Reason

The final `adaptation_reason` is not trusted from the LLM.

The backend overwrites or normalizes the final adaptation reason using actual adaptation state.

Main file:

```text
app/llm/mcq_generator.py
```

This is important because LLMs may incorrectly write adaptive-sounding reasons even during cold-start runs.

The backend prevents that.

### Cold-start reason

```text
Cold-start coverage question generated from the selected section because no prior relevant learning history exists.
```

### Returning run without section-specific weakness

```text
Returning-run question generated using previous session history without a section-specific weak topic.
```

### Adaptive weak-section reason

```text
Adaptive question generated for section 8 because prior session history marks this section as weak.
```

This makes the output explainable and reviewer-verifiable.

---

## 13. Scenario B Adaptation Proof

Scenario B is the main evaluation proof.

It runs three consecutive iterations.

### Iteration 1

Selected sections:

```text
[5, 8]
```

Expected behavior:

```text
mode = cold_start
score = 50.0
```

Reason:

```text
No prior relevant history exists.
The run creates baseline history.
Section 8 is intentionally simulated as weak.
```

With `5` questions per section:

```text
section 5 = 5 questions
section 8 = 5 questions
total     = 10 questions
correct   = 5
wrong     = 5
score     = 50.0
```

Expected adaptation reason:

```text
Cold-start coverage question generated from the selected section because no prior relevant learning history exists.
```

---

### Iteration 2

Selected sections:

```text
[6, 8, 9]
```

Expected behavior:

```text
mode = adaptive
score = 66.67
```

Reason:

```text
Section 8 appeared in iteration 1.
Section 8 has prior wrong answers.
The system detects section 8 as weak.
Sections 6 and 9 are selected but not section-specific weak topics.
```

With `5` questions per section:

```text
section 6 = 5 questions
section 8 = 5 questions
section 9 = 5 questions
total     = 15 questions
correct   = 10
wrong     = 5
score     = 66.67
```

Expected adaptation reasons:

```text
Section 6:
Returning-run question generated using previous session history without a section-specific weak topic.

Section 8:
Adaptive question generated for section 8 because prior session history marks this section as weak.

Section 9:
Returning-run question generated using previous session history without a section-specific weak topic.
```

---

### Iteration 3

Selected sections:

```text
[8]
```

Expected behavior:

```text
mode = adaptive
score = 0.0
```

Reason:

```text
Only section 8 is selected.
Section 8 is already known as weak from previous iterations.
All simulated answers for section 8 are wrong.
```

With `5` questions per section:

```text
section 8 = 5 questions
total     = 5 questions
correct   = 0
wrong     = 5
score     = 0.0
```

Expected adaptation reason:

```text
Adaptive question generated for section 8 because prior session history marks this section as weak.
```

---

## 14. Simulation Strategy

The assessment allows simulated answers.

This project uses simulation in CLI evaluation scenarios to prove the adaptive flow without requiring a human tester.

Simulation is designed to create a realistic mix of correct and incorrect answers.

Scenario B intentionally keeps section 8 weak so the adaptive behavior is visible.

The simulation pattern creates:

```text
Iteration 1: section 8 weakness begins
Iteration 2: section 8 weakness is detected and reused
Iteration 3: section 8 is selected alone and remains adaptive
```

Main CLI files:

```text
cli/run_scenario_a.py
cli/run_scenario_b.py
cli/run_evaluation.py
```

Workflow files:

```text
app/workflow/state.py
app/workflow/nodes.py
app/workflow/prep_graph.py
```

---

## 15. LangGraph Role in Adaptation

The CLI prep flow is orchestrated with LangGraph.

LangGraph is useful because adaptation is a multi-step stateful process.

The graph carries state through:

```text
load document and history
retrieve selected-section chunks
generate MCQs
simulate and score answers
persist session
```

Workflow nodes:

```text
load_document_and_history
retrieve_selected_section_chunks
generate_questions
simulate_and_score_answers
persist_session
```

The adaptation payload is created early in the graph and then passed into question generation.

This allows later nodes to use the same preparation context consistently.

Main files:

```text
app/workflow/state.py
app/workflow/nodes.py
app/workflow/prep_graph.py
app/services/prep_service.py
```

---

## 16. Interactive API Adaptation

The interactive API uses the same adaptation principle.

### Start session

Endpoint:

```text
POST /prep/start
```

The API:

```text
receives selected sections
checks prior history
generates questions
returns questions without answers
persists the session
```

### Submit answers

Endpoint:

```text
POST /prep/submit
```

The API:

```text
receives submitted answers
scores the session
returns correct answers after submission
returns clarification for wrong answers
updates weak-topic statistics
```

This means real user answers and simulated CLI answers both contribute to future adaptive behavior.

---

## 17. KB Snapshot Role

KB snapshots show the stored learning state after a session.

They include:

```text
recent sessions
selected sections
scores
questions asked
user answers
correct answers
wrong answers
weak topics
adaptation payloads
adaptation summaries
```

Snapshots are important because they prove that adaptation is grounded in persisted data, not just in temporary memory.

Output files:

```text
outputs/scenario_a/kb_snapshot_scenario_a.json
outputs/scenario_b_iter1/kb_snapshot_iter1.json
outputs/scenario_b_iter2/kb_snapshot_iter2.json
outputs/scenario_b_iter3/kb_snapshot_iter3.json
```

API endpoint:

```text
GET /kb/snapshot
```

---

## 18. Why Adaptation Is Not Fully Delegated to the LLM

The LLM is useful for generating question content, but it is not reliable enough to own learning-state metadata.

Therefore:

```text
LLM generates:
  question text
  options
  correct answer
  explanation
  topic suggestions

Backend owns:
  question ID
  final adaptation_reason
  mode
  weak-topic tracking
  session persistence
  scoring
  KB snapshots
```

This separation avoids false adaptation claims and makes the output easier to audit.

---

## 19. Handling LLM Non-Determinism

LLM output may vary between runs.

This is expected.

The backend handles non-determinism through:

```text
strict MCQ validation
section-by-section generation
retry logic
question distribution enforcement
backend-owned adaptation metadata
Pydantic schema validation
```

The exact MCQ wording may change, but the required structure must remain valid.

What matters for the assessment:

```text
4 answer choices
one correct answer
one explanation
valid section number
correct question count
stored results
adaptive behavior in later iterations
```

---

## 20. Reviewer Evidence

Reviewers can verify adaptation through:

```text
CLI output
questions JSON files
KB snapshot JSON files
GET /sessions/{session_id}
GET /kb/snapshot
adaptation_reason fields
weak_topic_stats records
```

Most important files:

```text
outputs/scenario_b_iter1/questions_iter1.json
outputs/scenario_b_iter1/kb_snapshot_iter1.json
outputs/scenario_b_iter2/questions_iter2.json
outputs/scenario_b_iter2/kb_snapshot_iter2.json
outputs/scenario_b_iter3/questions_iter3.json
outputs/scenario_b_iter3/kb_snapshot_iter3.json
```

Most important expected result:

```text
Iteration 1: cold_start
Iteration 2: adaptive
Iteration 3: adaptive
```

---

## 21. Current Verified Scenario B Result

Latest verified final-scale behavior:

```text
Scenario B iteration 1 complete | mode=cold_start | score=50.0
Scenario B iteration 2 complete | mode=adaptive   | score=66.67
Scenario B iteration 3 complete | mode=adaptive   | score=0.0
```

Latest verified final-scale question counts:

```text
Scenario B iteration 1: 10 questions
Scenario B iteration 2: 15 questions
Scenario B iteration 3: 5 questions
```

This uses:

```text
5 questions per selected section
```

---

## 22. Known Limitations

### LLM variation

The exact generated MCQs can differ between runs because LLM output is non-deterministic.

The backend validates structure and retries generation, but very poor responses can still fail.

### Simulated answers

Scenario A and Scenario B use simulated answers.

This is allowed by the assessment.

Real answer collection is supported through the FastAPI `/prep/start` and `/prep/submit` endpoints.

### Existing database history affects mode

If old sessions remain in the database, a new `/prep/start` request may return `adaptive`.

This is expected.

To test a clean cold-start flow, reset the database first.

### Topic labels depend partly on LLM output

The topic field is generated from MCQ content and may vary between runs.

The weak-topic mechanism still works because wrong answers are stored and aggregated by section and topic.

---

## 23. Summary

The adaptation strategy is based on persisted learning history.

The system uses PostgreSQL to store sessions, answers, scores, weak topics, and snapshots.

It uses Qdrant only for selected-section semantic retrieval.

It uses the LLM to generate MCQ content, but the backend owns the final adaptation metadata.

Scenario B proves the adaptive behavior:

```text
Iteration 1 creates section 8 weakness.
Iteration 2 detects and uses section 8 weakness.
Iteration 3 focuses only on section 8 and remains adaptive.
```

This satisfies the core assessment requirement that later iterations genuinely use previous session history to shape future preparation.