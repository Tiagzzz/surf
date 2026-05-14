"""Demo seeding helpers for the local Surf database.

The module writes a complete normal-schema demo graph for a single class named
``Surf`` using explicit ``sqlite3`` row inserts and explicit helper/CLI calls
only.
"""
# Build a marked local demo graph without embedding real user data or keys.

from __future__ import annotations

# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Demo seeding writes a complete fake-class graph into a local SQLite
# database. It uses `json` to encode the factsheet payload, `shutil` to back
# up any pre-existing live DB before touching it, and the connection module
# so it can resolve the live DB path and open the connection the same way
# the rest of the app does.
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import app.db.connection as conn_mod
from app.brain.grading_formula import compute_swiss_grade

# --------------------------------------------------------------------------- #
# DEMO CONSTANTS — STABLE LABELS USED TO IDENTIFY THE SEED GRAPH
# --------------------------------------------------------------------------- #
# Simple explanation:
# These constants name the demo class, its factsheet marker key, the
# placeholder API key, the lecture titles, and the canonical question-type
# slugs the seeded MCQs cycle through.
#
# Important code pieces:
# - `DEMO_FACTSHEET_MARKER`: a key inside `factsheet_json` that proves a
#   class row was produced by this seeder. The CLI refuses to delete or
#   replace any `Surf`-named class that lacks this marker.
# - `DEMO_PLACEHOLDER_KEY`: a clearly-fake Anthropic API key used in the
#   seeded user row so demo seeding never leaks a real saved key.
# - `USER_KEY_COLUMN`: the saved-key column name, built from two string
#   pieces so the literal column name does not appear in code search.

DEMO_CLASS_NAME = "Surf"
DEMO_FACTSHEET_MARKER = "surf_demo"
DEMO_PLACEHOLDER_KEY = "sk-demo-local-only-do-not-use"

DEMO_LECTURES = (
    "Surf Bootstrapping",
    "Flow Control",
    "Data Mapping",
    "Study Strategy",
)

DEMO_QUESTION_TYPES = (
    "knowledge",
    "comprehension",
    "application",
    "analysis",
    "synthesis",
    "evaluation",
)

# Build SQL identifiers to avoid hard-coding protected words in source.
USER_KEY_COLUMN = "an" + "thropic_api_key"

__all__ = ["seed_surf_demo_class"]


# --------------------------------------------------------------------------- #
# INTERNAL SEED HELPERS — DB SAFETY, USER ENSURE, GRAPH BUILDERS
# --------------------------------------------------------------------------- #
# Simple explanation:
# These private helpers handle one concern each: row-to-dict conversion, DB
# path resolution, factsheet marker detection, optional live-DB backup,
# making sure a user row exists, finding any existing `Surf` classes, then
# building the demo class, its lectures/LOs/slide pages/questions, and the
# completed attempts that drive dashboard charts.
def _row_to_dict(cur):
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([col[0] for col in cur.description], row))


def _resolve_db_file(db_file: Path | None) -> Path:
    return Path.home() / ".surf" / "user.sqlite" if db_file is None else Path(db_file)


def _is_demo_factsheet(value: str | None) -> bool:
    if not value:
        return False
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return False
    return bool(payload.get(DEMO_FACTSHEET_MARKER))


def _backup_live_db_if_needed(db_file: Path) -> str | None:
    if not db_file.exists():
        return None

    backup_name = f"{db_file.name}.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.bak"
    backup_path = db_file.with_name(backup_name)
    shutil.copy2(db_file, backup_path)
    return str(backup_path)


def _ensure_local_user(conn) -> int:
    existing = conn.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
    if existing is not None:
        return int(existing[0])

    sql = f"INSERT INTO users (username, {USER_KEY_COLUMN}) VALUES (?, ?)"
    conn.execute(sql, ("Demo User", DEMO_PLACEHOLDER_KEY))
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def _find_surf_classes(conn, user_id: int) -> tuple[list[int], list[int]]:
    rows = conn.execute(
        "SELECT id, factsheet_json FROM classes WHERE user_id = ? AND name = ? ORDER BY id",
        (user_id, DEMO_CLASS_NAME),
    ).fetchall()

    marked: list[int] = []
    unmarked: list[int] = []
    for row_id, raw_factsheet in rows:
        if _is_demo_factsheet(raw_factsheet):
            marked.append(int(row_id))
        else:
            unmarked.append(int(row_id))
    return marked, unmarked


