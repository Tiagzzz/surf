-- Surf — single-file DDL (schema source of truth, no migrations).
-- All CREATE statements are idempotent (IF NOT EXISTS) so connect() can run
-- this script on every startup without harming an existing DB. For local rebuilds,
-- use the app's backup-first reset helper instead of deleting the live DB by hand.

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
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','ready','failed')),
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

-- slide_pages (one row per slide; status 'kept' | 'ignored' | 'pending')
CREATE TABLE IF NOT EXISTS slide_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecture_id INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    raw_md TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'kept' CHECK (status IN ('kept','ignored','pending')),
    learning_objective_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (lecture_id) REFERENCES lectures(id) ON DELETE CASCADE,
    FOREIGN KEY (learning_objective_id) REFERENCES learning_objectives(id) ON DELETE SET NULL,
    UNIQUE (lecture_id, page_number)
);

-- questions (MCQ schema with multi-correct answers via correct_indices JSON list)
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slide_page_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    options_json TEXT NOT NULL,
    correct_indices TEXT NOT NULL,
    rationales_per_option_json TEXT NOT NULL,
    question_type TEXT,
    source_page INTEGER NOT NULL,
    language TEXT NOT NULL,
    -- 3 current difficulty features (ingestion may compute or leave NULL)
    difficulty_word_count INTEGER,
    difficulty_readability REAL,
    difficulty_distractor_similarity REAL,
    -- 3 PENDING difficulty features (computed via per-MCQ Claude call;
    -- nullable — the ingestion flow may compute them or leave NULL).
    -- Names locked 2026-05-01 per docs/difficulty_criteria_recommendation.md.
    difficulty_conceptual_density INTEGER,
    difficulty_distractor_derivation INTEGER,
    difficulty_reasoning_steps INTEGER,
    difficulty_wording_complexity INTEGER,
    difficulty_wording_clarity_issue INTEGER NOT NULL DEFAULT 0,
    -- Optional difficulty score: nullable legacy/planned analytics field.
    -- The 2026-05-07 ML direction uses a separate future question-type
    -- classifier; current app code must not treat this field as the ML target.
    difficulty_score REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (slide_page_id) REFERENCES slide_pages(id) ON DELETE CASCADE
);

-- attempts (locked mock/practice kind + completion stats).
-- mock_kind CHECK locks the V1 vocabulary so P4 final-submit / P5 review /
-- P6 dashboard helpers can rely on a closed enum at the DB layer.
-- raw_score_pct and swiss_grade are nullable summary fields populated by
-- the all-or-nothing final-submit transaction.
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    mock_kind TEXT NOT NULL CHECK (mock_kind IN ('mock','practice')),
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT,
    correct_count INTEGER,
    total_count INTEGER,
    raw_score_pct REAL,
    swiss_grade REAL,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
);

-- attempt_answers (final-submit row shape).
-- selected_indices is the canonical answer list; is_correct and was_skipped
-- are NOT NULL with 0/1 CHECKs so P4 final submit cannot persist ambiguous
-- rows. UNIQUE(attempt_id, question_id) prevents duplicate answers and
-- UNIQUE(attempt_id, position) preserves the original mock/practice order
-- for review screens.
CREATE TABLE IF NOT EXISTS attempt_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    selected_indices TEXT NOT NULL,
    was_skipped INTEGER NOT NULL CHECK (was_skipped IN (0,1)),
    is_correct INTEGER NOT NULL CHECK (is_correct IN (0,1)),
    answered_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (attempt_id) REFERENCES attempts(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    UNIQUE (attempt_id, question_id),
    UNIQUE (attempt_id, position)
);

-- Indexes — every foreign key plus one class/lecture composite
CREATE INDEX IF NOT EXISTS idx_classes_user_id ON classes(user_id);
CREATE INDEX IF NOT EXISTS idx_lectures_class_id ON lectures(class_id);
CREATE INDEX IF NOT EXISTS idx_learning_objectives_lecture_id ON learning_objectives(lecture_id);
CREATE INDEX IF NOT EXISTS idx_slide_pages_lecture_id ON slide_pages(lecture_id);
CREATE INDEX IF NOT EXISTS idx_slide_pages_lo_id ON slide_pages(learning_objective_id);
CREATE INDEX IF NOT EXISTS idx_questions_slide_page_id ON questions(slide_page_id);
CREATE INDEX IF NOT EXISTS idx_attempts_class_id ON attempts(class_id);
CREATE INDEX IF NOT EXISTS idx_attempt_answers_attempt_id ON attempt_answers(attempt_id);
CREATE INDEX IF NOT EXISTS idx_attempt_answers_question_id ON attempt_answers(question_id);
-- composite: dashboard rollups (per-class, per-lecture)
CREATE INDEX IF NOT EXISTS idx_lectures_class_id_id ON lectures(class_id, id);
