"""Diagnostics and conservative quarantine helpers for OpenCode sessions."""

from __future__ import annotations

import copy
import json
import os
import re
import sqlite3
import subprocess
import time
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote

DEFAULT_OPENCODE_STATE_DIR = Path.home() / ".local" / "share" / "opencode"
DEFAULT_OPENCODE_DB_PATH = DEFAULT_OPENCODE_STATE_DIR / "opencode.db"
DEFAULT_OPENCODE_LOG_DIR = DEFAULT_OPENCODE_STATE_DIR / "log"

REQUEST_ID_RE = re.compile(r"\brequest ID ([0-9a-fA-F-]{36})\b")
SESSION_ID_RE = re.compile(r"\bsession\.id=(ses_[A-Za-z0-9]+)\b")
FIELD_RE_TEMPLATE = r"\b{}=([^ ]+)"


def diagnose_session(
    *,
    request_id: str | None = None,
    session_ids: list[str] | None = None,
    db_path: Path = DEFAULT_OPENCODE_DB_PATH,
    log_dir: Path = DEFAULT_OPENCODE_LOG_DIR,
    quarantine: bool = False,
    apply: bool = False,
    backup_dir: Path | None = None,
    now_ms: int | None = None,
) -> dict[str, Any]:
    """Build a support-ready report and optionally archive selected OpenCode sessions.

    The default path is read-only. Mutating quarantine requires ``quarantine=True`` and
    ``apply=True``; before that mutation the SQLite database is copied with the
    SQLite backup API.
    """
    requested_session_ids = sorted(set(session_ids or []))
    events = collect_server_error_events(log_dir, request_id=request_id, session_ids=requested_session_ids)
    event_session_ids = sorted({event["session_id"] for event in events if event.get("session_id")})
    target_session_ids = sorted(set(requested_session_ids + event_session_ids))

    report: dict[str, Any] = {
        "db_path": str(db_path),
        "log_dir": str(log_dir),
        "request_id": request_id,
        "session_ids": target_session_ids,
        "server_error_events": events,
        "summary": summarize_events(events),
        "sessions": {},
        "processes": collect_opencode_processes(target_session_ids),
        "quarantine": {
            "requested": quarantine,
            "applied": False,
            "dry_run": not apply,
            "backup_path": None,
            "archived_sessions": [],
        },
        "recovery_notes": [
            "Preserve request IDs from server_error log lines before changing model defaults.",
            "Only archive the affected session after fresh pure and plugin-loaded gpt-5.5 runs succeed.",
            "Stop only processes tied to the affected session before applying quarantine.",
        ],
    }

    if db_path.exists() and target_session_ids:
        with connect_readonly(db_path) as conn:
            report["sessions"] = {session_id: inspect_session(conn, session_id) for session_id in target_session_ids}
    elif not db_path.exists():
        report["db_error"] = f"OpenCode database not found: {db_path}"

    if quarantine:
        if not target_session_ids:
            raise ValueError("quarantine requires --session-id or a --request-id found in OpenCode logs")
        if apply:
            backup_path = backup_opencode_db(db_path, backup_dir=backup_dir, now_ms=now_ms)
            archived_sessions = archive_sessions(db_path, target_session_ids, now_ms=now_ms)
            report["quarantine"] = {
                "requested": True,
                "applied": True,
                "dry_run": False,
                "backup_path": str(backup_path),
                "archived_sessions": archived_sessions,
            }
        else:
            report["quarantine"]["archived_sessions"] = target_session_ids

    return report


