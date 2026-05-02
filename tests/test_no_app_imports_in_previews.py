"""Mechanical enforcement of the sandbox-isolation rule (CLAUDE.md).

Every `*.py` under `previews/` is walked; the file fails if any line
matches one of these import patterns:

  - `from app.<anything> import ...`
  - `import app.<anything>`
  - `from app import ...`
  - `import app` (rare, but covered)

The patterns are matched line-by-line via a regex so commented-out
imports (e.g. `# from app.brain.theme import ...`) are also flagged —
this is intentional; CLAUDE.md says "no `from app...` lines" and a
commented import is a footgun (someone uncomments it later).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PREVIEWS_DIR = _REPO_ROOT / "previews"

# Pattern: optional leading whitespace + optional "# " comment marker +
# import statement that pulls from the `app` package.
_BANNED = re.compile(
    r"^\s*#?\s*(from\s+app(\.[A-Za-z0-9_]+)*\s+import|import\s+app(\.[A-Za-z0-9_]+)*)\b"
)


def _python_files_in_previews() -> list[Path]:
    if not _PREVIEWS_DIR.exists():
        return []
    return sorted(_PREVIEWS_DIR.rglob("*.py"))


def test_previews_dir_exists() -> None:
    assert _PREVIEWS_DIR.exists(), "previews/ folder is missing"


@pytest.mark.parametrize("py_path", _python_files_in_previews(), ids=lambda p: p.relative_to(_REPO_ROOT).as_posix())
def test_no_app_imports(py_path: Path) -> None:
    """Each previews/*.py file is checked individually."""
    text = py_path.read_text(encoding="utf-8")
    offenders: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if _BANNED.match(line):
            offenders.append((lineno, line.rstrip()))
    if offenders:
        pretty = "\n".join(f"  line {n}: {ln}" for n, ln in offenders)
        rel = py_path.relative_to(_REPO_ROOT).as_posix()
        pytest.fail(
            f"Sandbox-isolation violation in {rel}:\n{pretty}\n"
            "previews/ must not import from app/. See CLAUDE.md "
            "'Visual Preview Gate' § Sandbox rules."
        )


def test_isolation_check_actually_catches_violations(tmp_path: Path) -> None:
    """Self-test: write a violating file in a tmp dir and confirm the
    regex catches every banned form. Documents the rule for readers."""
    samples = [
        "from app.brain.theme import inject_theme",
        "from app import db",
        "import app.brain.theme",
        "import app",
        "  from app.foo.bar import x",       # leading whitespace
        "# from app.brain.theme import x",    # commented (also banned)
    ]
    for s in samples:
        assert _BANNED.match(s), f"regex failed to catch: {s!r}"

    safe = [
        "from streamlit.testing.v1 import AppTest",
        "import streamlit as st",
        "from _theme import inject_theme",       # sibling-relative
        "from previews._theme import inject_theme",  # within previews/
        "import json",
    ]
    for s in safe:
        assert not _BANNED.match(s), f"regex falsely flagged: {s!r}"
