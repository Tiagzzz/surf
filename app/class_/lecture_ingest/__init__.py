"""Surf — lecture ingestion orchestrator (re-exports for downstream callers)."""
from app.class_.lecture_ingest.lecture_ingest import ingest_lecture

__all__ = ["ingest_lecture"]
