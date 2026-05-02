# theme.py — Surf design system (paper-and-stamp)

**Plain-language summary.** This file is the look-and-feel for the whole
app. It exposes one entry-point — `inject_theme()` — that paints the
entire Streamlit page with our editorial paper aesthetic, plus nine tiny
HTML helpers (`eyebrow`, `caption`, `meta`, `score`, `chip`, `chips_row`,
`steps`, `stat_card`, `empty_state_text`) that any view can call to
render a styled fragment in one line. Tokens (colors, radii, motion,
type) live as CSS custom properties at the top of `_CSS`; change a
hex once, every component re-themes automatically.

## How to call

```python
from app.brain.theme import inject_theme, eyebrow, score
inject_theme()                     # once at app entry, before st.navigation
eyebrow("OVERVIEW")                # mono uppercase tracking-out label
score(5.32)                        # big italic Fraunces grade — green ≥5
```

## In / out

- **Input:** `inject_theme()` takes nothing. Helpers take user-supplied
  strings (`text: str`); every helper html-escapes its input before
  interpolating into `st.markdown(unsafe_allow_html=True)` (D-2.19
  hardening).
- **Output:** all helpers return `None` and write directly into the
  Streamlit DOM. The single exception is `chip(text)` which returns the
  HTML string so callers can compose chip rows themselves.

## Where it fits

`streamlit_app.py` calls `inject_theme()` once at the top, before
`st.navigation`. After that, every page in `views/` and every component
under `app/<bucket>/<pipeline>/` can import the helpers and assume the
CSS is already in the page. The same module is mirrored at
`previews/_theme.py` (sandbox copy, D-2.22) — drift between the two is
deliberate; refresh the sandbox copy on the next visual task that
touches theme.

## Gotchas if real

- **Font path resolution.** Self-hosted `@font-face` URLs use absolute
  paths (`/assets/fonts/...`). Streamlit ≥1.50 serves the `assets/`
  folder from the working directory automatically — but only when the
  app is launched from the repo root. Launching from elsewhere will
  cause the fonts to fall back to Georgia/Menlo (still legible, off-brand).
- **`unsafe_allow_html=True` is for typography helpers only.** The
  helpers below use it to render styled `<p class="surf-…">` markup
  inside Streamlit's own widgets. We do NOT inject layout HTML — layout
  scoping uses `st.container(key="…")` per D-2.18.
- **Sandbox sync.** When a meaningful change lands here (new component,
  re-toned token), the next visual task touching that component
  refreshes `previews/_theme.py` and re-runs the preview gate. CLAUDE.md
  Visual Preview Gate enforces this.
- **Streamlit ≥ 1.50 required.** Older versions don't ship the
  `[theme] baseRadius` knob in `.streamlit/config.toml` and don't accept
  `key=` on every `st.container`. The pin lives in `pyproject.toml`.

## Code walkthrough

**def inject_theme()** — In plain language: pastes the entire `_CSS`
string into the Streamlit DOM via `st.markdown(unsafe_allow_html=True)`
so the whole app inherits the paper-and-stamp look. Idempotent across
reruns; calling it twice is harmless. Look out for: launch must be from
the repo root for the self-hosted font URLs to resolve.

**def eyebrow(text)** — In plain language: writes a tiny mono-uppercase
"section header" line (e.g. `OVERVIEW`) above a card or section. Takes
one string, escapes it, wraps in `<p class="surf-eyebrow">`. Look out
for: this is decoration, not a heading — screen readers ignore it.

**def caption(text)** — In plain language: writes a small italic helper
line under a heading (e.g. *"Two seasons of class data"*). Takes one
string, escapes, wraps in `<p class="surf-caption">`.

**def meta(text)** — In plain language: writes a mono mid-grey one-liner
(e.g. `12 LECTURES · 78%`) — the metadata strip on a card. Takes one
string, escapes, wraps in `<p class="surf-meta">`.

**def score(value)** — In plain language: paints a big italic Fraunces
grade in our 1–6 Swiss-school scale. Takes a float; under 3.5 paints
red, 3.5–4.99 paints gold, 5+ paints green. Look out for: format is
fixed at two decimals (`5.32`); pre-format the value if you need a
different grain.

**def chip(text, variant)** — In plain language: returns the HTML for
one little tag (e.g. `LECTURE 03`). Variant controls the look —
`outline` (default), `accent` (red text + border), `solid` (dark fill),
`dashed` (dashed outline). Returns the string; doesn't write to the
page.

**def chips_row(items)** — In plain language: writes a row of chips
side-by-side. Takes a list of `(text, variant)` pairs and prints them.
Look out for: `chip` itself escapes text, so `chips_row` is safe by
construction.

**def steps(items)** — In plain language: writes a "Sign up → Add class
→ Take mock" inline step bar. Takes a list of `(label, status)` where
status is `done`, `active`, or `todo`. Done steps show a check; active
shows a number with the accent fill; todo shows an outlined number.
Look out for: an unknown status string defaults to `todo` rather than
allowing arbitrary class names through.

**def stat_card(label, value, eyebrow_text, delta, delta_dir)** — In
plain language: writes the three stacked typography lines that compose
a KPI card — eyebrow on top, label, big italic value, optional
trend-arrow `delta`. Pair it with `st.container(key="stat-card-x")` to
get the framed surface. Look out for: `delta_dir` outside the
`up/down/flat` whitelist defaults to `flat`.

**def empty_state_text(headline, body)** — In plain language: writes
the three-line "✲ ✲ ✲ / NO MOCKS YET / Take a mock to see your stats"
block used inside an empty-state card. Pair with
`st.container(key="empty-…")` for the dashed-border frame.
