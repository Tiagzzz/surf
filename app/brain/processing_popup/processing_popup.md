# `processing_popup` — upload waiting popup

This shared helper renders the Surf-branded waiting popup used while uploaded
files are being processed.

## Purpose

P2 Add Class and P3 Add Lecture both run a slow file-processing path after the
user submits a PDF. This helper gives both pages the same two-state overlay:

1. **Processing:** “Your file is being processed” with the looped surfer video
   and the `processing ...` status.
2. **Done:** “Your file is ready” with the same looped video and the `Done!`
   status, shown briefly before the page reruns.

The helper is visual only. It does not change class creation, lecture ingestion,
SQLite writes, Claude calls, or upload validation.

## Connected files

- `assets/media/surfer-processing-loop.mp4` — the autoplaying, muted, looped
  MP4 shown in the popup.
- `app/my_classes/class_list_render/__init__.py` — shows the popup around Add
  Class factsheet processing.
- `app/class_/class_hub/__init__.py` — shows the popup around Add Lecture
  processing.
- `tests/test_processing_popup.py` — checks the two-state copy and video
  autoplay/loop attributes.

## Code walkthrough

### Asset path and cached video data URI

`_VIDEO_PATH` points to the checked-in MP4 under `assets/media/`.
`_video_data_uri()` base64-encodes that file once per process so Streamlit can
render the video inline without needing a separate static-file route. The card
fill uses `rgba(253, 246, 238, 1)` so the popup background matches the supplied
video background.

### `build_processing_popup_html(...)`

This pure helper chooses the visible copy for `processing` or `done`, embeds the
video tag with `autoplay`, `muted`, `loop`, and `playsinline`, and returns one
HTML/CSS block. The CSS draws the fixed backdrop, stamped warm-paper card,
Fraunces italic title, mono subtitle, centered video, and red/green status dot.

### `show_processing_popup(...)`

This small Streamlit adapter writes the generated HTML into a placeholder-like
object, preferring Streamlit Markdown with unsafe HTML enabled because it is
more reliable for mixed style + media blocks. Pages pass `st.empty()` so the
same placeholder can be switched from processing to done, then cleared on
error.

## What could break if changed

- Removing `muted` can stop browser autoplay.
- Removing `loop` makes the surfer animation stop during long ingestion.
- Removing `playsinline` can make mobile browsers try to open the video outside
  the page.
- Pointing at Tiago's personal `/Users/.../CS/` file path would make the app
  fail outside that local folder; keep the project asset copy instead.
- Moving ingestion into this helper would mix visual UI with processing logic
  and make failures harder to test.

## Verification commands

```bash
python -m pytest -q tests/test_processing_popup.py
python -m ruff check app/brain/processing_popup tests/test_processing_popup.py --no-cache
```
