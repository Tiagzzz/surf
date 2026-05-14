"""Surf — session/auth helpers.

Replaces the old DB-file-existence auth heuristic in ``streamlit_app.py``
with real saved-user/key checks against the ``users`` table.
Importing this module must not create or mutate ``~/.surf/user.sqlite``;
all DB access is deferred to the query helpers, which themselves use the
lazy ``DB`` proxy from ``app.db.connection``.

This module never logs or returns the saved API key. Callers that need
to display user state must format only the ``username`` field.
"""
# Auth state helpers that avoid exposing the saved Anthropic key.
from __future__ import annotations


def is_authenticated() -> bool:
    """True iff a saved user row exists with a non-blank Anthropic key.

    Imports the query helper lazily so importing ``app.brain.session`` is
    free of DB side effects.
    """
    # A user is authenticated only when a saved key is present.
    from app.db.queries_users import has_saved_user_with_key

    return has_saved_user_with_key()


def get_saved_user() -> dict | None:
    """Return the saved user row as a plain dict (or ``None``) for routing/UI.

    Caller must not log or persist the ``anthropic_api_key`` field.
    """
    # UI callers may read the row, but must not expose the key field.
    from app.db.queries_users import get_active_user

    return get_active_user()


def has_saved_user() -> bool:
    """True iff a saved user row exists, regardless of key state.

    Distinct from :func:`is_authenticated` — useful for UX paths that need
    to know "did anyone sign up here" without leaking key state.
    """
    # Separate signup existence from API-key readiness.
    from app.db.queries_users import get_active_user

    return get_active_user() is not None