def collect_server_error_events(
    log_dir: Path,
    *,
    request_id: str | None = None,
    session_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Collect OpenAI ``server_error`` stream failures from OpenCode log files."""
    if not log_dir.exists():
        return []

    requested_sessions = set(session_ids or [])
    events: list[dict[str, Any]] = []
    for log_path in sorted(log_dir.glob("*.log")):
        with log_path.open(encoding="utf-8", errors="replace") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.rstrip("\n")
                if "server_error" not in line and (not request_id or request_id not in line):
                    continue
                event = parse_server_error_line(log_path, line_number, line)
                if not event:
                    continue
                if request_id and request_id not in event.get("request_ids", []):
                    continue
                if requested_sessions and event.get("session_id") not in requested_sessions:
                    continue
                events.append(event)
    return events


def parse_server_error_line(log_path: Path, line_number: int, line: str) -> dict[str, Any] | None:
    """Parse one OpenCode log line into a structured server-error event."""
    if "server_error" not in line:
        return None

    request_ids = REQUEST_ID_RE.findall(line)
    error_payload = parse_error_payload(line)
    error_payload_error = error_payload.get("error")
    nested_error: dict[str, Any] = error_payload_error if isinstance(error_payload_error, dict) else {}
    nested_provider_error = nested_error.get("error")
    provider_error: dict[str, Any] = nested_provider_error if isinstance(nested_provider_error, dict) else {}
    message = provider_error.get("message")
    if isinstance(message, str):
        request_ids = sorted(set(request_ids + REQUEST_ID_RE.findall(message)))

    return {
        "log_path": str(log_path),
        "line": line_number,
        "timestamp": parse_log_timestamp(line),
        "session_id": parse_session_id(line),
        "provider_id": parse_log_field(line, "providerID"),
        "model_id": parse_log_field(line, "modelID"),
        "agent": parse_log_field(line, "agent"),
        "mode": parse_log_field(line, "mode"),
        "request_ids": request_ids,
        "sequence_number": nested_error.get("sequence_number"),
        "error_type": provider_error.get("type") or nested_error.get("type"),
        "error_code": provider_error.get("code"),
        "message": message,
    }


def parse_error_payload(line: str) -> dict[str, Any]:
    """Return the JSON object immediately after ``error=`` in an OpenCode log line."""
    marker = "error="
    marker_index = line.find(marker)
    if marker_index == -1:
        return {}
    payload_text = line[marker_index + len(marker) :]
    try:
        payload, _end = json.JSONDecoder().raw_decode(payload_text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def parse_log_timestamp(line: str) -> str | None:
    parts = line.split(maxsplit=3)
    if len(parts) < 2:
        return None
    return parts[1]


def parse_session_id(line: str) -> str | None:
    match = SESSION_ID_RE.search(line)
    return match.group(1) if match else None


def parse_log_field(line: str, field: str) -> str | None:
    match = re.search(FIELD_RE_TEMPLATE.format(re.escape(field)), line)
    return match.group(1) if match else None


def summarize_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize server-error events by session, model, provider, and request ID."""
    request_ids = sorted({request_id for event in events for request_id in event.get("request_ids", [])})
    sessions = Counter(str(event["session_id"]) for event in events if event.get("session_id"))
    models = Counter(str(event["model_id"]) for event in events if event.get("model_id"))
    providers = Counter(str(event["provider_id"]) for event in events if event.get("provider_id"))
    timestamps = [event["timestamp"] for event in events if event.get("timestamp")]
    return {
        "event_count": len(events),
        "request_ids": request_ids,
        "sessions": dict(sessions),
        "models": dict(models),
        "providers": dict(providers),
        "first_timestamp": min(timestamps) if timestamps else None,
        "last_timestamp": max(timestamps) if timestamps else None,
    }


def inspect_session(conn: sqlite3.Connection, session_id: str) -> dict[str, Any]:
    """Inspect one OpenCode session from an already-open SQLite connection."""
    session = fetch_session(conn, session_id)
    if not session:
        return {"exists": False, "id": session_id}

    messages = fetch_json_rows(conn, "message", session_id)
    parts = fetch_json_rows(conn, "part", session_id)
    session_messages = fetch_json_rows(conn, "session_message", session_id)

    assistant_messages = [row for row in messages if row["data"].get("role") == "assistant"]
    incomplete_assistant_messages = [row for row in assistant_messages if not assistant_message_completed(row["data"])]
    part_type_counts = Counter(str(row["data"].get("type", "unknown")) for row in parts)
    encrypted_reasoning_parts = [row for row in parts if part_has_encrypted_reasoning(row["data"], row["raw_data"])]
    error_parts = [row for row in parts if row["data"].get("type") == "error" or "server_error" in row["raw_data"]]

    return {
        "exists": True,
        "session": session,
        "message_count": len(messages),
        "assistant_message_count": len(assistant_messages),
        "incomplete_assistant_message_count": len(incomplete_assistant_messages),
        "incomplete_assistant_message_ids": [row["id"] for row in incomplete_assistant_messages],
        "part_count": len(parts),
        "part_type_counts": dict(part_type_counts),
        "encrypted_reasoning_part_count": len(encrypted_reasoning_parts),
        "encrypted_reasoning_part_ids": [row["id"] for row in encrypted_reasoning_parts],
        "error_part_count": len(error_parts),
        "error_part_ids": [row["id"] for row in error_parts[:20]],
        "session_message_count": len(session_messages),
        "last_messages": summarize_rows(messages[-5:]),
        "last_parts": summarize_rows(parts[-8:]),
    }


def fetch_session(conn: sqlite3.Connection, session_id: str) -> dict[str, Any] | None:
    columns = table_columns(conn, "session")
    wanted = [
        column
        for column in [
            "id",
            "slug",
            "title",
            "directory",
            "version",
            "agent",
            "model",
            "time_created",
            "time_updated",
            "time_archived",
        ]
        if column in columns
    ]
    if not wanted:
        return None
    sql = f"SELECT {', '.join(wanted)} FROM session WHERE id = ?"
    row = conn.execute(sql, (session_id,)).fetchone()
    if row is None:
        return None
    result = dict(zip(wanted, row, strict=True))
    model = result.get("model")
    if isinstance(model, str):
        result["model"] = parse_json_object(model) or model
    return result


def fetch_json_rows(conn: sqlite3.Connection, table: str, session_id: str) -> list[dict[str, Any]]:
    if table not in {"message", "part", "session_message"}:
        raise ValueError(f"unsupported OpenCode table: {table}")
    columns = table_columns(conn, table)
    if not {"id", "session_id", "time_created", "time_updated", "data"}.issubset(columns):
        return []
    rows = conn.execute(
        f"SELECT id, time_created, time_updated, data FROM {table} WHERE session_id = ? ORDER BY time_created, id",
        (session_id,),
    ).fetchall()
    return [
        {
            "id": row[0],
            "time_created": row[1],
            "time_updated": row[2],
            "raw_data": row[3],
            "data": parse_json_object(row[3]) or {},
        }
        for row in rows
    ]


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for row in rows:
        data = row["data"]
        summary.append(
            {
                "id": row["id"],
                "time_created": row["time_created"],
                "time_updated": row["time_updated"],
                "role": data.get("role"),
                "type": data.get("type"),
                "finish": data.get("finish"),
            }
        )
    return summary


def assistant_message_completed(data: dict[str, Any]) -> bool:
    if data.get("role") != "assistant":
        return True
    time_data = data.get("time")
    has_completed_time = isinstance(time_data, dict) and time_data.get("completed") is not None
    return has_completed_time and data.get("finish") not in {None, "error"}


def part_has_encrypted_reasoning(data: dict[str, Any], raw_data: str) -> bool:
    metadata = data.get("metadata")
    openai_metadata = metadata.get("openai") if isinstance(metadata, dict) else None
    if isinstance(openai_metadata, dict) and "reasoningEncryptedContent" in openai_metadata:
        return True
    return "reasoningEncryptedContent" in raw_data or "reasoning.encrypted_content" in raw_data


def collect_opencode_processes(session_ids: list[str]) -> list[dict[str, Any]]:
    """Return running process commands that mention OpenCode and, when possible, the session ID."""
    try:
        result = subprocess.run(
            ["ps", "-axo", "pid=,command="],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []

    processes: list[dict[str, Any]] = []
    wanted_sessions = set(session_ids)
    ignored_pids = {os.getpid(), os.getppid()}
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        pid, _, command = stripped.partition(" ")
        process_id = int(pid)
        if process_id in ignored_pids or "wagents opencode diagnose-session" in command:
            continue
        if "opencode" not in command.lower():
            continue
        matched_sessions = sorted(session_id for session_id in wanted_sessions if session_id in command)
        if wanted_sessions and not matched_sessions:
            continue
        processes.append({"pid": process_id, "command": command, "session_ids": matched_sessions})
    return processes


def backup_opencode_db(db_path: Path, *, backup_dir: Path | None = None, now_ms: int | None = None) -> Path:
    """Create a consistent SQLite backup before mutating ``opencode.db``."""
    if not db_path.exists():
        raise FileNotFoundError(f"OpenCode database not found: {db_path}")
    timestamp = time.strftime("%Y%m%dT%H%M%S", time.localtime((now_ms or current_time_ms()) / 1000))
    destination_dir = backup_dir or db_path.parent
    destination_dir.mkdir(parents=True, exist_ok=True)
    backup_path = destination_dir / f"{db_path.name}.before-session-quarantine-{timestamp}"

    with sqlite3.connect(db_path) as source, sqlite3.connect(backup_path) as backup:
        source.backup(backup)
    return backup_path


def archive_sessions(db_path: Path, session_ids: list[str], *, now_ms: int | None = None) -> list[str]:
    """Set ``time_archived`` for selected OpenCode sessions."""
    archived_at = now_ms or current_time_ms()
    archived: list[str] = []
    with sqlite3.connect(db_path) as conn:
        for session_id in session_ids:
            cursor = conn.execute(
                "UPDATE session SET time_archived = ? WHERE id = ?",
                (archived_at, session_id),
            )
            if cursor.rowcount:
                archived.append(session_id)
        conn.commit()
    return archived


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    uri_path = quote(str(db_path.resolve()), safe="/")
    conn = sqlite3.connect(f"file:{uri_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(row["name"] if isinstance(row, sqlite3.Row) else row[1]) for row in rows}


def parse_json_object(raw: str) -> dict[str, Any] | None:
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def current_time_ms() -> int:
    return int(time.time() * 1000)


def redact_report_for_text(report: dict[str, Any]) -> dict[str, Any]:
    """Return a report copy with long encrypted payload details omitted for display."""
    redacted = copy.deepcopy(report)
    for session_report in redacted.get("sessions", {}).values():
        if not isinstance(session_report, dict):
            continue
        session_report.pop("last_parts", None)
        session_report.pop("last_messages", None)
    return redacted
