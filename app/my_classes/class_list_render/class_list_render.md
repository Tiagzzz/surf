# `class_list_render` — P2 My Classes page renderer

This module owns the visual P2 page: the shared topbar, the page title and
helper paragraph, the inline `ADD CLASS` form, the Surf class cards
(italic Fraunces class name and color-coded last-4-mock average), the
open-class action, and the confirmation-gated delete
dialog. Production callers go through `render_my_classes_page` from the
package boundary; tests and previews drive the same renderer with injected
fakes.

## How to call it

```python
from app.my_classes.class_list_render import render_my_classes_page

render_my_classes_page(user={"id": user_id, "username": display_name})
```

`render_my_classes_page` accepts injectable hooks for the topbar, the
class/stat queries, the create-class submit service, the delete-after-
confirm service, the navigation function, and the layout renderer. Defaults
match production wiring; the preview sandbox passes fakes.

## Pure helpers (testable without Streamlit)

- `build_class_card_view_models(classes, stats_by_class_id)` — turns class
  rows + stats dicts into the locked card view-models. Numeric stats come
  from the second argument; missing entries fall through to honest "—"
  placeholders, never hardcoded demo data.
- `submit_add_class_form(user_id, class_name, grade4_threshold_percent,
  factsheet_file, *, create_fn)` — blocks with `missing_factsheet` when no
  PDF was uploaded; otherwise delegates to
  `app.my_classes.class_create.create_class_from_factsheet` and returns its
  status dict verbatim.
- `handle_open_class(class_id, state, switch_page_fn)` — sets
  `state["selected_class_id"]` and calls
  `switch_page_fn("views/class_view.py")`.
- `_default_list_class_stats(user_id)` — production stats provider. Walks
  the user's classes and assembles per-class stats by calling existing
  query helpers (no SQL in this module, no pandas). Used as the default
  for the renderer's `list_class_stats_fn` injection point.

## Inputs / outputs

`render_my_classes_page` takes a `user` mapping with at least an `id` and
returns nothing — it draws the page through Streamlit. All visible copy
comes from the locked module constants below.

`build_class_card_view_models` returns a list of dicts:

```text
{
  "class_id": int,
  "class_name": str,
  "avg_score_value": "3.25" | "—",
  "avg_score_tier": "fail" | "borderline" | "pass" | "empty",
  "avg_score_label": "Last 4 Mock Avg" | "Last 4 Mock Avg (N of 4)",
  "left_stats": ["{N} lectures", "{N} Questions"],
  "right_stats": ["{N}% Covered" | "— Covered",
                   "{X.XX} last grade" | "— last grade"],
}
```

## Locked content

`PAGE_TITLE = "My Classes"`, `HELPER_PARAGRAPH = "Each class holds your
lectures, generated questions, mocks, and stats."`, `ADD_CLASS_LABEL`,
`CLASS_NAME_LABEL`, `GRADE_THRESHOLD_LABEL`, `GRADE_THRESHOLD_HELPER`,
`FACTSHEET_LABEL`, `FACTSHEET_HELPER`, `DISCARD_DRAFT_LABEL`,
`CREATE_CLASS_LABEL`, `OPEN_CLASS_LABEL` (kept as a compatibility
constant with value `"OPEN CLASS"`), `ENTER_CLASS_LABEL` (the rendered
card button label, value `"ENTER CLASS >"` with the trailing `>` glyph),
`EMPTY_STATE_COPY`, `PROCESSING_TOAST`, `PROCESS_FAIL_TITLE`,
`PROCESS_FAIL_BODY`, `SAVE_SUCCESS_TOAST`,
`MISSING_FACTSHEET_ERROR`, `MISSING_API_KEY_ERROR`. Threshold slider
is locked to `(min=20, max=80, default=50, step=1)`.

The card-level delete trigger is sourced from the
`app.my_classes.class_delete` module; `DELETE_TRIGGER_LABEL` flipped
from the Mono/Meta text-link `"Delete"` to the matching
`"DELETE CLASS"` so card and destructive dialog primary share the
same word.

Session keys owned by this page: `p2_add_class_open`, `p2_add_class_status`,
`p2_delete_class_id`, `selected_class_id`. Routing target on open:
`views/class_view.py`.

