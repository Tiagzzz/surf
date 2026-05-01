# Phase 1: Ingestion Spine + Database - Context

**Gathered:** 2026-05-01
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers a **headless** end-to-end ingestion pipeline: a lecture PDF goes in, fully-populated SQLite rows come out — pages, learning objectives, eagerly-generated MCQs (with placeholder difficulty fields), all queryable via wrapper functions. **No user interface in this phase** — verification is via `pytest -q` smoke test exercising one ingestion of a sample lecture PDF into a fresh SQLite file. UI surfaces (P3 Class page, P4 Take Mock, etc.) are Phase 2 work and depend on this spine being solid.

In scope:
- `pdf_to_md_v3.py` updated to emit `--- PAGE N ---` markers
- `app/brain/ingestion/page_splitter/` — splits lecture markdown into per-slide chunks + max-10-slide batches
- `app/class_/lo_extract/` — Claude call producing `[{title, page_range}]` LOs from (lecture-md + factsheet-subset)
- `app/class_/mcq_generate/` — Claude call producing 1-3 MCQs per slide for batches of ≤10 slides
- `app/class_/lecture_ingest/` — orchestrator chaining the above + writing to DB
- `app/db/schema/schema.sql` — full DDL with NOT NULL, FK, indexes
- `app/db/connection.py` — central `connect()` + module-level `DB`
- `app/db/queries_<table>/__init__.py` — verb-named wrapper functions for every read/write
- Sample lecture PDF in `assets/sample_factsheets/` (or new `assets/sample_lectures/`) for the smoke test
- Smoke test exercising the full ingestion path

Out of scope (other phases):
- All Streamlit page wiring (Phase 2/3)
- "Resume ingestion" UI button (Phase 2)
- ML model training + final 3 difficulty features (Phase 4)
- Sample factsheet PDF + grader-runnable docs (Phase 5)

</domain>

<decisions>
## Implementation Decisions

### LO Extractor design

- **D-1.1 (Structural skip categories — LOCKED 2026-05-01):** A slide is skipped if it matches ANY of these 9 structural categories:
  1. **title** — course/lecture title slide (course title, lecturer name, date — nothing else).
  2. **agenda** — table of contents, "What we'll cover today", outline of upcoming sections.
  3. **section_divider** — single big heading marking transition between parts (e.g. "Part 2: Strategy"), no real content.
  4. **closing** — "Thank you", "Q&A?", "Any questions?", end-of-deck filler.
  5. **references_only** — bibliography / reference list with no concept content.
  6. **image_only** — pure decoration, photo, or illustrative diagram with no labels/text that would teach a concept.
  7. **blank** — empty or near-empty slide (whitespace, transition placeholder).
  8. **institutional** — university logo, copyright notice, affiliations, institutional branding/disclaimer/policy.
  9. **speaker_bio** — "About me" / lecturer credentials / speaker introduction.
- **D-1.1b (Semantic skip rule — LOCKED 2026-05-01):** Independent of structure: a slide is also skipped if its content is not relevant to ANY topic in the class's factsheet (`core_course_content.main_topics`, `important_concepts_models_methods`, or `FSLO`). This catches off-topic guest-speaker slides, tangents, and anecdotes inside otherwise on-topic decks.
- **D-1.2 (Inputs):** The LO-extractor takes `(lecture_md, factsheet_subset)` where `factsheet_subset` is a curated subset of the factsheet JSON — NOT the whole thing. Only these keys pass through:
  - `surf_extraction_notes` (the ~130-word collapsed prose context note)
  - `core_course_content.narrative_summary` (Course Narrative)
  - `FSLO` (Factsheet Learning Objectives)
  - `core_course_content.main_topics`
  - `core_course_content.important_concepts_models_methods`
  - `core_course_content.skills_students_are_expected_to_develop`
  - `assessment_and_grading.exam_relevant_content`
  Explicitly excluded: `course_snapshot` (admin), `assessment_and_grading.assessment_components` (logistics), `prerequisites_and_assumed_knowledge`, `source_gaps`, and the deprecated `slide_processing_context` (which used to duplicate other fields).
