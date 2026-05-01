-- Surf — single-file DDL (D-3.1 wipe-and-rerun, no migrations).
-- All CREATE statements are idempotent (IF NOT EXISTS) so connect() can run
-- this script on every startup without harming an existing DB. Drop the file
-- (~/.surf/user.sqlite) and re-run to apply schema changes during the build.

-- users (single-user app; row count is always 0 or 1)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    anthropic_api_key TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- classes (HSG courses; one factsheet per class, stored as JSON in factsheet_json)
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    factsheet_json TEXT NOT NULL,
    pass_threshold_pct INTEGER NOT NULL DEFAULT 50,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- lectures (one row per ingested lecture PDF)
CREATE TABLE IF NOT EXISTS lectures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    source_pdf_path TEXT NOT NULL,
    total_pages INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
);

-- learning_objectives (output of LO-extractor)
CREATE TABLE IF NOT EXISTS learning_objectives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecture_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    page_start INTEGER NOT NULL,
    page_end INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (lecture_id) REFERENCES lectures(id) ON DELETE CASCADE
);

-- slide_pages (one row per slide; status 'kept' | 'ignored' | 'pending' per D-4.5/D-4.8)
CREATE TABLE IF NOT EXISTS slide_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecture_id INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    raw_md TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'kept',
    learning_objective_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (lecture_id) REFERENCES lectures(id) ON DELETE CASCADE,
    FOREIGN KEY (learning_objective_id) REFERENCES learning_objectives(id) ON DELETE SET NULL,
    UNIQUE (lecture_id, page_number)
);

-- questions (D-2.4 schema, D-2.5 multi-correct via correct_indices JSON list)
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slide_page_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    options_json TEXT NOT NULL,
    correct_indices TEXT NOT NULL,
    rationales_per_option_json TEXT NOT NULL,
    source_page INTEGER NOT NULL,
    language TEXT NOT NULL,
    -- 3 LOCKED difficulty features (Phase 1 may compute or leave NULL)
    difficulty_word_count INTEGER,
    difficulty_readability REAL,
    difficulty_distractor_similarity REAL,
    -- 3 PENDING difficulty features (Phase 4 ML; Phase 1 always NULL)
    difficulty_topic REAL,
    difficulty_concept_overlap REAL,
    difficulty_skip_confidence REAL,
    difficulty_score REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (slide_page_id) REFERENCES slide_pages(id) ON DELETE CASCADE
);

-- attempts (Phase 2 will populate; included now per DB-01 schema completeness)
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    mock_kind TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT,
    correct_count INTEGER,
    total_count INTEGER,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
);

-- attempt_answers (Phase 2 populates; one row per question shown)
CREATE TABLE IF NOT EXISTS attempt_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_indices TEXT,
    is_correct INTEGER,
    answered_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (attempt_id) REFERENCES attempts(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- Indexes (D-3.3) — every FK + composite (class_id, lecture_id)
CREATE INDEX IF NOT EXISTS idx_classes_user_id ON classes(user_id);
CREATE INDEX IF NOT EXISTS idx_lectures_class_id ON lectures(class_id);
CREATE INDEX IF NOT EXISTS idx_learning_objectives_lecture_id ON learning_objectives(lecture_id);
CREATE INDEX IF NOT EXISTS idx_slide_pages_lecture_id ON slide_pages(lecture_id);
CREATE INDEX IF NOT EXISTS idx_slide_pages_lo_id ON slide_pages(learning_objective_id);
CREATE INDEX IF NOT EXISTS idx_questions_slide_page_id ON questions(slide_page_id);
CREATE INDEX IF NOT EXISTS idx_attempts_class_id ON attempts(class_id);
CREATE INDEX IF NOT EXISTS idx_attempt_answers_attempt_id ON attempt_answers(attempt_id);
CREATE INDEX IF NOT EXISTS idx_attempt_answers_question_id ON attempt_answers(question_id);
-- composite (D-3.3): dashboard rollups (per-class, per-lecture)
CREATE INDEX IF NOT EXISTS idx_lectures_class_id_id ON lectures(class_id, id);
