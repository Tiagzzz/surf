# edit_this_later.md — single edit-map for the Surf design system

Every locked visual decision (D-2.12..D-2.24) maps to **one** location
in the codebase. This file is the index. When a visual rule needs to
change, find the row, follow the path.

## Tokens (D-2.12)

| Decision | Where it lives | What to change | Propagation |
|---|---|---|---|
| Paper ladder hex values (`--paper..--paper-5`) | `app/brain/theme/theme.py` `_CSS` `:root` block | Edit the hex on the custom property | Every component re-themes automatically; also update the matching column in `.streamlit/config.toml [theme]` |
| Accent hex values (`--accent-vibrant`, `--accent-deep`, `--accent-soft`, `--accent-wash`) | Same `:root` block | Same | Same — also update `[theme] primaryColor` in `.streamlit/config.toml` |
| Status colors (`--ok`, `--ok-wash`, `--warn`, `--info`) | Same `:root` block | Same | Same |
| Radii (`--r-xs`, `--r-sm`, `--r-md`, `--r-lg`, `--r-pill`) | Same `:root` block | Edit the px values | Used on cards, buttons, inputs, MCQ container; MCQ option uses a literal `5px` (intentional) |
| Motion tokens (`--ease`, `--t-fast`, `--t-base`, `--t-slow`) | Same `:root` block | Edit the duration | Reduced-motion media query at the bottom of `_CSS` overrides for accessibility |
| Type stack (`--serif`, `--mono`) | Same `:root` block | Swap font-family fallbacks | If you change the family name, also update the `@font-face` rule at the top |

## Stamp shadow (D-2.13)

| Decision | Where it lives | What to change | Propagation |
|---|---|---|---|
| 3px stamp on default + tinted buttons, class card, interactive card | `_CSS` per-component selector | Change `box-shadow: 3px 3px 0 0 var(--paper-shadow)` | Per-component; consider a CSS custom property if changing globally |
| 4px stamp on interactive card hover | `[class*="st-key-card-interactive"]:hover` | Change the hover offset | Per-component |
| 2px stamp on soft button, passive card, stat card | Per-component selectors | Change the offset | Per-component |
| Hover lift `translate(-1px, -1px)` | Per-component selectors | Change the translate | Reduced-motion query already disables it |

## Animation primitives (D-2.14)

| Decision | Where it lives | What to change | Propagation |
|---|---|---|---|
| Transitions only — no `@keyframes` | `_CSS` global rule | Don't introduce keyframes; if you do, add a reduced-motion override | App-wide |

## Reduced motion (D-2.15)

| Decision | Where it lives | What to change | Propagation |
|---|---|---|---|
| `@media (prefers-reduced-motion: reduce)` block | Bottom of `_CSS` | Add new selectors to the comma list when introducing a new interactive surface | App-wide |

## Self-hosted fonts (D-2.16)

| Decision | Where it lives | What to change | Propagation |
|---|---|---|---|
| Three `@font-face` rules | Top of `_CSS` | Edit the `src: url(...)` paths | Files live in `assets/fonts/` |
| Streamlit fallback `font` field | `.streamlit/config.toml [theme]` (currently absent — fallback to "serif" via Streamlit default) | Add or remove the `font` line | Only matters if a Streamlit-native widget paints before our CSS binds |
| Add WONK/SOFT axes for pixel-perfect Figma italic | Re-fetch from Google Fonts CSS2 with full axis query, swap the woff2 file, add `font-variation-settings: 'SOFT' 0, 'WONK' 1` to `:root` | Same | Visible in question text on P4/P5 |

## Theme delivery (D-2.17)

| Decision | Where it lives | What to change | Propagation |
|---|---|---|---|
| Embedded `_CSS` Python string | `app/brain/theme/theme.py` | Edit the string | Sandbox copy at `previews/_theme.py` must re-sync on next visual task |
| Split `_CSS` into a sibling `theme.css` (only if string exceeds ~800 lines) | Replace `_CSS = """..."""` with `_CSS = (Path(__file__).with_name("theme.css")).read_text()` | Module API stays identical | None |

## Scoping (D-2.18)

| Decision | Where it lives | What to change | Propagation |
|---|---|---|---|
| `[class*="st-key-XXX"]` selectors | `_CSS` per component | When adding a component, pick a key from the canonical vocabulary | Drift between production and sandbox key names breaks scoped CSS silently |

## Helpers (D-2.19)

| Decision | Where it lives | What to change | Propagation |
|---|---|---|---|
| `html.escape()` on all user-supplied text | `app/brain/theme/theme.py` helper functions | Keep escapes when extending; new helpers must escape too | Sandbox copy must mirror |
| Add a new helper | Below the existing 9 in `theme.py` | Follow the 1-liner pattern: `st.markdown(f'<p class="surf-X">{html.escape(text)}</p>', unsafe_allow_html=True)` | Re-export from `__init__.py` |

## MCQ option (D-2.20)

| Decision | Where it lives | What to change | Propagation |
|---|---|---|---|
| Four state styles (off/on/correct/incorrect) | `_CSS` `MCQ OPTION` section | Edit the bg/border per state | Production + sandbox copies |
| Custom checkbox glyph (20×20, 5px radius, `✓` on check) | `_CSS` same section | Edit the `[data-baseweb="checkbox"] > div:first-child` block | Production + sandbox |
| State key vocabulary `mcq-opt-{key}-{state}` | Both `theme.py` (CSS branches on suffix) and the call sites in `app/mock_take/question_render/` | Don't drift | Breaks scoped CSS |

## st.status + st.expander skins (D-2.21)

| Decision | Where it lives | What to change | Propagation |
|---|---|---|---|
| Status left-border colors per state | `_CSS` `STATUS · EXPANDER` section | Edit the border-left-color per `data-state` attribute | App-wide |
| Expander hover lift | Same section | Edit the transform/box-shadow | App-wide |

## MCQ card container (D-2.23)

| Decision | Where it lives | What to change | Propagation |
|---|---|---|---|
| Container: 6px radius, 3px stamp, 22/20/20/20 padding, 600px max-width | `_CSS` `MCQ CARD CONTAINER` section | Edit the values per spec | When P4 question_render changes layout |

## Difficulty stars (D-2.24)

| Decision | Where it lives | What to change | Propagation |
|---|---|---|---|
| Filled / empty star SVG | `assets/icons/star_filled.svg`, `assets/icons/star_empty.svg` | Replace the SVG | Read at module load — restart Streamlit |
| Score → level mapping | `app/mock_take/question_render/_difficulty.py` | Edit the `n = max(1, min(5, round(score * 5)))` line | App-wide |
| NULL difficulty placeholder | Caller in `app/mock_take/question_render/` (don't call `difficulty_stars` if score is NULL) | Render the dashed chip + "—" instead | Caller decision |