## Surf class-card pattern

The class-card layout uses three visible rules:

1. The four stat strings are arranged in two stacked mini-columns (lectures
   + Questions on the left, Covered + last grade on the right) instead of a
   single dot-separated line.
2. The title-row last-4-mock-avg uses tier coloring: Accent/Deep for `< 4.0`
   (fail), Status/Warn gold for `4.0–4.99` (borderline), Status/OK green for
   `≥ 5.0` (pass), and Paper3 gray for empty. The class name keeps
   the normal dark text color.
3. The action row renders two full-width stamped buttons: neutral
   `DELETE CLASS` on the left opens the destructive dialog, and primary
   `ENTER CLASS >` on the right sets `selected_class_id` and routes to
   `views/class_view.py`. The locked `OPEN_CLASS_LABEL` constant is
   preserved for tests and any future copy registry consumer, but it is
   not the rendered button label.

The earlier quiet `Delete` text trigger and small arrow/Open treatment are
superseded by the `DELETE CLASS` / `ENTER CLASS >` row. The `Delete this
class?` destructive dialog keeps the same user-facing confirmation copy.

## Code walkthrough

### Imports and exports

```python
from html import escape
from typing import Any, Callable, Iterable, Mapping

import streamlit as st

from app.brain.topbar import render_topbar
from app.db.queries_classes import list_classes_for_user
from app.db.queries_dashboard import (
    get_coverage_summary,
    get_mock_grade_metrics,
)
from app.db.queries_lectures import list_lectures_for_class
from app.my_classes.class_create import create_class_from_factsheet
from app.my_classes.class_delete import (
    DELETE_LABEL,
    DELETE_SUCCESS_TOAST,
    DELETE_TRIGGER_LABEL,
    DIALOG_TITLE,
    KEEP_LABEL,
    delete_class_after_confirmation,
    format_dialog_body,
)
```

The renderer never writes raw SQL or calls Anthropic; the only
side-effect entries are the topbar, the listing/stats query helpers, the
create service, the delete-after-confirm service, and `st.switch_page`.
The stats query helpers are imported only so `_default_list_class_stats`
can compose them into a per-class dict — every other entry is swappable
from the public render entry point.

### Pure formatters

`_format_grade_value`, `_grade_tier`, `_format_avg_score_label`,
`_format_coverage`, and `_format_last_grade` are independently testable
helpers that turn raw numbers into the locked card strings. Tier returns
one of `fail`, `borderline`, `pass`, or `empty`; the renderer maps each to
a CSS class on the avg-score span.

### `build_class_card_view_models`

Walks the input class iterable and returns view-models in the same order.
Defensive: if `classes` is not a `list`/`tuple`, raises `TypeError`; if a
class row is missing `id`, raises `KeyError` (these guards are tested in
`tests/test_class_list_render.py`).

### `submit_add_class_form`

Blocks with `{"ok": False, "error": "missing_factsheet"}` when the page
submitted without a PDF. Otherwise calls the injected
`create_fn(user_id=..., class_name=..., grade4_threshold_percent=...,
factsheet_file_or_bytes=...)` and returns its status dict unchanged. The
class-name is forwarded as-is so the create-service's own trim/validate
contract stays the single source of normalization.

### `handle_open_class`

`state[SELECTED_CLASS_KEY] = class_id; switch_page_fn(CLASS_VIEW_PATH)`.
Tested with a plain dict so the contract is independent of Streamlit
session state semantics.

### `render_my_classes_page`

Composes topbar → class list query → stats query →
`build_class_card_view_models` → layout renderer. The default layout
renderer (`_default_layout_renderer`) draws the page via Streamlit:

- page title + helper paragraph,
- `ADD CLASS` toggle button (writes
  `st.session_state["p2_add_class_open"]`),
- inline form `_render_add_class_form` (text input, locked threshold
  slider, file uploader, `DISCARD CLASS DRAFT` + `CREATE CLASS`),
- empty state card or one `_render_class_card` per view-model,
- destructive dialog `_render_delete_dialog` shown when
  `st.session_state["p2_delete_class_id"]` is set.

