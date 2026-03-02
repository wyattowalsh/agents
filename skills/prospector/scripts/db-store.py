#!/usr/bin/env python3
"""SQLite CRUD for prospector skill.

Manages opportunities, evidence, sessions, and builder profile in
~/.claude/prospector/prospector.db.

Usage:
  python db-store.py init
  python db-store.py save-opportunity --title "AI Meeting Notes" --niche "productivity" ...
  python db-store.py load OPP-0001
  python db-store.py list --status discovered --tier strong
  python db-store.py update OPP-0001 --status evaluated
  python db-store.py stats
  python db-store.py dedup-check --title "AI Meeting Notes" --niche "productivity"
"""
import argparse
import contextlib
import csv
import io
import json
import re
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

DB_DIR = Path.home() / ".claude" / "prospector"
DB_PATH = DB_DIR / "prospector.db"

SCHEMA_VERSION = 1

# --- Valid values ---

_VALID_STATUSES = {
    "discovered", "evaluated", "researching", "building",
    "launched", "parked", "rejected",
}

_VALID_SIGNALS = {
    "pain_no_solution", "dying_product", "platform_expansion",
    "rising_trend", "terrible_ux", "manual_workflow",
}

_VALID_RATINGS = {"strong", "moderate", "weak"}

_VALID_TIERS = {"strong", "moderate", "weak"}

_VALID_SESSION_MODES = {"mine", "scan", "evaluate"}

_VALID_SESSION_STATUSES = {"in_progress", "complete", "interrupted"}

_VALID_PANEL_VERDICTS = {"go", "nogo", "conditional"}

# Lifecycle transitions: from_status -> set of valid to_statuses
_TRANSITIONS = {
    "discovered": {"evaluated", "parked", "rejected"},
    "evaluated": {"researching", "parked", "rejected"},
    "researching": {"building", "parked"},
    "building": {"launched", "parked"},
    "launched": {"parked"},
    "parked": set(),
    "rejected": set(),
}


# --- Database connection ---

