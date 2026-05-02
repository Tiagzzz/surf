"""Streamlit AppTest helpers + a fake Anthropic client for tests.

Layered on top of `tests/_fakes.py` (Phase 1 deterministic fakes for
`fake_extract_los` / `fake_generate_mcqs`). This module adds:

  - `make_apptest(script_path)` — thin wrapper around
    `st.testing.v1.AppTest.from_file` that resolves the path relative
    to the repo root.
  - `fake_anthropic_client()` — drop-in replacement for
    `app.brain.claude_client.call_claude` that returns the same hard-
    coded JSON as `previews/_fixtures.fake_call_claude`. Phase 2 tests
    that exercise the live Claude path through views/<page>.py wrappers
    monkey-patch the real `call_claude` symbol with this.

Both helpers are pure: no network, no DB, no real Anthropic SDK.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from streamlit.testing.v1 import AppTest

_REPO_ROOT = Path(__file__).resolve().parent.parent


def make_apptest(script_path: str | Path, *, timeout: float = 5.0) -> AppTest:
    """Create an AppTest for the given script path.

    `script_path` is resolved relative to the repo root if not absolute,
    so callers can write `make_apptest("views/signup.py")` or
    `make_apptest("previews/components/_theme_bench/preview.py")`.
    """
    p = Path(script_path)
    if not p.is_absolute():
        p = _REPO_ROOT / p
    return AppTest.from_file(str(p), default_timeout=timeout)


def fake_anthropic_client(
    *,
    system_prompt: str,
    user_message: str = "",
    expect_json: bool = False,
    **_kwargs: Any,
) -> dict[str, Any] | str:
    """Same hard-coded responses as `previews/_fixtures.fake_call_claude`.

    Mirrored here (not imported) because `tests/` and `previews/` are
    independent isolation contexts — `previews/` must not import from
    `app/`, and the test harness must not depend on `previews/`. So the
    stub lives in both places by design.
    """
    sp = system_prompt.lower()

    # 1. API-key validate ping
    if "validate" in sp or "ping" in sp or len(system_prompt) < 80:
        return {"ok": True} if expect_json else "ok"

    # 2. factsheet_clean
    if "factsheet" in sp or "clean" in sp:
        return {
            "title": "Microeconomics I",
            "semester": "Spring 2026",
            "professor": "Prof. K. Müller",
            "goal": "Understand supply and demand in competitive markets.",
            "format": "12 lectures · written exam.",
            "assessment": "70% final exam, 30% participation.",
            "language": "EN",
        }

    # 3. lo_extract — defer to Phase 1 fake
    if "learning objective" in sp or "lo_extract" in sp:
        from tests._fakes import fake_extract_los
        return fake_extract_los(user_message, {})

    # 4. mcq_generate — defer to Phase 1 fake (single-slide, page 1)
    if "mcq" in sp or "multiple-choice" in sp or "generate" in sp:
        from tests._fakes import fake_generate_mcqs
        return fake_generate_mcqs([{"page_number": 1, "raw_md": user_message}])

    return {} if expect_json else ""