The renderer never inserts class rows directly — it always goes through
`submit_add_class_form` → `create_class_from_factsheet`, which is the only
path that touches the saved Anthropic key.

### `_default_list_class_stats`

Production stats provider for the P2 cards. Walks every class owned by
`user_id` and returns a `dict[int, dict[str, Any]]` keyed by class id with
the six fields `build_class_card_view_models` consumes. No SQL lives in
this module: each numeric stat is sourced from an existing query helper.
Pandas is intentionally not imported.

Per-field wiring:

| Field | Helper | Notes |
|---|---|---|
| `lectures_count` | `app.db.queries_lectures.list_lectures_for_class(class_id)` | `len(...)` of the returned list. |
| `questions_count` | `app.db.queries_dashboard.get_coverage_summary(class_id)["total_questions"]` | Aggregates across the class's lectures. |
| `coverage_pct` | `get_coverage_summary(class_id)` | `(correct_at_least_once + attempted_never_correct) / total_questions × 100`, rounded to int. **Mock + practice both count** per the V1 "content covered" lock. `None` when `total_questions == 0` so the renderer prints `— Covered`. |
| `last_grade` | `app.db.queries_dashboard.get_mock_grade_metrics(class_id)["last_grade"]` | Mock-only. `None` when no completed mocks exist. |
| `last_4_mock_avg` | `get_mock_grade_metrics(class_id)["class_average"]` | Mock-only. The helper averages exactly the last 4 completed mocks (or fewer if 1–3 exist). |
| `completed_mock_count` | `get_mock_grade_metrics(class_id)["mock_count"]` | Mock-only — practice attempts do NOT increment this. The renderer uses this to switch between `Last 4 Mock Avg` and `Last 4 Mock Avg (N of 4)` copy. |

The mock-only rule on `last_grade` / `last_4_mock_avg` /
`completed_mock_count` enforces the V1 lock: "class average and last grade
use mock exams only." Coverage is the one exception: it counts any
attempted question — mock or practice — because content covered means
"the user has seen and answered this question at least once."

When the user owns no classes, returns `{}` (the renderer then draws the
empty-state card).

### Inline `@font-face` (`_font_data_uri`, `_font_face_block`, `_styles`)

The module loads its own copies of Fraunces (regular / medium / semibold-
italic) and JetBrains Mono (regular / medium) by reading the `assets/fonts/*.woff2`
binaries, base64-encoding them, and emitting a block of `@font-face` rules
at the top of `_styles()` via plain string concatenation. Streamlit does
not preserve a custom-font registration across `st.switch_page` boundaries,
so a user who lands on P2 directly (or navigates from P7) would otherwise
see the theme's serif fallback. The same pattern is used by
`app/signup/signup_flow/__init__.py` and the P1 / P7 preview sandboxes.

`_styles()` is a regular triple-quoted string so the surrounding CSS
doesn't have to escape every `{` / `}`; `_font_face_block()` is appended
via `"<style>\n" + _font_face_block() + """ ... </style> """`.

### Destructive-dialog state machine (`_render_delete_dialog`)

The card-level `DELETE CLASS` button writes the class id into
`st.session_state[DELETE_PENDING_KEY]` (`p2_delete_class_id`) and reruns.
The renderer reads the pending id with **`pop`, not `get`** — the moment
we hand the id to `_render_delete_dialog`, the session-state slot is
cleared. Streamlit's `@st.dialog` keeps the modal alive on its own until
the user confirms, cancels, or dismisses with the X. Without the pop, an
unrelated rerun (e.g. clicking ADD CLASS) would re-open the modal because
the session-state flag would still be set. Inside the dialog the KEEP /
DELETE handlers also pop defensively as a no-op safeguard.

## Constraints

- **Streamlit-only chrome.** No raw HTML widgets that aren't Streamlit
  primitives plus scoped `st.html`. The button stamp/animation and the
  card hard-stamp follow 03-UI-SPEC §2.5.
- **No app-bypass paths.** The renderer does not import sqlite directly,
  does not read `ANTHROPIC_API_KEY`, and does not display the saved key.
- **Honest empty stats.** When stats are missing, cards render the locked
  `—` strings — never `0` for unknown coverage or fake grades.
