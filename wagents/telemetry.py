"""Opt-in local telemetry for wagents command timings."""

from __future__ import annotations

import json
import os
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path

TELEMETRY_ENV = "WAGENTS_TELEMETRY"
DEFAULT_TELEMETRY_PATH = Path.home() / ".cache" / "wagents" / "telemetry.jsonl"


def telemetry_enabled() -> bool:
    return os.environ.get(TELEMETRY_ENV, "").strip() in {"1", "true", "yes", "on"}


def telemetry_path() -> Path:
    override = os.environ.get("WAGENTS_TELEMETRY_PATH", "").strip()
    if override:
        return Path(override).expanduser()
    return DEFAULT_TELEMETRY_PATH


@dataclass
class TelemetrySession:
    command: str
    started_at: float = field(default_factory=time.monotonic)
    failure_class: str | None = None

    def record(self, *, exit_code: int, failure_class: str | None = None) -> None:
        if not telemetry_enabled():
            return
        payload = {
            "command": self.command,
            "duration_ms": int((time.monotonic() - self.started_at) * 1000),
            "exit_code": exit_code,
            "failure_class": failure_class or self.failure_class,
        }
        path = telemetry_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")


_ACTIVE_SESSION: ContextVar[TelemetrySession | None] = ContextVar("wagents_telemetry_session", default=None)


def begin_command_telemetry(command: str) -> None:
    """Start timing for the active CLI invocation when telemetry is enabled."""
    if not telemetry_enabled():
        return
    _ACTIVE_SESSION.set(TelemetrySession(command=command))


def end_command_telemetry(result: int | None) -> None:
    """Record command duration and exit code from the Typer result callback."""
    session = _ACTIVE_SESSION.get()
    if session is None:
        return
    exit_code = 0 if result is None else int(result)
    failure_class = "env-error" if exit_code == 2 else None
    session.record(exit_code=exit_code, failure_class=failure_class)
    _ACTIVE_SESSION.set(None)


def doctor_telemetry_check() -> dict[str, str]:
    enabled = telemetry_enabled()
    path = telemetry_path()
    if not enabled:
        return {
            "name": "telemetry",
            "status": "ok",
            "summary": "Telemetry disabled (set WAGENTS_TELEMETRY=1 to opt in)",
        }
    return {
        "name": "telemetry",
        "status": "ok",
        "summary": f"Telemetry enabled; writing to {path}",
    }
