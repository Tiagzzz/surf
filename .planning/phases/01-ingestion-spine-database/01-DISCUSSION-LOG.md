# Phase 1: Ingestion Spine + Database - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 01-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-01
**Phase:** 01-ingestion-spine-database
**Areas discussed:** LO extractor design · MCQ generator strategy · DB schema specifics · Pipeline shape & atomicity

---

## Area 1 — LO extractor design

### Q1.1 Skip rule

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed checklist | Hand Claude a fixed list of skip-types (title, ToC, "Thank you", references, blank, image-only, institutional) | |
| Let Claude judge | Tell Claude "skip slides that don't teach a concept the student needs to know" | |
| Hybrid | Fixed list + Claude judges borderline cases | ✓ (effectively) |

**User's choice:** Free-text — *"If the slide is about agenda, if it's just an image, if it's just about sources, if it's a title page, if it's actually blank, if it has nothing to do with the important class knowledge mentioned in the factsheet."*
**Notes:** Last item is a hybrid rule — Claude must check slide content against the class factsheet. Triggered the factsheet-as-input follow-up.

### Q1.2 Factsheet as LO-extractor input

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — full factsheet JSON | Whole factsheet as input | |
| No — factsheet not needed | Lecture markdown only | |
| Curated subset | A specific subset of factsheet keys passes through | ✓ (custom) |

**User's choice:** Free-text — specified exactly 7 keys to pass: `surf_extraction_notes`, `core_course_content.narrative_summary`, `FSLO`, `core_course_content.main_topics`, `core_course_content.important_concepts_models_methods`, `core_course_content.skills_students_are_expected_to_develop`, `assessment_and_grading.exam_relevant_content`. Explicitly excluded: course_snapshot, assessment_components, prerequisites, source_gaps, deprecated slide_processing_context.
**Notes:** User cited `docs/idea_v1.md`, `app/my_classes/factsheet_clean/factsheet_cleaner_system_prompt.md`, and the handoff snapshot of Idea v1 as canonical sources. Added to canonical_refs in CONTEXT.md.

### Q1.3 Institutional / disclaimer slides

| Option | Description | Selected |
|--------|-------------|----------|
| Skip them too | Add to skip list | ✓ |
| Keep them | Let Claude judge if any teach a concept | |
| Skip if Claude is confident, otherwise keep | Treat as borderline | |

### Q1.4 LO output shape

| Option | Description | Selected |
|--------|-------------|----------|
| `{title, page_range}` | Minimal | ✓ (with cap) |
| `{title, page_range, summary}` | + 1-2 sentence summary | |
| `{title, page_range, summary, key_terms}` | Full | |

**User's choice:** Minimal, plus a cap: max LOs per lecture = `total_pages / 5`, aim for less.
**Notes:** Stops Claude from over-producing 1-LO-per-slide chaff. Average ~5 slides per LO with flexibility upward.

### Q1.5 Orphan slides

| Option | Description | Selected |
|--------|-------------|----------|
| Force every on-topic slide into some LO | Page-ranges partition kept slides | ✓ |
| Allow orphans → MCQs anyway in "Misc" LO | | |
| Allow orphans → silently skip | | |
| Allow orphans → flag for review | | |

---

## Area 2 — MCQ generator strategy

### Q2.1 MCQs per slide

| Option | Description | Selected |
|--------|-------------|----------|
| Exactly 1 per slide | Predictable cost | |
| Exactly 3 per slide | More variety | |
| Claude decides 1–3 | Flexible based on slide content | ✓ |
| Exactly 5 per slide (one per cognitive variant) | Most expensive but pre-builds variant mix | |

### Q2.2 Variant rule

| Option | Description | Selected |
|--------|-------------|----------|
| Free-form | Claude decides per slide | |
| Force cognitive variety (recall / application / edge) | Bloom-style rotation | |
| Pre-decide per slide ahead of time | Two-pass approach | |

**User's choice:** Free-text — *"Claude should generate multiple MCQs when a slide contains a lot of knowledge. Each MCQ should cover a different part of the knowledge."*
**Notes:** Variety is by *what's tested* (sub-topic), not by cognitive level. Cleaner than Bloom.

### Q2.3 MCQ schema fields

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal | `{question, options[4], correct_index, rationale, source_page}` | |
| Minimal + per-option rationale | Each of 4 options has its own rationale | ✓ (with additions) |
| Minimal + topic_tag | | |
| Full (all of the above) | | |

**User's choice:** Free-text — *"Minimal + per option rationale + 6 ML difficulty criteria (These need to be locked later, 3 have already been agreed on)"*
**Notes:** Schema gets the 6 difficulty-feature columns provisioned at ingestion time even though only 3 are computable now and the score is null until Phase 4 ML model lands.

### Q2.4 Language

| Option | Description | Selected |
|--------|-------------|----------|
| Match slide language | Per-slide detection | ✓ |
| Always English | | |
| Match dominant lecture language | | |
| Student picks at sign-up | | |

**User's correction during Q2.4:** *"there can be 1 to 4 correct answers to a question."* — caught a critical schema bug. Updated MCQ shape to use `correct_indices: list[int]` instead of `correct_index: int`. Phase 2 P4 deferred decision: use checkboxes when `len >= 2`.

---

## Area 3 — DB schema specifics

### Q3.1 Migration approach

| Option | Description | Selected |
|--------|-------------|----------|
| Single `schema.sql`, wipe-and-rerun | Simplest, fine for 2-week build with no real user data | ✓ |
| Hand-written numbered migration scripts | Preserves data through changes | |
| Alembic | Industry-standard auto-gen migrations | (rejected — out of scope per D-06) |

