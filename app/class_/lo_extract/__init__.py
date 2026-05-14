"""Surf — LO-extractor (re-exports for downstream callers)."""
# --------------------------------------------------------------------------- #
# PACKAGE RE-EXPORT — `app.class_.lo_extract`
# --------------------------------------------------------------------------- #
# Simple explanation:
# Public door for the learning-objective extractor. `extract_los` is the
# one helper specialist callers need; the system prompt lives next to
# `lo_extractor.py` as a sibling `.md` file so the prompt can be edited
# without touching Python.
from app.class_.lo_extract.lo_extractor import extract_los

__all__ = ["extract_los"]
