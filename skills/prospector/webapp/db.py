"""Database connection helpers for the prospector webapp."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_DIR = Path.home() / ".claude" / "prospector"
DB_PATH = DB_DIR / "prospector.db"
PID_PATH = DB_DIR / "server.pid"

VALID_TRANSITIONS: dict[str, set[str]] = {
    "discovered": {"evaluated", "parked", "rejected"},
    "evaluated": {"researching", "parked", "rejected"},
    "researching": {"building", "parked"},
    "building": {"launched", "parked"},
    "launched": {"parked"},
    "parked": set(),
    "rejected": set(),
}

ALL_STATUSES = set(VALID_TRANSITIONS.keys())

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    one_liner TEXT NOT NULL,
    niche TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'discovered',
    primary_signal TEXT NOT NULL,
    triage_bootstrappability TEXT,
    triage_pmf TEXT,
    triage_competition TEXT,
    triage_revenue TEXT,
    triage_technical TEXT,
    triage_moat TEXT,
    triage_tier TEXT,
    triage_reasoning TEXT,
    counter_evidence_json TEXT DEFAULT '[]',
    panel_json TEXT,
    panel_verdict TEXT,
    mvp_days INTEGER,
    mvp_tech_stack TEXT,
    session_id TEXT NOT NULL,
    seed_query TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
    notes TEXT
);
CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id TEXT NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    source_category TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    source_url TEXT,
    source_tool TEXT,
    quote TEXT,
    intensity TEXT,
    payment_signal INTEGER DEFAULT 0,
    context TEXT,
    accessed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    mode TEXT NOT NULL,
    seed_query TEXT,
    source_filter TEXT,
    opportunities_found INTEGER DEFAULT 0,
    wave_completed INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress',
    started_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
    completed_at TEXT
);
CREATE TABLE IF NOT EXISTS builder_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    tech_stack TEXT DEFAULT '[]',
    constraints TEXT DEFAULT '[]',
    time_budget_hours_week INTEGER DEFAULT 10,
    revenue_goal_mrr INTEGER DEFAULT 1000,
    interests TEXT DEFAULT '[]',
    avoid TEXT DEFAULT '[]',
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);
CREATE INDEX IF NOT EXISTS idx_opp_status ON opportunities(status);
CREATE INDEX IF NOT EXISTS idx_opp_tier ON opportunities(triage_tier);
CREATE INDEX IF NOT EXISTS idx_opp_niche ON opportunities(niche);
CREATE INDEX IF NOT EXISTS idx_opp_session ON opportunities(session_id);
CREATE INDEX IF NOT EXISTS idx_ev_opp ON evidence(opportunity_id);
"""


def get_conn(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = str(db_path or DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def init_db(db_path: str | Path | None = None) -> None:
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn(path)
    conn.executescript(SCHEMA_SQL)
    conn.execute("PRAGMA user_version = 1")
    conn.commit()
    conn.close()
