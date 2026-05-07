CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    phone TEXT,
    default_city TEXT,
    expected_salary_min INTEGER,
    expected_salary_max INTEGER,
    preferred_roles TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS resume (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    raw_text TEXT,
    structured_data TEXT,
    parsed_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS job (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    city TEXT,
    district TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    description TEXT,
    requirements TEXT,
    tags TEXT,
    url TEXT,
    source TEXT DEFAULT 'boss_zhipin',
    posted_date TEXT,
    discovered_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS application (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER REFERENCES job(id),
    resume_id INTEGER REFERENCES resume(id),
    pipeline_stage TEXT NOT NULL DEFAULT 'discovered',
    match_score REAL,
    match_details TEXT,
    applied_at TEXT,
    application_response TEXT,
    interview_scheduled_at TEXT,
    interview_notes TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS offer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER REFERENCES application(id),
    company TEXT NOT NULL,
    position TEXT NOT NULL,
    base_salary INTEGER,
    bonus_months INTEGER DEFAULT 12,
    equity TEXT,
    benefits TEXT,
    work_mode TEXT DEFAULT 'onsite',
    location TEXT,
    commute_minutes INTEGER DEFAULT 0,
    growth_potential TEXT,
    received_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,
    status TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS message_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER REFERENCES application(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
