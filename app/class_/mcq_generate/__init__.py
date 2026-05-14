"""Surf — MCQ-generator (re-exports for downstream callers)."""
from app.class_.mcq_generate.mcq_generator import MAX_BATCH_SIZE, generate_mcqs

__all__ = ["generate_mcqs", "MAX_BATCH_SIZE"]