def get_db(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")


# --- Init ---

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    one_liner TEXT NOT NULL,
    niche TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'discovered'
        CHECK (status IN ('discovered','evaluated','researching','building','launched','parked','rejected')),
    primary_signal TEXT NOT NULL
        CHECK (primary_signal IN ('pain_no_solution','dying_product','platform_expansion',
                                   'rising_trend','terrible_ux','manual_workflow')),
    triage_bootstrappability TEXT CHECK (triage_bootstrappability IN ('strong','moderate','weak')),
    triage_pmf TEXT CHECK (triage_pmf IN ('strong','moderate','weak')),
    triage_competition TEXT CHECK (triage_competition IN ('strong','moderate','weak')),
    triage_revenue TEXT CHECK (triage_revenue IN ('strong','moderate','weak')),
    triage_technical TEXT CHECK (triage_technical IN ('strong','moderate','weak')),
    triage_moat TEXT CHECK (triage_moat IN ('strong','moderate','weak')),
    triage_tier TEXT CHECK (triage_tier IN ('strong','moderate','weak')),
    triage_reasoning TEXT,
    counter_evidence_json TEXT DEFAULT '[]',
    panel_json TEXT,
    panel_verdict TEXT CHECK (panel_verdict IN ('go','nogo','conditional') OR panel_verdict IS NULL),
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
    intensity TEXT CHECK (intensity IN ('strong','moderate','weak')),
    payment_signal INTEGER DEFAULT 0,
    context TEXT,
    accessed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    mode TEXT NOT NULL CHECK (mode IN ('mine','scan','evaluate')),
    seed_query TEXT,
    source_filter TEXT,
    opportunities_found INTEGER DEFAULT 0,
    wave_completed INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress' CHECK (status IN ('in_progress','complete','interrupted')),
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


def cmd_init(args: argparse.Namespace) -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    conn.executescript(_SCHEMA_SQL)
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.commit()
    conn.close()
    json.dump({"action": "initialized", "db": str(DB_PATH), "version": SCHEMA_VERSION}, sys.stdout, indent=2)
    print()


# --- Migrate ---

def cmd_migrate(args: argparse.Namespace) -> None:
    conn = get_db()
    current = conn.execute("PRAGMA user_version").fetchone()[0]

    if current >= SCHEMA_VERSION:
        json.dump({"action": "no_migration_needed", "version": current}, sys.stdout, indent=2)
        print()
        conn.close()
        return

    # Add migration steps here as SCHEMA_VERSION increases
    # Example: if current < 2: conn.execute("ALTER TABLE ...")

    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.commit()
    json.dump({"action": "migrated", "from_version": current, "to_version": SCHEMA_VERSION}, sys.stdout, indent=2)
    print()
    conn.close()


# --- ID generation ---

def next_opp_id(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT id FROM opportunities ORDER BY id DESC LIMIT 1").fetchone()
    if row is None:
        return "OPP-0001"
    last = row["id"]
    match = re.match(r"OPP-(\d+)", last)
    num = int(match.group(1)) + 1 if match else 1
    return f"OPP-{num:04d}"


# --- Save opportunity ---

def cmd_save_opportunity(args: argparse.Namespace) -> None:
    conn = get_db()

    triage = {}
    if args.triage:
        try:
            triage = json.loads(args.triage)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON in --triage: {exc}", file=sys.stderr)
            sys.exit(1)

    evidence_list = []
    if args.evidence:
        try:
            evidence_list = json.loads(args.evidence)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON in --evidence: {exc}", file=sys.stderr)
            sys.exit(1)

    counter_evidence = "[]"
    if args.counter_evidence:
        try:
            json.loads(args.counter_evidence)
            counter_evidence = args.counter_evidence
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON in --counter-evidence: {exc}", file=sys.stderr)
            sys.exit(1)

    signal = args.signal or "pain_no_solution"
    if signal not in _VALID_SIGNALS:
        print(f"Error: invalid signal type: {signal!r}", file=sys.stderr)
        sys.exit(1)

    opp_id = next_opp_id(conn)
    ts = now_iso()

    conn.execute(
        """INSERT INTO opportunities
           (id, title, one_liner, niche, status, primary_signal,
            triage_bootstrappability, triage_pmf, triage_competition,
            triage_revenue, triage_technical, triage_moat,
            triage_tier, triage_reasoning, counter_evidence_json,
            panel_json, panel_verdict, mvp_days, mvp_tech_stack,
            session_id, seed_query, created_at, updated_at, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            opp_id,
            args.title,
            args.one_liner or "",
            args.niche,
            "discovered",
            signal,
            triage.get("bootstrappability"),
            triage.get("pmf_signals"),
            triage.get("competition"),
            triage.get("revenue_potential"),
            triage.get("technical_feasibility"),
            triage.get("moat_potential"),
            triage.get("tier"),
            triage.get("reasoning"),
            counter_evidence,
            None,
            None,
            args.mvp_days,
            args.mvp_tech_stack,
            args.session_id or "",
            args.seed_query,
            ts,
            ts,
            args.notes,
        ),
    )

    # Insert evidence rows
    for ev in evidence_list:
        conn.execute(
            """INSERT INTO evidence
               (opportunity_id, source_category, signal_type, source_url,
                source_tool, quote, intensity, payment_signal, context, accessed_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                opp_id,
                ev.get("source_category", ""),
                ev.get("signal_type", ""),
                ev.get("source_url"),
                ev.get("source_tool"),
                ev.get("quote"),
                ev.get("intensity"),
                1 if ev.get("payment_signal") else 0,
                ev.get("context"),
                ev.get("accessed_at", ts),
            ),
        )

    conn.commit()
    conn.close()

    json.dump({"action": "saved", "id": opp_id}, sys.stdout, indent=2)
    print()


# --- Load ---

def cmd_load(args: argparse.Namespace) -> None:
    conn = get_db()
    target = args.id

    # Support both OPP-XXXX and bare number
    if re.match(r"^\d+$", target):
        target = f"OPP-{int(target):04d}"

    row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (target,)).fetchone()
    if row is None:
        print(f"Error: opportunity not found: {target}", file=sys.stderr)
        sys.exit(1)

    opp = dict(row)

    evidence_rows = conn.execute(
        "SELECT * FROM evidence WHERE opportunity_id = ? ORDER BY id",
        (target,),
    ).fetchall()
    opp["evidence"] = [dict(r) for r in evidence_rows]

    conn.close()
    json.dump(opp, sys.stdout, indent=2, default=str)
    print()


# --- List ---

def cmd_list(args: argparse.Namespace) -> None:
    conn = get_db()
    query = "SELECT * FROM opportunities WHERE 1=1"
    params: list = []

    if args.status:
        query += " AND status = ?"
        params.append(args.status)
    if args.tier:
        query += " AND triage_tier = ?"
        params.append(args.tier)
    if args.niche:
        query += " AND niche LIKE ?"
        params.append(f"%{args.niche}%")

    query += " ORDER BY created_at DESC"

    if args.limit:
        query += " LIMIT ?"
        params.append(args.limit)

    rows = conn.execute(query, params).fetchall()
    result = [dict(r) for r in rows]
    conn.close()

    json.dump(result, sys.stdout, indent=2, default=str)
    print()


# --- Update ---

def cmd_update(args: argparse.Namespace) -> None:
    conn = get_db()
    target = args.id

    if re.match(r"^\d+$", target):
        target = f"OPP-{int(target):04d}"

    row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (target,)).fetchone()
    if row is None:
        print(f"Error: opportunity not found: {target}", file=sys.stderr)
        sys.exit(1)

    updates: list[str] = []
    params: list = []

    if args.status:
        current_status = row["status"]
        if args.status not in _VALID_STATUSES:
            print(f"Error: invalid status: {args.status!r}", file=sys.stderr)
            sys.exit(1)
        allowed = _TRANSITIONS.get(current_status, set())
        if args.status != current_status and args.status not in allowed:
            print(
                f"Error: invalid transition {current_status} -> {args.status}. "
                f"Allowed: {sorted(allowed) if allowed else 'none (terminal state)'}",
                file=sys.stderr,
            )
            sys.exit(1)
        updates.append("status = ?")
        params.append(args.status)

    if args.notes is not None:
        updates.append("notes = ?")
        params.append(args.notes)

    if args.panel_json is not None:
        try:
            panel = json.loads(args.panel_json)
            verdict = panel.get("final_verdict")
            if verdict and verdict not in _VALID_PANEL_VERDICTS:
                print(f"Error: invalid panel verdict: {verdict!r}", file=sys.stderr)
                sys.exit(1)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON in --panel-json: {exc}", file=sys.stderr)
            sys.exit(1)
        updates.append("panel_json = ?")
        params.append(args.panel_json)
        if verdict:
            updates.append("panel_verdict = ?")
            params.append(verdict)

    if not updates:
        print("Error: nothing to update.", file=sys.stderr)
        sys.exit(1)

    updates.append("updated_at = ?")
    params.append(now_iso())
    params.append(target)

    conn.execute(
        f"UPDATE opportunities SET {', '.join(updates)} WHERE id = ?",
        params,
    )
    conn.commit()
    conn.close()

    json.dump({"action": "updated", "id": target}, sys.stdout, indent=2)
    print()


