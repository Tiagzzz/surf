# _difficulty.py — difficulty stars display (D-2.24)

**Plain-language summary.** This module paints the little 5-star
difficulty chip that sits next to each question on P4 (Take Mock) and
P5 (Review). It maps a `difficulty_score` float between 0 and 1 to a
star count between 1 and 5 and renders the SVG icons inline.

## How to call

```python
from app.mock_take.question_render._difficulty import difficulty_stars
difficulty_stars(0.62)             # 3 filled + 2 empty stars
```

## In / out

- **Input:** one `score: float`. Values outside `[0.0, 1.0]` are clamped
  via the `min/max` in the level formula.
- **Output:** writes a single inline `<span>` to the Streamlit DOM via
  `st.html`. Returns `None`.

## Where it fits

P4 question_render builds the MCQ card (D-2.23) and includes a
difficulty chip in the header row alongside the Q-number and class
chips. P5 question_render reuses the same component on each result
card. When `difficulty_score IS NULL` (Phase 4 ML hasn't landed yet)
the caller renders a fallback chip with the dashed-border frame and a
"—" placeholder instead of calling this function — so this function
itself never has to handle null.

## Gotchas if real

- **SVGs are read at module load.** `_FILLED_SVG` and `_EMPTY_SVG` are
  loaded once when the module imports. If the icon files change while
  the app is running, restart Streamlit to pick up the new bytes.
- **No `<img>` tags.** Per D-2.24 we inline the SVG markup directly
  inside the span — `<img>` tags introduce DOM-ordering quirks when
  Streamlit re-renders the parent container.
- **The clamp keeps the minimum at 1.** A score of 0 still renders one
  filled star. If you need a "0 of 5" empty visual, render the chip
  frame with a `—` placeholder instead.

## Code walkthrough

**def difficulty_stars(score)** — In plain language: takes a
difficulty number between 0 and 1 and shows a row of 5 stars where the
first few are filled to match the score. Look out for: the formula is
`round(score * 5)` clamped to the range 1–5, so even a 0.0 input shows
one filled star; for "no score yet" cases the caller renders a "—"
placeholder instead of calling this function.
