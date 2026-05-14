"""Surf — lecture ingestion orchestrator (re-exports for downstream callers)."""
# --------------------------------------------------------------------------- #
# PACKAGE RE-EXPORT — `app.class_.lecture_ingest`
# --------------------------------------------------------------------------- #
# Simple explanation:
# Public door for the lecture-ingest orchestrator. The actual function
# lives in `lecture_ingest.py` next to this file; this shim lets callers
# write `from app.class_.lecture_ingest import ingest_lecture` cleanly.
from app.class_.lecture_ingest.lecture_ingest import ingest_lecture

__all__ = ["ingest_lecture"]
