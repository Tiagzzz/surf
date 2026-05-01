"""Surf — users query wrappers."""
from __future__ import annotations

import pandas as pd

from app.db.connection import DB


def insert_user(username: str, anthropic_api_key: str) -> int:
    with DB:
        cur = DB.execute(
            "INSERT INTO users (username, anthropic_api_key) VALUES (?, ?)",
            (username, anthropic_api_key),
        )
        return cur.lastrowid


def _row_to_dict(cur) -> dict | None:
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([c[0] for c in cur.description], row))


def get_user_by_id(user_id: int) -> dict | None:
    return _row_to_dict(DB.execute("SELECT * FROM users WHERE id = ?", (user_id,)))


def get_user_by_username(username: str) -> dict | None:
    return _row_to_dict(DB.execute("SELECT * FROM users WHERE username = ?", (username,)))


def list_users() -> "pd.DataFrame":
    return pd.read_sql("SELECT * FROM users ORDER BY id", DB)
