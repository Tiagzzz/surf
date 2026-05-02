# `previews/` — visual sandbox

This folder is the **visual preview gate** for Surf (CLAUDE.md "Visual
Preview Gate" section). Every production component or page that ships
visible UI lands with a sandbox copy here. Tiago runs the sandbox,
visually approves it, and only then is the production change considered
done.

## Sandbox-isolation rule (non-negotiable)

**Files inside `previews/` MUST NOT import from `app/`.** No
`from app...`, no `import app...`, no symlinks pointing into `app/`.
The mechanical enforcement test is `tests/test_no_app_imports_in_previews.py`
— it walks every `*.py` here and fails the build on any match.

When a sandbox needs production code, it carries its own copy. Drift
between the sandbox copy and `app/` is **deliberate** — when production
changes meaningfully, the next visual task that touches the component
refreshes its sandbox copy and re-runs the preview gate.

## Directory layout

```
previews/
├── README.md                   ← this file
├── _theme.py                   ← sandbox copy of app/brain/theme/theme.py
├── _fixtures.py                ← shared pure-data fixtures + fake_call_claude
├── components/
│   └── _theme_bench/           ← the master component bench
│       ├── _theme.py           ← second copy of theme.py (this sandbox is self-contained)
│       └── preview.py
└── spikes/
    └── …                       ← time-boxed risk-reduction sandboxes
```

Each component or page sandbox is its own folder under
`components/<name>/` or `pages/<name>/`. New sandboxes start by copying
`previews/_theme.py` into the folder and importing from `_theme` in
their `preview.py`.

## Stub policy

- **No real Anthropic calls.** Sandboxes use `fake_call_claude(...)`
  from `previews/_fixtures.py` which returns hard-coded JSON for every
  prompt path Phase 2 cares about (factsheet_clean, lo_extract,
  mcq_generate, API-key validate).
- **No real DB.** Sandboxes use either fixture dicts (`FAKE_USER`,
  `FAKE_CLASS`, etc.) or an in-memory SQLite (`sqlite3.connect(":memory:")`).
  Closed sandboxes mean a preview can never accidentally touch the
  user's real `~/.surf/user.sqlite`.
- **No real API keys.** Anthropic stubs ignore the key argument entirely.

## Run pattern

From the repo root:

```bash
streamlit run previews/components/_theme_bench/preview.py
```

The bench opens at `http://localhost:8501`. Tiago confirms the
component renders correctly; production code is approved only after
the visual sign-off.

## Drift policy

When `app/brain/theme/theme.py` changes meaningfully (new component,
re-toned token, MCQ rebuild), refresh both sandbox copies in the
**same commit** as the production change:

```bash
cp app/brain/theme/theme.py previews/_theme.py
cp app/brain/theme/theme.py previews/components/_theme_bench/_theme.py
```

Then re-run the preview gate.

## Why two copies of `_theme.py`?

`previews/_theme.py` is the **template** — new component sandboxes
copy from here to start. `previews/components/_theme_bench/_theme.py`
is a separate copy so the theme bench treats itself as a fully
self-contained sandbox (the bench never reaches outside its own folder
for theme code). Yes, this means the same CSS exists three times in
the tree (production + template + bench). That triplication is the
deliberate cost of sandbox isolation.