- **Confirmation gate.** Delete only fires through
  `delete_class_after_confirmation(..., confirmed=True)` from the
  destructive dialog button. The card-level `DELETE CLASS` button only
  opens the dialog by setting `st.session_state["p2_delete_class_id"]`.
- **Open routes only.** `ENTER CLASS >` writes `selected_class_id` and
  switches to `views/class_view.py`. The destination page owns the class-hub details.

## Verification commands

```bash
pytest tests/test_class_list_render.py tests/test_class_delete.py \
       tests/test_no_app_imports_in_previews.py tests/test_no_real_db.py -q
ruff check app/my_classes/class_list_render app/my_classes/class_delete \
            views/my_classes.py
streamlit run previews/pages/p2_my_classes/preview.py
```

## Shared page-header and rail integration

The P2 title area uses the shared `app.brain.page_header.render_page_header(...)` helper, and the default layout is wrapped in `app.brain.page_layout.page_rail("p2_my_classes_page")`.

Locked P2 copy stays unchanged:

- Kicker: `SURFBOARD`
- Title: `My Classes`
- Helper: `Each class holds your lectures, generated questions, mocks, and stats.`

The shared helper only renders escaped HTML and scoped CSS; it does not change class listing, Add Class submission, delete confirmation, routing, or saved-key behavior. The page rail uses the shared 880px authenticated-page ruler and keeps top padding delegated to the shared topbar.

### Code walkthrough addendum

`_default_layout_renderer` still injects P2 styles first. It now opens `page_rail("p2_my_classes_page")` instead of a raw Streamlit container, then calls `render_page_header(...)` with the locked P2 copy before rendering the `ADD CLASS` button, optional form, empty state, class cards, and delete dialog. The old page-specific title/helper CSS remains harmless compatibility styling, but the actual P2 header markup now comes from the shared helper.

## Add Class rail/dropbox polish

The Add Class visual surface keeps the P2 data flow unchanged:

- `ADD CLASS` now uses `use_container_width=True` and CSS `width: 100%` so it spans the same shared 880px page rail as the class cards.
- `_render_add_class_form` uses one keyed dashed container, `p2_add_class_form_card`, directly around the form. The previous nested `st.container(border=True)` wrapper was removed so the form no longer draws an inner non-dashed card line.
- The factsheet upload is wrapped in `p2_factsheet_dropbox`. It still uses the real `st.file_uploader` with key `p2_add_class_factsheet`, but the native Streamlit dropzone is now the full dashed Dropbox visual surface. The decorative overlay shows a file icon, `DROPBOX`, `UPLOAD YOUR FACTSHEET`, and a selected-file `READY: <filename>` line after Streamlit has a file.
- Streamlit's native browse/upload button stays mounted for click/tap users but is stretched invisibly over the full dashed zone. That makes the real uploader and the visible Dropbox surface the same size, removes the small stamped button overlap, and avoids the thin non-dashed line inside the dashed upload area.

### Streamlit uploader constraint

Streamlit does not expose a first-class API for fully replacing the file-uploader internals. The implementation therefore keeps the native uploader mounted and scopes CSS under `.st-key-p2_factsheet_dropbox`. The key implementation detail is that the native dropzone draws the dashed border and Paper0 fill, while a decorative overlay provides the Surf file icon and copy. The transparent native button remains above the dropzone but below the decorative overlay, preserving upload state, validation, and the existing class-creation submit path.

## Scoped button-font note

The visible P2 button labels stay in JetBrains Mono through a narrow button-font selector. The font rule now targets only `.st-key-p2_my_classes_page` buttons, their inner Streamlit label wrappers, and the two P2 delete-dialog keys (`p2_delete_keep` and `p2_delete_confirm`), because Streamlit renders the dialog outside the page rail.

This is a CSS scope correction only. `ADD CLASS`, Add Class form submit/discard, class-card `DELETE CLASS` / `ENTER CLASS >`, and the class-delete dialog keep the same labels, keys, disabled/hover/active styling, and behavior. Non-button copy such as class names, helper text, and uploader/dropbox text keeps its existing typography; the extra inner-label selectors are only there because Streamlit often nests visible button text inside child `<p>`/`span` elements.
