"""Factsheet cleaning package export for P2 class setup."""
# --------------------------------------------------------------------------- #
# PACKAGE EXPORT — `clean_factsheet`
# --------------------------------------------------------------------------- #
# Simple explanation:
# Re-exports the one public function in this package so callers can write
# `from app.my_classes.factsheet_clean import clean_factsheet` without
# knowing which file actually defines it. The implementation lives in
# `factsheet_cleaner.py` (the ~10-line Claude wrapper); the renderer for
# the cleaned JSON lives next to it in `factsheet_renderer.py`.
from app.my_classes.factsheet_clean.factsheet_cleaner import clean_factsheet

__all__ = ["clean_factsheet"]
