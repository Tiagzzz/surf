# lecture_ingest.md

What this file is: the single entry point that ingests one lecture PDF into Surf's database. It runs the 5-step pipeline end-to-end: PDF → markdown → split into slides → ask Claude for learning objectives → ask Claude for practice questions → write everything to SQLite.

## How to call

```python
from pathlib import Path
from app.class_.lecture_ingest import ingest_lecture

lecture_id = ingest_lecture(class_id=1, pdf_path=Path("lecture.pdf"))
```

Optional kwargs:
- `title` — defaults to the PDF filename (no extension).
- `claude_call_lo`, `claude_call_mcq` — only used by tests to inject deterministic fakes (no real network call).

## In / out

| Function | In | Out |
|----------|----|-----|
| `ingest_lecture(class_id, pdf_path, ...)` | int + Path (file must exist) | `int` lecture_id |

The lecture row's `status` column is the audit signal:
- `'ready'` — full success: every kept slide has MCQs, every ignored slide is flagged.
- `'pending'` — partial failure: either LO-extraction failed twice (no MCQs at all), or at least one MCQ batch failed twice (those slides are 'pending', the rest still have MCQs). Phase 2's UI surfaces a "retry" button for these.

## Where it fits

Phase 1's pipeline lives behind this single call. Phase 2's "Class" page (P3) calls it when a user uploads a PDF. Phase 4's ML model later backfills `difficulty_score` on the questions table; this orchestrator already fills `difficulty_word_count` per MCQ.

## Gotchas-if-real

- If LO extraction fails twice, NO MCQ generation runs (D-4.7). The lecture row exists with `status='pending'` and zero rows in `learning_objectives` / `slide_pages` / `questions`. Caller can retry later.
- If a single MCQ batch fails twice, those slides flip to `status='pending'` (D-4.5) and the rest of the lecture is fine. The lecture row's status stays `'pending'` so the UI can surface a partial-retry.
- When Claude returns `mcqs: []` for a slide, that slide is reclassified `'ignored'` (D-4.8) — it's a Claude-driven skip on top of the structural taxonomy.
- The orchestrator only passes the 7-key factsheet subset to the LO-extractor (D-1.2), not the full factsheet — saves ~40% input tokens per call.

## Code walkthrough

This script is the conductor for the whole Phase-1 pipeline. The single public function `ingest_lecture` runs five steps end-to-end (PDF → markdown → split → LOs → MCQs → DB) and applies the locked policies for retry, partial success, and failure handling. It's the one place where everything wires together. Here's what each piece does, top to bottom.

**Module-level imports + factsheet-key constants** — Pulls in every helper this orchestrator needs: PDF extractor, page splitter, LO extractor, MCQ generator, and the six DB query modules. The three `_FACTSHEET_*_KEYS` tuples list which factsheet fields the LO extractor cares about per D-1.2 (the 7-key subset rule). They live as module constants so the next person editing the policy doesn't have to hunt for the keys inside a function body.

**`_build_factsheet_subset(factsheet)`** — In plain language: takes the full cleaned factsheet dict and returns just the 7 keys the LO extractor actually uses. Missing keys default to `None` so the system prompt always sees a complete shape — Claude doesn't have to handle "key absent" vs "key empty" separately. Watch out for: this is a defensive trim; passing the full factsheet still works but burns ~40% extra input tokens per call.

**`_call_with_retry(fn, *args, **kwargs)`** — In plain language: calls a function up to two times, returning the first success. Per D-4.4: 2 attempts, no backoff. If both fail, raises the last exception. The `noqa: BLE001` comment suppresses a lint warning about the broad `except Exception` because retrying ANY error is the intentional policy. Watch out for: this is the only retry layer in the whole pipeline. The wrappers (`extract_los`, `generate_mcqs`) don't retry themselves.

**`_find_lo_id(page_number, lo_records)`** — In plain language: given a page number and a list of `(lo_id, page_start, page_end)` tuples, returns the `lo_id` of the LO whose range contains that page, or `None` if no LO covers it. Used to bind each kept slide to its LO when writing `slide_pages` rows. The `None` return is the D-1.5 violation signal (a slide that should be kept but no LO claimed it) — the caller flips that slide to `'pending'` so the user can re-run.

**`_validate_mcq(mcq)`** — In plain language: defensive shape-check against the D-2.4/D-2.5/D-2.6 schema. Returns True if `options` is a 4-element list, `rationales_per_option` is a 4-element list, and `correct_indices` is a list of 1-4 integers each between 0 and 3. Returns False (without raising) on missing keys or wrong types so the orchestrator can skip a malformed MCQ and continue with the rest of the batch.

**`ingest_lecture(class_id, pdf_path, *, title, claude_call_lo, claude_call_mcq)`** — The public entry point and the longest function in the file. In plain language, it walks five steps:

1. **PDF → markdown.** Calls `extract_with_tables` from `pdf_to_md_v3`. Computes `total_pages` from the highest page-number marker. If the markdown has no markers, raises `ValueError` immediately — there's nothing to process.
2. **Insert the lecture row.** With `status='pending'` (the D-4.7 default). Looks up the class to grab its factsheet, trims it to the 7-key subset. The lecture row is created BEFORE Claude is called so a mid-pipeline failure still leaves a visible record the user can retry.
3. **LO extraction (one call, with retry).** Wraps the LO-extractor call in `_call_with_retry`. If both attempts fail, logs the exception and returns the lecture id with `status='pending'` and zero LOs / slides / MCQs — D-4.7 policy. If it succeeds, persists each LO row, then walks every slide and writes a `slide_pages` row: ignored pages get `status='ignored'`; kept pages get bound to their LO via `_find_lo_id`; pages that should be kept but have no covering LO flip to `status='pending'` (D-1.5 defensive).
4. **MCQ generation (per batch, with retry, partial-success).** Filters down to the kept slides that found an LO, batches them at size 10 (D-4.3), and loops one Claude call per batch. A batch failure (after both retries) flips every slide in that batch to `'pending'` and sets `any_failure = True` so the lecture status reflects partial-success. A successful batch walks every per-slide MCQ list: an empty list reclassifies the slide as `'ignored'` (D-4.8); each valid MCQ gets inserted via `insert_question` with the locked `difficulty_word_count` filled and the rest of the difficulty fields left NULL for Phase 4. Invalid MCQs are skipped with a warning rather than raising.
5. **Final status flip.** If no batch failed, sets `lecture.status = 'ready'`. If at least one batch failed, leaves it at `'pending'` so the UI can surface a partial-retry button.

Watch out for: the `claude_call_lo` and `claude_call_mcq` kwargs let tests inject deterministic fakes — Phase 1's smoke test uses this to run the full pipeline without a real Anthropic key. In production, both default to the real Claude wrappers. The function returns the lecture_id no matter what so the caller can always look up the row and check `status` to decide what to show the user.