# --- Delete ---

def cmd_delete(args: argparse.Namespace) -> None:
    conn = get_db()
    target = args.id

    if re.match(r"^\d+$", target):
        target = f"OPP-{int(target):04d}"

    row = conn.execute("SELECT id FROM opportunities WHERE id = ?", (target,)).fetchone()
    if row is None:
        print(f"Error: opportunity not found: {target}", file=sys.stderr)
        sys.exit(1)

    if not args.force:
        print(f"Delete {target}? Pass --force to confirm.", file=sys.stderr)
        sys.exit(1)

    conn.execute("DELETE FROM opportunities WHERE id = ?", (target,))
    conn.commit()
    conn.close()

    json.dump({"action": "deleted", "id": target}, sys.stdout, indent=2)
    print()


# --- Sessions ---

def cmd_save_session(args: argparse.Namespace) -> None:
    conn = get_db()
    mode = args.mode or "mine"
    if mode not in _VALID_SESSION_MODES:
        print(f"Error: invalid mode: {mode!r}", file=sys.stderr)
        sys.exit(1)

    ts = now_iso()
    # Generate session ID
    row = conn.execute("SELECT COUNT(*) as cnt FROM sessions").fetchone()
    count = row["cnt"] + 1
    session_id = f"SES-{count:04d}"

    conn.execute(
        """INSERT INTO sessions (id, mode, seed_query, source_filter,
           opportunities_found, wave_completed, status, started_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            session_id,
            mode,
            args.seed,
            args.source_filter,
            args.opportunities_found or 0,
            args.wave_completed or 0,
            "in_progress",
            ts,
        ),
    )
    conn.commit()
    conn.close()

    json.dump({"action": "saved", "id": session_id}, sys.stdout, indent=2)
    print()


def cmd_update_session(args: argparse.Namespace) -> None:
    conn = get_db()
    target = args.id

    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (target,)).fetchone()
    if row is None:
        print(f"Error: session not found: {target}", file=sys.stderr)
        sys.exit(1)

    updates: list[str] = []
    params: list = []

    if args.status:
        if args.status not in _VALID_SESSION_STATUSES:
            print(f"Error: invalid session status: {args.status!r}", file=sys.stderr)
            sys.exit(1)
        updates.append("status = ?")
        params.append(args.status)
        if args.status == "complete":
            updates.append("completed_at = ?")
            params.append(now_iso())

    if args.wave_completed is not None:
        updates.append("wave_completed = ?")
        params.append(args.wave_completed)

    if args.opportunities_found is not None:
        updates.append("opportunities_found = ?")
        params.append(args.opportunities_found)

    if not updates:
        print("Error: nothing to update.", file=sys.stderr)
        sys.exit(1)

    params.append(target)
    conn.execute(
        f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?",
        params,
    )
    conn.commit()
    conn.close()

    json.dump({"action": "updated", "id": target}, sys.stdout, indent=2)
    print()


def cmd_list_sessions(args: argparse.Namespace) -> None:
    conn = get_db()
    query = "SELECT * FROM sessions"
    params: list = []

    if args.status:
        query += " WHERE status = ?"
        params.append(args.status)

    query += " ORDER BY started_at DESC"
    rows = conn.execute(query, params).fetchall()
    result = [dict(r) for r in rows]
    conn.close()

    json.dump(result, sys.stdout, indent=2, default=str)
    print()


# --- Stats ---

def cmd_stats(args: argparse.Namespace) -> None:
    conn = get_db()

    # Check if tables exist
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = {r["name"] for r in tables}

    if "opportunities" not in table_names:
        json.dump({
            "total": 0,
            "by_status": {},
            "by_tier": {},
            "by_signal": {},
            "by_niche": {},
            "sessions": 0,
            "has_profile": False,
        }, sys.stdout, indent=2)
        print()
        conn.close()
        return

    total = conn.execute("SELECT COUNT(*) as cnt FROM opportunities").fetchone()["cnt"]

    by_status = {}
    for row in conn.execute("SELECT status, COUNT(*) as cnt FROM opportunities GROUP BY status"):
        by_status[row["status"]] = row["cnt"]

    by_tier = {}
    for row in conn.execute("SELECT triage_tier, COUNT(*) as cnt FROM opportunities GROUP BY triage_tier"):
        key = row["triage_tier"] or "unrated"
        by_tier[key] = row["cnt"]

    by_signal = {}
    for row in conn.execute("SELECT primary_signal, COUNT(*) as cnt FROM opportunities GROUP BY primary_signal"):
        by_signal[row["primary_signal"]] = row["cnt"]

    by_niche = {}
    niche_query = (
        "SELECT niche, COUNT(*) as cnt FROM opportunities "
        "GROUP BY niche ORDER BY cnt DESC LIMIT 10"
    )
    for row in conn.execute(niche_query):
        by_niche[row["niche"]] = row["cnt"]

    sessions = 0
    if "sessions" in table_names:
        sessions = conn.execute("SELECT COUNT(*) as cnt FROM sessions").fetchone()["cnt"]

    has_profile = False
    if "builder_profile" in table_names:
        has_profile = conn.execute("SELECT COUNT(*) as cnt FROM builder_profile").fetchone()["cnt"] > 0

    conn.close()

    json.dump({
        "total": total,
        "by_status": by_status,
        "by_tier": by_tier,
        "by_signal": by_signal,
        "by_niche": by_niche,
        "sessions": sessions,
        "has_profile": has_profile,
    }, sys.stdout, indent=2)
    print()


# --- Dedup check ---

def _normalize(text: str) -> set[str]:
    """Normalize text for dedup: lowercase, remove articles/punctuation, tokenize."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    words = text.split()
    stop = {"a", "an", "the", "for", "to", "of", "in", "on", "and", "or", "with", "by"}
    return {w for w in words if w not in stop}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cmd_dedup_check(args: argparse.Namespace) -> None:
    conn = get_db()

    title_words = _normalize(args.title)
    niche_words = _normalize(args.niche) if args.niche else set()

    rows = conn.execute("SELECT id, title, niche FROM opportunities").fetchall()
    conn.close()

    best_match = None
    best_score = 0.0

    for row in rows:
        existing_title_words = _normalize(row["title"])
        existing_niche_words = _normalize(row["niche"])

        # Niche must be somewhat related (or niche not provided)
        if niche_words:
            niche_sim = _jaccard(niche_words, existing_niche_words)
            if niche_sim < 0.3:
                continue

        title_sim = _jaccard(title_words, existing_title_words)
        if title_sim > best_score:
            best_score = title_sim
            best_match = {
                "id": row["id"],
                "title": row["title"],
                "niche": row["niche"],
                "similarity": round(title_sim, 3),
            }

    if best_match and best_score > 0.7:
        json.dump({"match": best_match}, sys.stdout, indent=2)
    else:
        json.dump({"match": None}, sys.stdout, indent=2)
    print()


# --- Profile ---

def cmd_profile_get(args: argparse.Namespace) -> None:
    conn = get_db()

    # Check table exists
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='builder_profile'"
    ).fetchall()
    if not tables:
        json.dump({"profile": None}, sys.stdout, indent=2)
        print()
        conn.close()
        return

    row = conn.execute("SELECT * FROM builder_profile WHERE id = 1").fetchone()
    conn.close()

    if row is None:
        json.dump({"profile": None}, sys.stdout, indent=2)
    else:
        profile = dict(row)
        # Parse JSON fields
        for field in ("tech_stack", "constraints", "interests", "avoid"):
            with contextlib.suppress(json.JSONDecodeError, TypeError):
                profile[field] = json.loads(profile[field])
        json.dump({"profile": profile}, sys.stdout, indent=2, default=str)
    print()


