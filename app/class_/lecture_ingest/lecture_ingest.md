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
