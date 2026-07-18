PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_meta (version, applied_at)
VALUES (1, '2026-07-19T00:00:00Z');

CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    decision_domain TEXT NOT NULL,
    title TEXT NOT NULL,
    state TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS policy_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL REFERENCES cases(case_id),
    assessment_hash TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    state TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    evaluated_at TEXT NOT NULL,
    UNIQUE (case_id, assessment_hash, policy_version, evaluated_at)
);

CREATE INDEX IF NOT EXISTS idx_policy_results_case
ON policy_results (case_id, result_id);