def cmd_profile_set(args: argparse.Namespace) -> None:
    conn = get_db()
    ts = now_iso()

    # Build fields
    fields = {"updated_at": ts}
    if args.tech_stack is not None:
        fields["tech_stack"] = args.tech_stack
    if args.constraints is not None:
        fields["constraints"] = args.constraints
    if args.time_budget is not None:
        fields["time_budget_hours_week"] = args.time_budget
    if args.revenue_goal is not None:
        fields["revenue_goal_mrr"] = args.revenue_goal
    if args.interests is not None:
        fields["interests"] = args.interests
    if args.avoid is not None:
        fields["avoid"] = args.avoid

    # Upsert
    existing = conn.execute("SELECT id FROM builder_profile WHERE id = 1").fetchone()
    if existing:
        sets = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(
            f"UPDATE builder_profile SET {sets} WHERE id = 1",
            list(fields.values()),
        )
    else:
        fields["id"] = 1
        cols = ", ".join(fields.keys())
        placeholders = ", ".join("?" for _ in fields)
        conn.execute(
            f"INSERT INTO builder_profile ({cols}) VALUES ({placeholders})",
            list(fields.values()),
        )

    conn.commit()
    conn.close()

    json.dump({"action": "profile_updated"}, sys.stdout, indent=2)
    print()


