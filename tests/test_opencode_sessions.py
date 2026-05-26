import json
import sqlite3
import subprocess
from pathlib import Path

from pytest import MonkeyPatch
from typer.testing import CliRunner

from wagents import opencode_sessions
from wagents.cli import app
from wagents.opencode_sessions import collect_opencode_processes, diagnose_session

REQUEST_ID = "8658ec5f-b93b-4245-b0c1-d1a8e8161dbe"
SESSION_ID = "ses_test123"


def write_sample_log(log_dir: Path) -> None:
    log_dir.mkdir()
    line = (
        "ERROR 2026-05-09T07:29:53 +9383ms service=llm providerID=openai modelID=gpt-5.5 "
        f"session.id={SESSION_ID} small=false agent=build mode=primary "
        'error={"error":{"type":"error","sequence_number":3,"error":{"type":"server_error",'
        f'"code":"server_error","message":"Please include the request ID {REQUEST_ID} in your message.",'
        '"param":null}}} stream error\n'
    )
    (log_dir / "2026-05-09T072739.log").write_text(line, encoding="utf-8")


def write_sample_db(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE session (
                id text PRIMARY KEY,
                slug text,
                title text,
                directory text,
                version text,
                agent text,
                model text,
                time_created integer,
                time_updated integer,
                time_archived integer
            );
            CREATE TABLE message (
                id text PRIMARY KEY,
                session_id text NOT NULL,
                time_created integer NOT NULL,
                time_updated integer NOT NULL,
                data text NOT NULL
            );
            CREATE TABLE part (
                id text PRIMARY KEY,
                message_id text NOT NULL,
                session_id text NOT NULL,
                time_created integer NOT NULL,
                time_updated integer NOT NULL,
                data text NOT NULL
            );
            CREATE TABLE session_message (
                id text PRIMARY KEY,
                session_id text NOT NULL,
                type text NOT NULL,
                time_created integer NOT NULL,
                time_updated integer NOT NULL,
                data text NOT NULL
            );
            """
        )
        conn.execute(
            """
            INSERT INTO session
            (id, slug, title, directory, version, agent, model, time_created, time_updated, time_archived)
            VALUES (?, 'quick-island', 'Exact OK reply', '/repo', '1.14.41', 'build', ?, 1, 2, NULL)
            """,
            (SESSION_ID, json.dumps({"id": "gpt-5.5", "providerID": "openai", "variant": "high"})),
        )
        conn.execute(
            "INSERT INTO message VALUES (?, ?, 10, 20, ?)",
            (
                "msg_assistant",
                SESSION_ID,
                json.dumps({"role": "assistant", "time": {"created": 10}, "modelID": "gpt-5.5"}),
            ),
        )
        conn.execute(
            "INSERT INTO part VALUES (?, ?, ?, 11, 12, ?)",
            (
                "prt_reasoning",
                "msg_assistant",
                SESSION_ID,
                json.dumps(
                    {
                        "type": "reasoning",
                        "metadata": {"openai": {"reasoningEncryptedContent": "encrypted"}},
                    }
                ),
            ),
        )
        conn.commit()


def test_diagnose_session_matches_request_id_and_inspects_db(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    db_path = tmp_path / "opencode.db"
    write_sample_log(log_dir)
    write_sample_db(db_path)

    report = diagnose_session(request_id=REQUEST_ID, db_path=db_path, log_dir=log_dir)

    assert report["summary"]["event_count"] == 1
    assert report["summary"]["request_ids"] == [REQUEST_ID]
    assert report["session_ids"] == [SESSION_ID]
    session_report = report["sessions"][SESSION_ID]
    assert session_report["session"]["model"]["variant"] == "high"
    assert session_report["incomplete_assistant_message_count"] == 1
    assert session_report["encrypted_reasoning_part_count"] == 1


def test_quarantine_is_dry_run_unless_apply_is_set(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    db_path = tmp_path / "opencode.db"
    backup_dir = tmp_path / "backups"
    write_sample_log(log_dir)
    write_sample_db(db_path)

    dry_report = diagnose_session(
        session_ids=[SESSION_ID],
        db_path=db_path,
        log_dir=log_dir,
        quarantine=True,
        apply=False,
    )

    assert dry_report["quarantine"]["dry_run"] is True
    assert dry_report["quarantine"]["backup_path"] is None
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT time_archived FROM session WHERE id = ?", (SESSION_ID,)).fetchone()[0] is None

    applied_report = diagnose_session(
        session_ids=[SESSION_ID],
        db_path=db_path,
        log_dir=log_dir,
        quarantine=True,
        apply=True,
        backup_dir=backup_dir,
        now_ms=1770000000000,
    )

    assert applied_report["quarantine"]["applied"] is True
    assert applied_report["quarantine"]["archived_sessions"] == [SESSION_ID]
    backup_path = Path(applied_report["quarantine"]["backup_path"])
    assert backup_path.exists()
    with sqlite3.connect(db_path) as conn:
        assert (
            conn.execute("SELECT time_archived FROM session WHERE id = ?", (SESSION_ID,)).fetchone()[0] == 1770000000000
        )
    with sqlite3.connect(backup_path) as conn:
        assert conn.execute("SELECT time_archived FROM session WHERE id = ?", (SESSION_ID,)).fetchone()[0] is None


def test_cli_emits_json_diagnosis(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    db_path = tmp_path / "opencode.db"
    write_sample_log(log_dir)
    write_sample_db(db_path)

    result = CliRunner().invoke(
        app,
        [
            "opencode",
            "diagnose-session",
            "--request-id",
            REQUEST_ID,
            "--db-path",
            str(db_path),
            "--log-dir",
            str(log_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["summary"]["event_count"] == 1


def test_parse_server_error_line_handles_bare_error_payload() -> None:
    line = (
        "ERROR 2026-05-09T07:29:53 +9383ms service=llm providerID=openai modelID=gpt-5.5 "
        f"session.id={SESSION_ID} small=false agent=build mode=primary "
        'error={"error":{"type":"error","sequence_number":3,"error":{"type":"server_error",'
        f'"code":"server_error","message":"Please include the request ID {REQUEST_ID} in your message.",'
        '"param":null}}}'
    )

    event = opencode_sessions.parse_server_error_line(Path("opencode.log"), 42, line)

    assert event is not None
    assert event["request_ids"] == [REQUEST_ID]
    assert event["sequence_number"] == 3
    assert event["error_type"] == "server_error"
    assert event["error_code"] == "server_error"


def test_cli_rejects_invalid_format_before_quarantine_mutates(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    db_path = tmp_path / "opencode.db"
    backup_dir = tmp_path / "backups"
    write_sample_log(log_dir)
    write_sample_db(db_path)

    result = CliRunner().invoke(
        app,
        [
            "opencode",
            "diagnose-session",
            "--session-id",
            SESSION_ID,
            "--db-path",
            str(db_path),
            "--log-dir",
            str(log_dir),
            "--quarantine",
            "--apply",
            "--backup-dir",
            str(backup_dir),
            "--format",
            "yaml",
        ],
    )

    assert result.exit_code == 1
    assert "unsupported format" in result.output
    assert not backup_dir.exists()
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT time_archived FROM session WHERE id = ?", (SESSION_ID,)).fetchone()[0] is None


def test_collect_opencode_processes_excludes_diagnostic_command(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(opencode_sessions.os, "getpid", lambda: 100)
    monkeypatch.setattr(opencode_sessions.os, "getppid", lambda: 99)

    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        stdout = "\n".join(
            [
                f" 99 uv run wagents opencode diagnose-session --session-id {SESSION_ID}",
                f"100 python -m wagents opencode diagnose-session --session-id {SESSION_ID}",
                f"200 opencode run --session {SESSION_ID}",
                "300 opencode run --session ses_other",
            ]
        )
        return subprocess.CompletedProcess(args=["ps"], returncode=0, stdout=stdout)

    monkeypatch.setattr(opencode_sessions.subprocess, "run", fake_run)

    assert collect_opencode_processes([SESSION_ID]) == [
        {"pid": 200, "command": f"opencode run --session {SESSION_ID}", "session_ids": [SESSION_ID]}
    ]