- **D-1.3 (Output):** Each LO is `{title: str, page_range: [start: int, end: int]}`. No summary. No key-terms.
- **D-1.4 (Cap):** Maximum LOs per lecture = `total_pages / 5`, aim for less. (30-page lecture → max 6 LOs, target 4-5.)
- **D-1.5 (Coverage):** Every non-skipped slide MUST belong to exactly one LO's `page_range`. No orphans. The prompt enforces this constraint; LO `page_range`s partition the kept slides.

### MCQ Generator strategy

- **D-2.1 (Count):** Claude generates 1-3 MCQs per slide; default is 1. Generate 2 or 3 only when the slide has multiple distinct pieces of testable knowledge. Each MCQ on the same slide covers a *different* piece of that knowledge.
- **D-2.2 (Variant rule):** Variety is by *what's tested* (sub-topic coverage), NOT by cognitive level (not Bloom-style recall/application/edge-case rotation). Simpler prompt; Claude's discretion within the "different sub-topic" constraint.
- **D-2.3 (Language):** Match the slide's language (per-slide detection by Claude). HSG lectures often mix German and English; let MCQs follow the source.
- **D-2.4 (MCQ schema):** Each MCQ has:
  ```
  {
    question: str
    options: [str, str, str, str]              # always 4 options
    correct_indices: [int, ...]                # 1 to 4 entries (CRITICAL: list, not single int)
    rationales_per_option: [str, str, str, str]
    source_page: int                           # the slide page this question is rooted in
    language: "en" | "de" | ...                # detected per slide
    difficulty_word_count: int | null          # 3 LOCKED features computable at ingestion
    difficulty_readability: float | null
    difficulty_distractor_similarity: float | null
    # 3 PENDING features (Claude-computed per-MCQ; names locked 2026-05-01
    # per docs/difficulty_criteria_recommendation.md). Integer not float.
    difficulty_conceptual_density: int | null   # 1..15 — concurrent variables / framework constraints
    difficulty_distractor_derivation: int | null # 0..3 — count of distractors derivable via common error path
    difficulty_reasoning_steps: int | null      # 1..10 — ordered solution steps required
    difficulty_score: float | null             # filled by trained model in Phase 4
  }
  ```
- **D-2.5 (Multi-correct support):** A question can have 1 to 4 correct answers. The schema uses `correct_indices` (list) rather than `correct_index` (int). Phase 2 P4 must use checkboxes when `len(correct_indices) >= 2`.
- **D-2.6 (Per-option rationale):** Claude writes a rationale for each of the 4 options (why right or why wrong). Used in Phase 2 P5 review to show the student WHY their wrong pick was wrong.

### DB Schema design

- **D-3.1 (Migration approach):** Single `app/db/schema/schema.sql` with full current DDL. Wipe-and-rerun on schema changes during the 2-week build. No migration scripts. The scaffold-folder `app/db/migrations/` stays empty (delete in cleanup).
- **D-3.2 (Strictness):** Strict mode — `NOT NULL` on every column that should never be empty. Foreign keys enforced via `PRAGMA foreign_keys = 1` set at connection startup. Bad inserts crash with a clear error so bugs surface during build, not during demo.
- **D-3.3 (Indexes):** Every foreign-key column gets an index (`class_id`, `lecture_id`, `slide_page_id`, `attempt_id`). Plus a composite index on `(class_id, lecture_id)` for dashboard rollups.
- **D-3.4 (Wrapper style):** Course idioms inside Surf's scaffold structure.
  - **Course-aligned idioms** (verified against `streamlit_db_demo.py` and `Assignment_07_Solution.ipynb`, both in zip `FCS-BWL-07-Databases-SQL-notebooks.zip` from Module 7):
    - `import sqlite3` + `import pandas as pd`
    - Module-level connection: `DB = sqlite3.connect(DB_FILE)` (where `DB_FILE = Path('~/.surf/user.sqlite').expanduser()`)
    - `with DB:` block for INSERT/UPDATE/DELETE (auto-commit on success, rollback on error)
    - `pd.read_sql(sql, DB, params=(...))` for SELECTs
    - `DB.execute(sql, (...))` inside `with DB:` for writes
    - `?` placeholders for all user/runtime input (NEVER f-string SQL with untrusted values)
    - `DB.execute("PRAGMA foreign_keys = 1")` at connection startup
  - **Surf scaffold structure:**
    - `app/db/connection.py` — module-level `DB`, `connect()` helper, FK pragma
    - `app/db/schema/schema.sql` — full DDL, idempotent (uses `CREATE TABLE IF NOT EXISTS`)
    - `app/db/queries_<table>/__init__.py` — one verb-named function per query (e.g., `get_user_by_username`, `save_class`, `list_lectures_for_class`, `count_attempts_for_class`)
    - Returns: DataFrame for multi-row SELECT (matches course demo); plain dict for single-row SELECT (convert at boundary); `None` on miss; `int` (lastrowid) for INSERT.