# --- Export ---

def cmd_export(args: argparse.Namespace) -> None:
    conn = get_db()
    fmt = args.format or "json"

    rows = conn.execute("SELECT * FROM opportunities ORDER BY created_at DESC").fetchall()
    opportunities = [dict(r) for r in rows]

    # Attach evidence
    for opp in opportunities:
        ev_rows = conn.execute(
            "SELECT * FROM evidence WHERE opportunity_id = ? ORDER BY id",
            (opp["id"],),
        ).fetchall()
        opp["evidence"] = [dict(r) for r in ev_rows]

    conn.close()

    if fmt == "json":
        json.dump(opportunities, sys.stdout, indent=2, default=str)
        print()
    elif fmt == "csv":
        if not opportunities:
            print("", end="")
            return
        # Flatten for CSV (exclude nested evidence)
        csv_fields = [
            "id", "title", "one_liner", "niche", "status", "primary_signal",
            "triage_tier", "triage_bootstrappability", "triage_pmf",
            "triage_competition", "triage_revenue", "triage_technical",
            "triage_moat", "mvp_days", "mvp_tech_stack", "panel_verdict",
            "session_id", "seed_query", "created_at", "updated_at",
        ]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        for opp in opportunities:
            writer.writerow(opp)
        sys.stdout.write(output.getvalue())
    else:
        print(f"Error: unsupported format: {fmt!r}", file=sys.stderr)
        sys.exit(1)


# --- Main ---

