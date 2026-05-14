# `app/my_classes/` bucket — P2 My Classes setup

This bucket owns the P2 My Classes setup area: class creation from a required
factsheet PDF, factsheet cleaning, approved Surf class cards, and
confirmation-gated class delete. The current implementation validates
the setup inputs, extracts factsheet PDF text, cleans it with the saved user's
Anthropic key, inserts only after that processing succeeds, and renders the P2
class list with the shared topbar plus stamped `DELETE CLASS` / `ENTER CLASS >`
card actions.

## What lives in this bucket

| Folder / file | What it does |
|---|---|
| `factsheet_clean/` | Loads the factsheet-cleaner system prompt and calls the shared Claude wrapper. The package exports `clean_factsheet` from `app.my_classes.factsheet_clean`. |
| `class_create/` | Creates a class from class name, grade-4 threshold, and uploaded factsheet PDF. It is responsible for the no-partial-insert rule. |
| `class_list_render/` | Renders the visual P2 page: shared topbar, page header, helper paragraph, inline `ADD CLASS` form, Surf class cards (italic class name, color-tier last-4-mock average, and stamped `DELETE CLASS` / `ENTER CLASS >` row), empty state, and destructive delete dialog. Exports `render_my_classes_page` and `build_class_card_view_models`. |
| `class_delete/` | Confirmation-gated delete service. Wraps `delete_class_for_user` so the destructive call only runs after the user pressed `DELETE CLASS` in the locked dialog. Exports `delete_class_after_confirmation` plus the locked dialog copy. |
| `my_classes.md` | This bucket-level sidecar. |

## How the pieces fit together

```
views/my_classes.py                       ← thin Streamlit wrapper
        │
        ▼
app.my_classes.class_list_render.render_my_classes_page
        ├── app.brain.topbar.render_topbar("my_classes")
        ├── app.db.queries_classes.list_classes_for_user(user_id)
        ├── _default_list_class_stats(user_id)            ← honest "—" placeholders
        ├── build_class_card_view_models(classes, stats)  ← pure
        ├── ADD CLASS toggle → inline form → submit_add_class_form
        │       └── app.my_classes.class_create.create_class_from_factsheet
        │               ├── app.db.queries_users.get_saved_anthropic_api_key(user_id)
        │               ├── temp .pdf file from uploaded bytes/file
        │               ├── app.brain.ingestion.pdf_to_md_v3.extract_with_tables
        │               ├── app.my_classes.factsheet_clean.clean_factsheet(...)
        │               └── app.db.queries_classes.insert_class(...)
        ├── ENTER CLASS > → state["selected_class_id"] = class_id
        │                 → st.switch_page("views/class_view.py")
        └── DELETE CLASS → destructive dialog
                           → app.my_classes.class_delete
                               .delete_class_after_confirmation(
                                   confirmed=True
                               )
                               └── app.db.queries_classes.delete_class_for_user
```

## Constraints

- **Factsheet is required.** P2 class setup must not create an empty class and
  ask the user to fix the factsheet later.
- **Clean before insert.** `insert_class` runs only after PDF extraction and
  Claude factsheet cleaning both succeed.
- **Use the saved user's key.** The service gets the key through
  `get_saved_anthropic_api_key(user_id)` and passes that exact key to
  `clean_factsheet(..., api_key=saved_key)`. It must not render the key, read
  `ANTHROPIC_API_KEY`, or reuse an old key from another user.
- **No live DB/API in tests.** Tests fake extraction, Claude cleaning, saved-key
  lookup, and insertion. Temp files live under pytest temp locations or Python
  temporary directories.
- **Status dicts, not tracebacks.** Invalid uploads, including broken file-like
  objects, return a small invalid-input dict so P2 can show friendly copy.
- **No pandas in this bucket.** Query helpers return plain Python data, and this
  bucket should keep the same style.

## Code walkthrough

This bucket-level doc explains the service flow. The detailed code tours live in
the module sidecars:

- `factsheet_clean/factsheet_cleaner.md` — cleaner prompt loading and saved-key
  `call_claude` routing.
- `class_create/class_create.md` — class-creation validation, temporary PDF
  extraction, cleaner-before-insert order, and renderer-friendly status dicts.
- `class_list_render/class_list_render.md` — visual P2 page composition:
  pure view-model builder, ADD CLASS form, class cards, `ENTER CLASS >`
  route action, `DELETE CLASS` dialog trigger, and the Surf class-card
  pattern (italic name + color tier + stamped two-button row).
- `class_delete/class_delete.md` — confirmation-gated wrapper around the
  ownership-checked DB helper, plus locked dialog copy.

## What could break if changed

- Moving `insert_class` before the cleaner can leave partial classes when Claude
  or PDF extraction fails.
- Letting `clean_factsheet` omit the explicit `api_key` can accidentally use an
  environment key or a stale key rather than the current saved user key.
- Letting `clean_factsheet` accept a blank key can also trigger that fallback;
  the cleaner now rejects blank keys before calling Claude.
- Keeping uploaded files outside a temporary directory can leave factsheet PDFs
  behind after success or failure.
- Hardcoding demo grades or stats inside `class_list_render` would break the
  honesty contract; the renderer must read all stats from the injected stats
  dict and fall back to locked `—` placeholders.
- Wiring the card-level `DELETE CLASS` trigger directly to `delete_class_for_user`
  bypasses the destructive dialog. The renderer must always go through
  `class_delete.delete_class_after_confirmation(..., confirmed=True)` from
  the dialog branch.
- Inserting a class from inside the renderer (instead of the
  `submit_add_class_form` → `create_class_from_factsheet` flow) bypasses
  the no-partial-insert and saved-key contracts.

## Verification commands

```bash
pytest tests/test_class_create.py tests/test_class_list_render.py \
       tests/test_class_delete.py tests/test_no_app_imports_in_previews.py \
       tests/test_no_real_db.py tests/test_no_secrets_committed.py -q
ruff check app/my_classes/class_create app/my_classes/class_list_render \
            app/my_classes/class_delete app/my_classes/factsheet_clean \
            views/my_classes.py tests/test_class_create.py \
            tests/test_class_list_render.py tests/test_class_delete.py
streamlit run previews/pages/p2_my_classes/preview.py
```

## Shared header and rail note

The `class_list_render/` page now uses two shared brain helpers for page chrome:

- `app.brain.page_layout.page_rail("p2_my_classes_page")` centers P2 on the shared 880px authenticated-page rail.
- `app.brain.page_header.render_page_header(...)` renders the locked `SURFBOARD` / `My Classes` / helper-copy header.

This is visual chrome only. Class creation, stats, delete confirmation, and `ENTER CLASS >` routing remain owned by the same P2 modules described above.

## Add Class visual polish

The P2 Add Class visual shell aligns the `ADD CLASS` trigger and expanded form to the shared 880px authenticated page rail from `app.brain.page_layout`. The Add Class draft form has one dashed outer boundary and no inner non-dashed card wrapper. The factsheet uploader remains the real Streamlit uploader but is presented inside a large scoped Dropbox-style zone with empty and selected-file states; its native browse/upload button stays visible and is styled as a Surf stamped control so the form remains clickable.

No class-creation behavior changed: factsheet upload is still required, the grade threshold remains setup-only, class rows are still inserted only after PDF extraction and factsheet cleaning, and delete/open class behavior stays in the existing modules.

## Scoped button-font note

The My Classes button-font CSS is scoped to P2-owned surfaces only: the `p2_my_classes_page` rail and the P2 class-delete dialog keys. This preserves JetBrains Mono button labels for `ADD CLASS`, form buttons, `DELETE CLASS`, `ENTER CLASS >`, and dialog buttons, including Streamlit inner label wrappers, without using a broad selector that could affect unrelated Streamlit controls on other pages.

No class creation, class deletion, stats, routing, factsheet upload, or API-key behavior changed.
