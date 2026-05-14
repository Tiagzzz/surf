"""Surf — MCQ-generator (re-exports for downstream callers)."""
# --------------------------------------------------------------------------- #
# PACKAGE RE-EXPORT — `app.class_.mcq_generate`
# --------------------------------------------------------------------------- #
# Simple explanation:
# Public door for the MCQ generator. Callers import `generate_mcqs` (one
# Claude call per slide batch) and `MAX_BATCH_SIZE` (the locked batch cap).
from app.class_.mcq_generate.mcq_generator import MAX_BATCH_SIZE, generate_mcqs

__all__ = ["generate_mcqs", "MAX_BATCH_SIZE"]