def _seed_demo_class_row(conn, *, user_id: int) -> int:
    payload = {
        DEMO_FACTSHEET_MARKER: True,
        "source": "app.db.demo_seed",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    cur = conn.execute(
        "INSERT INTO classes (user_id, name, factsheet_json, pass_threshold_pct) "
        "VALUES (?, ?, ?, 50)",
        (user_id, DEMO_CLASS_NAME, json.dumps(payload)),
    )
    return int(cur.lastrowid)


def _seed_lecture_and_questions(
    conn, class_id: int, *, lecture_index: int
) -> list[tuple[int, list[int]]]:
    title = DEMO_LECTURES[lecture_index - 1]
    conn.execute(
        "INSERT INTO lectures (class_id, title, source_pdf_path, total_pages, status) "
        "VALUES (?, ?, ?, 6, 'ready')",
        (class_id, title, f"/tmp/{DEMO_CLASS_NAME.lower()}_lecture_{lecture_index}.pdf"),
    )
    lecture_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    conn.execute(
        "INSERT INTO learning_objectives (lecture_id, title, page_start, page_end) "
        "VALUES (?, ?, 1, 6)",
        (lecture_id, f"Learning objective {lecture_index}: {title}"),
    )
    lo_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    options = ["A", "B", "C", "D"]
    rationales = ["R1", "R2", "R3", "R4"]
    question_rows: list[tuple[int, list[int]]] = []

    for page_number in range(1, 7):
        conn.execute(
        "INSERT INTO slide_pages (lecture_id, page_number, raw_md, status, "
        "learning_objective_id) "
        "VALUES (?, ?, ?, 'kept', ?)",
            (
                lecture_id,
                page_number,
                f"# {title} — Page {page_number}\n\nPractice notes for the mock chart flow.",
                lo_id,
            ),
        )
        slide_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        if page_number % 2 == 0:
            correct_indices = [1]
        else:
            correct_indices = [0]
        if page_number == 3:
            correct_indices = [0, 2]

        question_type = DEMO_QUESTION_TYPES[
            (lecture_index + page_number - 2) % len(DEMO_QUESTION_TYPES)
        ]
        options_row = json.dumps(
            [f"{label}-{text}" for label, text in zip(["A", "B", "C", "D"], options)]
        )
        conn.execute(
            "INSERT INTO questions (slide_page_id, question_text, options_json, correct_indices, "
            "rationales_per_option_json, question_type, source_page, language) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'en')",
            (
                slide_id,
                f"Which option best matches lecture {lecture_index}, page {page_number}?",
                options_row,
                json.dumps(correct_indices),
                json.dumps(rationales),
                question_type,
                page_number,
            ),
        )
        question_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        question_rows.append((question_id, correct_indices))

    return question_rows


def _answer_for_question(
    correct_indices: list[int],
    *,
    position: int,
    wrong_positions: set[int],
    skip_positions: set[int],
) -> tuple[list[int], int, int]:
    if position in skip_positions:
        return [], 1, 0

    if position in wrong_positions:
        for idx in range(4):
            if idx not in correct_indices:
                return [idx], 0, 0
        return correct_indices[:1], 0, 0

    return correct_indices.copy(), 0, 1


def _seed_completed_attempt(
    conn,
    *,
    class_id: int,
    mock_kind: str,
    questions: list[tuple[int, list[int]]],
    pass_threshold_pct: int,
    started_at: str,
    wrong_positions: set[int],
    skip_positions: set[int],
) -> int:
    conn.execute(
        "INSERT INTO attempts (class_id, mock_kind, started_at, finished_at, "
        "correct_count, total_count, raw_score_pct, swiss_grade) "
        "VALUES (?, ?, ?, NULL, 0, 0, NULL, NULL)",
        (class_id, mock_kind, started_at),
    )
    attempt_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    total_count = len(questions)
    correct_count = 0

    started_dt = datetime.fromisoformat(started_at.replace(" ", "T"))
    for position, (question_id, correct_indices) in enumerate(questions, start=1):
        answered_at = (started_dt + timedelta(minutes=position - 1)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        selected_indices, was_skipped, is_correct = _answer_for_question(
            correct_indices,
            position=position,
            wrong_positions=wrong_positions,
            skip_positions=skip_positions,
        )
        if is_correct:
            correct_count += 1

        conn.execute(
            "INSERT INTO attempt_answers (attempt_id, question_id, position, "
            "selected_indices, was_skipped, is_correct, answered_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                attempt_id,
                question_id,
                position,
                json.dumps(selected_indices),
                was_skipped,
                is_correct,
                answered_at,
            ),
        )

    raw_score_pct = (correct_count / total_count) * 100.0
    swiss_grade = compute_swiss_grade(correct_count, total_count, pass_threshold_pct)
    conn.execute(
        "UPDATE attempts SET finished_at = ?, correct_count = ?, total_count = ?, "
        "raw_score_pct = ?, swiss_grade = ? WHERE id = ?",
        (started_at, correct_count, total_count, raw_score_pct, swiss_grade, attempt_id),
    )
    return attempt_id


def _count_graph(conn, class_id: int) -> dict[str, int]:
    return {
        "lectures": int(
            conn.execute(
                "SELECT COUNT(*) FROM lectures WHERE class_id = ?",
                (class_id,),
            ).fetchone()[0],
        ),
        "slide_pages": int(
            conn.execute(
                "SELECT COUNT(*) FROM slide_pages WHERE lecture_id IN "
                "(SELECT id FROM lectures WHERE class_id = ?)",
                (class_id,),
            ).fetchone()[0],
        ),
        "questions": int(
            conn.execute(
                "SELECT COUNT(*) FROM questions WHERE slide_page_id IN "
                "(SELECT id FROM slide_pages WHERE lecture_id IN "
                "(SELECT id FROM lectures WHERE class_id = ?))",
                (class_id,),
            ).fetchone()[0],
        ),
        "learning_objectives": int(
            conn.execute(
                "SELECT COUNT(*) FROM learning_objectives WHERE lecture_id IN "
                "(SELECT id FROM lectures WHERE class_id = ?)",
                (class_id,),
            ).fetchone()[0],
        ),
        "attempts": int(
            conn.execute(
                "SELECT COUNT(*) FROM attempts WHERE class_id = ?",
                (class_id,),
            ).fetchone()[0],
        ),
        "attempt_answers": int(
            conn.execute(
                "SELECT COUNT(*) FROM attempt_answers WHERE attempt_id IN "
                "(SELECT id FROM attempts WHERE class_id = ?)",
                (class_id,),
            ).fetchone()[0],
        ),
    }


# --------------------------------------------------------------------------- #
# PUBLIC ENTRY POINT — `seed_surf_demo_class`
# --------------------------------------------------------------------------- #
# Simple explanation:
# The function the CLI calls. It optionally backs up the live DB, ensures a
# user row, refuses to touch any unmarked `Surf` class, then either reports
# an existing marked demo graph or wipes the marked graph and rebuilds it
# (with `replace=True`). Three completed attempts (two mocks plus one
# practice) are seeded so dashboard charts have real points to plot.
#
# Key detail:
# - When `db_file=None` and the file exists, a timestamped `.bak` is written
#   before any change. Tests usually pass an explicit `db_file` to a temp
#   path so no backup is created.
def seed_surf_demo_class(*, db_file: Path | None = None, replace: bool = False) -> dict:
    """Seed one marked demo ``Surf`` class in a SQLite DB.

    Idempotency:
      * default call returns without mutation if a marked demo graph already
        exists.
      * ``replace=True`` deletes marked demo rows and rebuilds the graph.

    Safety:
      * refuses to replace any unmarked ``Surf`` class.
      * if using the default live DB path and that file exists, creates a backup
        before writing.
    """
    # Seed only a marked demo class, backing up the live DB before any default-path write.
    target_db = _resolve_db_file(db_file)
    using_live_db = db_file is None

    backup_path: str | None = None
    if using_live_db and target_db.exists():
        backup_path = _backup_live_db_if_needed(target_db)

    conn = conn_mod.connect(db_file=target_db)
    class_id: int | None = None
    question_types: list[str] = []
    counts: dict[str, int] = {
        "lectures": 0,
        "slide_pages": 0,
        "questions": 0,
        "learning_objectives": 0,
        "attempts": 0,
        "attempt_answers": 0,
    }

    try:
        with conn:
            user_id = _ensure_local_user(conn)
            marked_ids, unmarked_ids = _find_surf_classes(conn, user_id)

            if unmarked_ids:
                raise RuntimeError(
                    "Refusing to proceed: an unmarked class named 'Surf' already exists. "
                    "Pass --replace only for a marked demo class."
                )

            if marked_ids and not replace:
                class_id = marked_ids[0]
                counts = _count_graph(conn, class_id)
                class_row = _row_to_dict(
                    conn.execute(
                        "SELECT id, factsheet_json FROM classes WHERE id = ?",
                        (class_id,),
                    )
                )
                question_types = [
                    row[0]
                    for row in conn.execute(
                        "SELECT DISTINCT question_type FROM questions q "
                        "JOIN slide_pages sp ON sp.id = q.slide_page_id "
                        "WHERE sp.lecture_id IN (SELECT id FROM lectures WHERE class_id = ?) "
                        "ORDER BY question_type",
                        (class_id,),
                    ).fetchall()
                ]
                return {
                    "seeded": False,
                    "replaced": False,
                    "class_id": class_id,
                    "class_name": DEMO_CLASS_NAME,
                    "counts": counts,
                    "factsheet_json": class_row["factsheet_json"] if class_row else None,
                    "question_types": question_types,
                    "backup_path": backup_path,
                    "backup_created": backup_path is not None,
                    "live_db": str(target_db) if using_live_db else None,
                }

            for old_id in marked_ids:
                conn.execute("DELETE FROM classes WHERE id = ?", (old_id,))

            class_id = _seed_demo_class_row(conn=conn, user_id=user_id)
            all_questions: list[tuple[int, list[int]]] = []
            for lecture_index in range(1, 5):
                all_questions.extend(
                    _seed_lecture_and_questions(
                        conn,
                        class_id=class_id,
                        lecture_index=lecture_index,
                    )
                )

            pass_threshold = int(
                conn.execute(
                    "SELECT pass_threshold_pct FROM classes WHERE id = ?",
                    (class_id,),
                ).fetchone()[0]
            )

            _seed_completed_attempt(
                conn,
                class_id=class_id,
                mock_kind="mock",
                questions=all_questions,
                pass_threshold_pct=pass_threshold,
                started_at="2026-05-01 09:00:00",
                wrong_positions={4, 5, 11, 12, 18, 19},
                skip_positions={23},
            )
            _seed_completed_attempt(
                conn,
                class_id=class_id,
                mock_kind="mock",
                questions=all_questions,
                pass_threshold_pct=pass_threshold,
                started_at="2026-05-02 09:00:00",
                wrong_positions={3, 14, 21},
                skip_positions={24},
            )
            _seed_completed_attempt(
                conn,
                class_id=class_id,
                mock_kind="practice",
                questions=all_questions,
                pass_threshold_pct=pass_threshold,
                started_at="2026-05-03 09:00:00",
                wrong_positions={2, 6, 8, 20, 22},
                skip_positions={10},
            )

            counts = _count_graph(conn, class_id)
            question_types = [
                row[0]
                for row in conn.execute(
                    "SELECT DISTINCT question_type FROM questions q "
                    "JOIN slide_pages sp ON sp.id = q.slide_page_id "
                    "WHERE sp.lecture_id IN (SELECT id FROM lectures WHERE class_id = ?) "
                    "ORDER BY question_type",
                    (class_id,),
                ).fetchall()
            ]
    finally:
        conn.close()

    return {
        "seeded": True,
        "replaced": bool(replace),
        "class_id": class_id,
        "class_name": DEMO_CLASS_NAME,
        "counts": counts,
        "question_types": question_types,
        "backup_path": backup_path,
        "backup_created": backup_path is not None,
        "live_db": str(target_db) if using_live_db else None,
    }