def main() -> None:
    ap = argparse.ArgumentParser(
        description="SQLite CRUD for prospector opportunities, evidence, sessions, and profile.",
    )
    sub = ap.add_subparsers(dest="command", required=True)

    # init
    sub.add_parser("init", help="Create database and tables.")

    # migrate
    sub.add_parser("migrate", help="Apply schema migrations.")

    # save-opportunity
    sp = sub.add_parser("save-opportunity", help="Save a new opportunity.")
    sp.add_argument("--title", required=True)
    sp.add_argument("--one-liner", dest="one_liner", default="")
    sp.add_argument("--niche", required=True)
    sp.add_argument("--signal", default="pain_no_solution")
    sp.add_argument("--triage", default=None, help="JSON object with triage dimensions.")
    sp.add_argument("--evidence", default=None, help="JSON array of evidence objects.")
    sp.add_argument("--counter-evidence", dest="counter_evidence", default=None)
    sp.add_argument("--session-id", dest="session_id", default="")
    sp.add_argument("--seed-query", dest="seed_query", default=None)
    sp.add_argument("--mvp-days", dest="mvp_days", type=int, default=None)
    sp.add_argument("--mvp-tech-stack", dest="mvp_tech_stack", default=None)
    sp.add_argument("--notes", default=None)

    # load
    sp = sub.add_parser("load", help="Load an opportunity with evidence.")
    sp.add_argument("id", help="OPP-XXXX or bare number.")

    # list
    sp = sub.add_parser("list", help="List opportunities.")
    sp.add_argument("--status", default=None)
    sp.add_argument("--tier", default=None)
    sp.add_argument("--niche", default=None)
    sp.add_argument("--limit", type=int, default=None)

    # update
    sp = sub.add_parser("update", help="Update an opportunity.")
    sp.add_argument("id", help="OPP-XXXX or bare number.")
    sp.add_argument("--status", default=None)
    sp.add_argument("--notes", default=None)
    sp.add_argument("--panel-json", dest="panel_json", default=None)

    # delete
    sp = sub.add_parser("delete", help="Delete an opportunity.")
    sp.add_argument("id", help="OPP-XXXX or bare number.")
    sp.add_argument("--force", action="store_true")

    # save-session
    sp = sub.add_parser("save-session", help="Save a new session.")
    sp.add_argument("--mode", default="mine")
    sp.add_argument("--seed", default=None)
    sp.add_argument("--source-filter", dest="source_filter", default=None)
    sp.add_argument("--wave-completed", dest="wave_completed", type=int, default=0)
    sp.add_argument("--opportunities-found", dest="opportunities_found", type=int, default=0)

    # update-session
    sp = sub.add_parser("update-session", help="Update a session.")
    sp.add_argument("id")
    sp.add_argument("--status", default=None)
    sp.add_argument("--wave-completed", dest="wave_completed", type=int, default=None)
    sp.add_argument("--opportunities-found", dest="opportunities_found", type=int, default=None)

    # list-sessions
    sp = sub.add_parser("list-sessions", help="List sessions.")
    sp.add_argument("--status", default=None)

    # stats
    sub.add_parser("stats", help="Aggregate stats.")

    # dedup-check
    sp = sub.add_parser("dedup-check", help="Check for duplicate opportunities.")
    sp.add_argument("--title", required=True)
    sp.add_argument("--niche", default=None)

    # profile-get
    sub.add_parser("profile-get", help="Get builder profile.")

    # profile-set
    sp = sub.add_parser("profile-set", help="Set builder profile.")
    sp.add_argument("--tech-stack", dest="tech_stack", default=None)
    sp.add_argument("--constraints", default=None)
    sp.add_argument("--time-budget", dest="time_budget", type=int, default=None)
    sp.add_argument("--revenue-goal", dest="revenue_goal", type=int, default=None)
    sp.add_argument("--interests", default=None)
    sp.add_argument("--avoid", default=None)

    # export
    sp = sub.add_parser("export", help="Export opportunities.")
    sp.add_argument("--format", default="json", choices=["json", "csv"])

    args = ap.parse_args()

    dispatch = {
        "init": cmd_init,
        "migrate": cmd_migrate,
        "save-opportunity": cmd_save_opportunity,
        "load": cmd_load,
        "list": cmd_list,
        "update": cmd_update,
        "delete": cmd_delete,
        "save-session": cmd_save_session,
        "update-session": cmd_update_session,
        "list-sessions": cmd_list_sessions,
        "stats": cmd_stats,
        "dedup-check": cmd_dedup_check,
        "profile-get": cmd_profile_get,
        "profile-set": cmd_profile_set,
        "export": cmd_export,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
