"""Surf — page splitter (re-exports for downstream callers)."""
# --------------------------------------------------------------------------- #
# PACKAGE RE-EXPORT — `app.brain.ingestion.page_splitter`
# --------------------------------------------------------------------------- #
# Simple explanation:
# Tiny shim file that promotes the two helpers from the inner module so
# callers can write `from app.brain.ingestion.page_splitter import ...`
# without knowing the inner filename.
#
# Important code pieces:
# - `split_lecture_md`: cuts the lecture markdown into per-slide records
#   using `--- PAGE N ---` markers.
# - `batch_slides`: groups those records into small batches for the MCQ
#   generator so each Claude call stays a reasonable size.
from app.brain.ingestion.page_splitter.page_splitter import batch_slides, split_lecture_md

__all__ = ["split_lecture_md", "batch_slides"]