- **D-3.5 (DB location):** `~/.surf/user.sqlite` (per locked C-08; expanded via `pathlib.Path.expanduser()`).

### Pipeline shape & atomicity

- **D-4.1 (Page markers):** `pdf_to_md_v3.py` emits `--- PAGE N ---` on its own line between pages (not the current `# Page N` heading). Splitter regex: `^---\s+PAGE\s+(\d+)\s+---\s*$` (multiline, captures page number as int).
- **D-4.2 (Pipeline order):**
  1. PDF → Markdown (existing `pdf_to_md_v3.py`, updated to emit markers)
  2. Splitter chunks the markdown into per-slide records, then groups slides into batches of max 10
  3. LO-extractor runs ONCE on the full lecture markdown (cross-slide context needed)
  4. MCQ-generator runs ONCE per batch (≤10 slides per Claude call)
  5. Lecture-ingest orchestrator writes everything to DB
- **D-4.3 (Batching):** Max 10 slides per MCQ-generator Claude call. A 30-slide lecture = 3 MCQ-generator calls. Reduces blast radius of any single Claude failure.
- **D-4.4 (Retry policy):** 2 attempts max per Claude call (1 original + 1 auto-retry). Applies to both LO-extractor and each MCQ-generator batch. No exponential backoff — just a retry once on any error (rate limit, network, invalid JSON).
- **D-4.5 (Partial-success ingestion):** If a batch fails both attempts, write its slides to DB as `status = 'pending'`, skip to the next batch, and CONTINUE the ingestion. The lecture lands with however many batches succeeded; failed batches are flagged for user-driven retry.
- **D-4.6 (Additive writes):** MCQ generation writes are *additive*, not idempotent. If a slide somehow gets re-processed (manual retry, race), it accumulates more MCQs — that's fine; mock pool just gets richer for that slide. No de-dup logic needed.
- **D-4.7 (LO-extractor failure):** If LO-extraction fails both attempts, the lecture row exists in DB but is flagged `status = 'pending'`. User sees "Retry ingestion" on the lecture card (Phase 2 UI). No MCQ generation runs without LOs.
- **D-4.8 (0-MCQ slide):** If Claude returns valid JSON but the MCQ array is empty (slide has no testable content), reclassify the slide as `ignored` (same effect as hitting the skip rule). Cleaner state machine: every slide is either `ignored` OR has ≥1 MCQ. No 'pending' loop on this case (retrying won't help; Claude consistently judges no content).

### Claude's Discretion

These are NOT decided here — the planner / executor picks the pragmatic defaults:
- Exact prompt text for the LO-extractor and MCQ-generator (the *shape* of inputs/outputs is locked above; the *prose* is implementation).
- Internal helper function names and module structure within each `app/class_/<pipeline>/` folder.
- Which Anthropic model to use for each call (default: whatever `claude_client.py` uses now; can override per-call if needed).
- Whether the page-ignore taxonomy is a Python constant, a sibling `.md` file, or inline in the system prompt — pick whichever keeps the prompt readable.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project planning (always relevant)
- `.planning/PROJECT.md` — locked constraints (C-06 stack, C-07 LLM, C-08 SQLite stdlib, C-21 engineering rules, C-22 doc clarity), success metric, team split.
- `.planning/REQUIREMENTS.md` — Phase 1 requirements: PIPE-01, PIPE-03, PIPE-04, DB-01, MECH-04, GRADE-02.
- `.planning/ROADMAP.md` — Phase 1 success criteria + dependencies.
- `.planning/intel/decisions.md` — recorded decisions D-01 through D-36 from Idea v1 (especially D-01 eager MCQ generation, D-03 page markers, D-06 SQLite stdlib).
- `.planning/intel/constraints.md` — full text of C-01 through C-22.

### Idea v1 architecture + factsheet schema
- `docs/idea_v1.md` — canonical project state (7-page UI, ML approach, data-flow shape).
- `docs/handoff_2026-04-30_gsd_planning/01_idea_v1_state.md` — handoff snapshot of Idea v1 (gitignored, local copy).
- `docs/handoff_2026-04-30_gsd_planning/09_open_tbds.md` — distilled list of open questions (A1–A5 are this phase's TBDs).

### Existing code (already shipped — patterns to follow)
- `app/brain/claude_client/claude_client.py` — single shared Anthropic wrapper. Every Claude call goes through this.
- `app/brain/claude_client/claude_client.md` — sidecar doc (note: this is one of the four "too dense" examples per C-22; new sidecars must be simpler).
- `app/brain/ingestion/pdf_to_md_v3.py` — existing PDF→MD extractor; needs `--- PAGE N ---` marker injection (small change per D-4.1).
- `app/brain/ingestion/pdf_to_md_v3.md` — sidecar doc.
- `app/my_classes/factsheet_clean/factsheet_cleaner.py` — TEMPLATE PATTERN. Every new Claude-call pipeline (LO-extractor, MCQ-generator) follows this 10-line wrapper shape.
- `app/my_classes/factsheet_clean/factsheet_cleaner_system_prompt.md` — sibling system-prompt doc; defines the canonical factsheet JSON schema (the keys listed in D-1.2 come from here).
- `app/my_classes/factsheet_clean/factsheet_renderer.py` — pure-Python JSON-to-Markdown renderer.

### Course-aligned DB pattern (verified, locked)
- `/private/tmp/course_db_files/streamlit_db_demo.py` — extracted from Module 7 zip; the canonical `sqlite3 + pandas.read_sql + with DB:` pattern.
- `/private/tmp/course_db_files/Unit07.section3.ipynb` — section 3 of the SQL-in-Python lecture.
- `/private/tmp/course_db_files/Unit07.section4.ipynb` — Chinook continued.
- `/private/tmp/course_db_files/chinook.db` — Chinook sample DB used in lecture demos.
- `/private/tmp/Assignment_07_Solution.ipynb` — official Assignment 07 solution; canonical query patterns + `with DB: DB.execute("PRAGMA foreign_keys = 1")` startup.
- (Note: these are downloaded to `/tmp` for reference only — NOT committed to the repo. Re-download via Canvas MCP if needed; course ID 26148, module ID 142885.)

### Streamlit + Anthropic SDK docs (for the planner if it needs deeper API references)
- Anthropic Python SDK docs (the `claude_client` already wraps this).
- Streamlit docs are NOT relevant for Phase 1 (no UI work).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`app/brain/claude_client/claude_client.py`** — `call_claude(system_prompt, user_message, expect_json=False)`. Used as-is for both LO-extractor and MCQ-generator. Prompt caching is enabled by default; the system prompt becomes the cache key, so we benefit from reusing identical system prompts across MCQ-generator batches within the same lecture ingestion.
- **`app/my_classes/factsheet_clean/factsheet_cleaner.py`** — exact 10-line wrapper template:
  ```python
  from pathlib import Path
  from app.brain.claude_client import call_claude

  _SYSTEM_PROMPT = Path(__file__).with_name("<script>_system_prompt.md")

  def <verb>_<noun>(input_text: str) -> dict:
      return call_claude(
          system_prompt=_SYSTEM_PROMPT.read_text(),
          user_message=input_text,
          expect_json=True,
      )
  ```
  Both `lo_extract/lo_extractor.py` and `mcq_generate/mcq_generator.py` follow this exact pattern. System prompts live as sibling `.md` files.
- **`app/brain/ingestion/pdf_to_md_v3.py`** — existing PDF→MD already shipped; only needs the marker-injection change per D-4.1 (~10 lines per the TBD doc).

### Established Patterns

- **One sub-folder per pipeline** (C-01, C-02): each Claude call lives in its own folder under the right bucket. `lo_extract/` and `mcq_generate/` go under `app/class_/`. `page_splitter/` goes under `app/brain/ingestion/`. `lecture_ingest/` (orchestrator) under `app/class_/`.
- **System prompt as sibling .md** (C-05): keeps prompts editable without touching Python. New: `lo_extractor_system_prompt.md`, `mcq_generator_system_prompt.md`.
- **JSON-only Claude returns** (C-05): `expect_json=True` on every call.
- **Sidecar .md for every script** (C-22): each new Python module ships with a sibling `<script>.md` ≤100 lines, deliberately simpler than the existing 4 sidecars (claude_client.md, pdf_to_md_v3.md, factsheet_cleaner.md, factsheet_renderer.md). Plain-language summary → how to call → in/out → where it fits → gotchas-if-real.

### Integration Points

- `lecture_ingest/lecture_ingest.py` (orchestrator) imports from: `pdf_to_md_v3`, `page_splitter`, `lo_extract`, `mcq_generate`, and `db.queries_lectures + db.queries_pages + db.queries_questions`.
- DB connection lives in `app/db/connection.py`; every queries module imports `DB` from there. Connection is module-level (matches course pattern).
- The factsheet that feeds into the LO-extractor (D-1.2) is fetched via `app/db/queries_classes.get_class_by_id(class_id) -> dict` — the cleaned factsheet JSON is stored on the `classes` row by the existing factsheet_clean pipeline (which is already shipped).

</code_context>

<specifics>
## Specific Ideas

- The user explicitly named the factsheet keys to pass to LO-extractor (D-1.2). Do not pass the whole factsheet JSON — only the 7 listed keys.
- The user explicitly said MCQs can have 1-4 correct answers (D-2.5). The schema must support this from day one — fixing it later means rewriting the answer-checking logic in Phase 2.
- The user explicitly said additive MCQ writes (D-4.6) — don't waste planning effort on idempotency / dedupe.
- The DB pattern is locked against the actual course file `streamlit_db_demo.py`. The pattern is verifiable and citable to slides 24–26 of the Databases lecture (Module 7), which directly addresses GRADE-02 ("Uses data via API and/or DB" — graded 0–3).

</specifics>

<deferred>
## Deferred Ideas

### Phase 2 (Mock Taking Loop)
- **Checkbox UI in P4 Take Mock when `len(correct_indices) >= 2`** — the question render must detect multi-correct and switch from radio buttons to checkboxes.
- **Partial-credit scoring policy for multi-correct questions** — does selecting 2 of 3 correct answers earn 2/3, or 0? UX call. (Suggest: all-or-nothing for v1, simpler grading.)
- **"Resume ingestion" button on P3 Class** — re-runs only the batches with `status = 'pending'`. Phase 2 UI work; the data layer is already supportive (D-4.5).

### Phase 4 (ML Difficulty Model)
- **Lock the 3 candidate difficulty features** (`difficulty_topic`, `difficulty_concept_overlap`, `difficulty_skip_confidence`) once dataset is acquired. May prune to 3 total if dataset doesn't support all 6 — fallback documented in roadmap parallel-tracks note.
- **Backfill `difficulty_score` for all existing question rows** once the model is trained (Phase 4 deliverable).

### Phase 5 (Submission Package)
- **Sample lecture PDF** to commit alongside sample factsheet — needed by smoke test in this phase, polished/cleaned for graders in Phase 5.

### Cleanup / housekeeping
- **Delete unused `app/db/migrations/` scaffold folder** — not used (D-3.1 = single `schema.sql`).
- **Source the existing 4 sidecar docs into the C-22 audit** — once new sidecars exist (under 100 lines), consider rewriting the four "too dense" originals to match. Out of scope for Phase 1.

### Reviewed Todos (not folded)
None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-ingestion-spine-database*
*Context gathered: 2026-05-01 via /gsd-discuss-phase*
