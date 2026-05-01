"""Surf — classes query wrappers."""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

from app.db.connection import DB


def insert_class(
    user_id: int,
    name: str,
    factsheet_json: dict[str, Any] | str,
    pass_threshold_pct: int = 50,
) -> int:
    payload = factsheet_json if isinstance(factsheet_json, str) else json.dumps(factsheet_json)
    with DB:
        cur = DB.execute(
            "INSERT INTO classes (user_id, name, factsheet_json, pass_threshold_pct) "
            "VALUES (?, ?, ?, ?)",
            (user_id, name, payload, pass_threshold_pct),
        )
        return cur.lastrowid


def get_class_by_id(class_id: int) -> dict | None:
    cur = DB.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
    row = cur.fetchone()
    if row is None:
        return None
    out = dict(zip([c[0] for c in cur.description], row))
    out["factsheet_json"] = json.loads(out["factsheet_json"])
    return out


def list_classes_for_user(user_id: int) -> "pd.DataFrame":
    return pd.read_sql(
        "SELECT * FROM classes WHERE user_id = ? ORDER BY id",
        DB,
        params=(user_id,),
    )
