"""Surf — page splitter (re-exports for downstream callers)."""
from app.brain.ingestion.page_splitter.page_splitter import batch_slides, split_lecture_md

__all__ = ["split_lecture_md", "batch_slides"]