### Q3.2 Schema strictness

| Option | Description | Selected |
|--------|-------------|----------|
| Strict (NOT NULL on everything required) | DB rejects bad inserts; bugs surface immediately | ✓ |
| Loose (NOT NULL only on PKs) | Code responsible | |
| Mixed by table importance | Strict on core, loose on volume tables | |

### Q3.3 Indexes

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — every FK + (class_id, lecture_id) composite | Standard practice | ✓ |
| Skip indexes for v1 | Add only if slow | |
| Yes + lo_id + completed_at | Most aggressive indexing | |

### Q3.4 Wrapper style

| Option | Description | Selected |
|--------|-------------|----------|
| Verb-named functions, plain dicts | One per query, sqlite3.Row → dict | |
| Repository class per table | OOP/Java-like | |
| Pure inline SQL (no wrappers) | Fastest, painful for 7-page app | |

**User's choice:** Free-text — *"Use the nlm connector to understand how it is thought in class, and use that method. If multiple methods are thought, pick the best for our project from those thought in the lecture"*

**Research escalation:** Queried the Lectures NotebookLM (notebook 6bc919e0) for course-taught SQLite patterns. Result: **Low confidence** — slides reference but don't contain the code; they point to `Unit07.section3.ipynb`, `Unit07.section4.ipynb`, `streamlit_db_demo.py` on Canvas.

**Canvas escalation:** Pulled `FCS-BWL-07-Databases-SQL-notebooks.zip` and `Assignment_07_Solution.ipynb` from Module 7 (course ID 26148, module ID 142885) via Canvas MCP. Extracted to `/private/tmp/course_db_files/`. Read `streamlit_db_demo.py` and Assignment_07_Solution.ipynb code patterns. **Course-canonical pattern locked:** `sqlite3 + pandas.read_sql + with DB:`, FK pragma at startup, `?` placeholders, module-level connection.

### Q3.4-final — Lock decision

| Option | Description | Selected |
|--------|-------------|----------|
| Course idioms inside Surf scaffold | sqlite3+pd.read_sql+with DB: idioms; verb-named functions in queries_<table>/__init__.py; central app/db/connection.py | ✓ |
| Same idioms but return list[dict] not DataFrame | | |
| Pure inline (no wrappers) | | |

---

## Area 4 — Pipeline shape & atomicity

### Q4.1 Page-marker format

| Option | Description | Selected |
|--------|-------------|----------|
| `--- PAGE N ---` on its own line | What's in v1 plan (D-03) | ✓ |
| HTML comment `<!-- PAGE N -->` | Invisible when rendered | |
| JSON sidecar | Most robust, extra file per lecture | |

### Q4.2 Mid-pipeline failure

| Option | Description | Selected |
|--------|-------------|----------|
| Save what worked, flag rest, user retry | Best UX, mid complexity | (combined) |
| Roll back the whole lecture | Simplest code | |
| Auto-retry with backoff (3 tries) | Most resilient | (combined) |
| Both: retry + save partial | | (effectively) |

**User's choice:** Free-text — *"Can we ask claude to only process slides in batches of max 10 slides to avoid such problems? If it fails, it saves what worked, but starts again anyway (first questions would get more MCQs (that's ok) max 2 attempts. Then lets USER retry"*
**Notes:**
- Adds batching as a primary defence (max 10 slides per Claude call)
- Retry policy: 2 attempts max per batch (1 + 1 retry)
- On failure: save successful batches, flag failed batches, continue
- Additive writes accepted (re-running can produce duplicate MCQs on the same slide; mock pool gets richer)

### Q4.3 LO-extractor failure

| Option | Description | Selected |
|--------|-------------|----------|
| Same as MCQ — retry once, then flag whole lecture pending | | ✓ |
| Hard-fail — don't write the lecture row at all | | |

### Q4.4 0-MCQ slide

| Option | Description | Selected |
|--------|-------------|----------|
| Accept as 'covered, no questions' | | |
| Treat as a skip → reclassify ignored | Clean state machine | ✓ |
| Flag as pending for retry | Retrying won't help | |

---

## Claude's Discretion

User explicitly deferred these to the planner / executor:
- Exact prompt text for LO-extractor and MCQ-generator (shape locked, prose open)
- Internal helper function names within `app/class_/<pipeline>/` folders
- Anthropic model selection per call (default to whatever claude_client uses)
- Whether the page-ignore taxonomy is a Python constant, sibling .md, or inline in the system prompt

## Deferred Ideas

(Captured in CONTEXT.md `<deferred>` section.)

- **Phase 2:** checkbox UI for multi-correct MCQs · partial-credit scoring policy · Resume Ingestion button
- **Phase 4:** lock the 3 candidate difficulty features once dataset is acquired · backfill difficulty_score
- **Phase 5:** polished sample lecture PDF for graders
- **Cleanup:** delete `app/db/migrations/` scaffold · rewrite the 4 "too dense" sidecars to C-22 standards once new ones exist

## External research escalations during discussion

1. **NotebookLM Lectures notebook query** (notebook ID `6bc919e0-21c9-452e-b203-507f078efa33`) — asked how the course teaches SQLite patterns. Returned Low confidence (slides reference but don't show code).
2. **Canvas MCP** (course `4,125,1.00` ID 26148, module ID 142885) — downloaded `FCS-BWL-07-Databases-SQL-notebooks.zip` + `Assignment_07_Solution.ipynb` to `/private/tmp/`. Read `streamlit_db_demo.py` and Assignment_07 solution; locked Surf's DB pattern against the course's actual code.
