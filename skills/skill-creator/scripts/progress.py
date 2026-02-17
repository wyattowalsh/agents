#!/usr/bin/env python3
"""Progress tracking for skill creation/improvement sessions.

Manages session state at /tmp/skill-progress-{name}.json.
Subcommands: init, phase, agent, metric, audit, read.
JSON to stdout, warnings to stderr. Atomic writes via temp+rename.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PHASES = [
    {"id": "understand", "label": "Understand"},
    {"id": "plan", "label": "Plan"},
    {"id": "scaffold", "label": "Scaffold"},
    {"id": "build", "label": "Build"},
    {"id": "validate", "label": "Validate"},
    {"id": "iterate", "label": "Iterate"},
]

DEFAULT_WAVES = [
    {
        "id": "wave-1",
        "label": "Wave 1: Body",
        "phase": "build",
        "agents": [
            {"id": "agent-body", "task": "Write SKILL.md body", "area": "body"},
        ],
    },
    {
        "id": "wave-2",
        "label": "Wave 2: References + Scripts + Templates + Evals",
        "phase": "build",
        "agents": [
            {"id": "agent-refs", "task": "Write reference files", "area": "references"},
            {"id": "agent-scripts", "task": "Write scripts", "area": "scripts"},
            {"id": "agent-templates", "task": "Write templates", "area": "templates"},
            {"id": "agent-evals", "task": "Write evals", "area": "evals"},
        ],
    },
]

VALID_PHASE_IDS = {p["id"] for p in PHASES}
VALID_PHASE_STATUSES = {"pending", "active", "completed", "skipped", "failed"}
VALID_AGENT_STATUSES = {"pending", "active", "completed", "failed"}
VALID_SESSION_STATUSES = {"active", "completed", "failed"}


def _warn(msg: str) -> None:
    print(f"[progress] {msg}", file=sys.stderr)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _state_path(skill_name: str) -> Path:
    return Path(f"/tmp/skill-progress-{skill_name}.json")


def _atomic_write(path: Path, data: dict) -> None:
    """Write JSON atomically via temp file + rename."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.rename(tmp, str(path))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _read_state(skill_name: str) -> dict:
    """Read existing session state or exit with error."""
    path = _state_path(skill_name)
    if not path.is_file():
        _warn(f"No active session for '{skill_name}' at {path}")
        sys.exit(1)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        _warn(f"Cannot read state: {exc}")
        sys.exit(1)


def _save_state(skill_name: str, state: dict) -> None:
    """Save session state with updated timestamp."""
    state["updated_at"] = _now()
    _atomic_write(_state_path(skill_name), state)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> None:
    """Initialize a new progress session."""
    now = _now()
    session_id = args.session_id or f"{args.skill}-{now.replace(':', '-')}"

    phases = []
    for p in PHASES:
        status = "pending"
        # For improve mode, scaffold is pre-skipped
        if args.mode == "improve" and p["id"] == "scaffold":
            status = "skipped"
        phases.append({
            "id": p["id"],
            "label": p["label"],
            "status": status,
            "started_at": None,
            "completed_at": None,
            "notes": None,
            "artifacts": [],
        })

    waves = []
    for w in DEFAULT_WAVES:
        agents = []
        for a in w["agents"]:
            agents.append({
                **a,
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "output_summary": None,
            })
        waves.append({
            "id": w["id"],
            "label": w["label"],
            "phase": w["phase"],
            "status": "pending",
            "agents": agents,
        })

    state = {
        "session_id": session_id,
        "skill_name": args.skill,
        "mode": args.mode,
        "started_at": now,
        "updated_at": now,
        "status": "active",
        "phases": phases,
        "waves": waves,
        "plan_approval": {
            "required": args.mode == "improve",
            "approved": None,
            "approved_at": None,
        },
        "metrics": {
            "files_created": 0,
            "lines_written": 0,
            "patterns_applied": [],
            "baseline_score": None,
            "current_score": None,
            "current_grade": None,
            "iteration_count": 0,
        },
        "audit": None,
    }

    _atomic_write(_state_path(args.skill), state)
    json.dump(state, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_phase(args: argparse.Namespace) -> None:
    """Update a phase's status."""
    if args.phase not in VALID_PHASE_IDS:
        _warn(f"Invalid phase: {args.phase}. Valid: {', '.join(sorted(VALID_PHASE_IDS))}")
        sys.exit(1)
    if args.status not in VALID_PHASE_STATUSES:
        _warn(f"Invalid status: {args.status}. Valid: {', '.join(sorted(VALID_PHASE_STATUSES))}")
        sys.exit(1)

    state = _read_state(args.skill)
    now = _now()

    for phase in state["phases"]:
        if phase["id"] == args.phase:
            phase["status"] = args.status
            if args.status == "active" and phase["started_at"] is None:
                phase["started_at"] = now
            if args.status in ("completed", "skipped", "failed"):
                phase["completed_at"] = now
            if args.notes:
                phase["notes"] = args.notes
            break

    _save_state(args.skill, state)
    json.dump(state, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_agent(args: argparse.Namespace) -> None:
    """Update an agent's status within a wave."""
    if args.status not in VALID_AGENT_STATUSES:
        _warn(f"Invalid status: {args.status}. Valid: {', '.join(sorted(VALID_AGENT_STATUSES))}")
        sys.exit(1)

    state = _read_state(args.skill)
    now = _now()
    found = False

    for wave in state["waves"]:
        if wave["id"] == args.wave:
            for agent in wave["agents"]:
                if agent["id"] == args.agent:
                    agent["status"] = args.status
                    if args.status == "active" and agent["started_at"] is None:
                        agent["started_at"] = now
                    if args.status in ("completed", "failed"):
                        agent["completed_at"] = now
                    if args.summary:
                        agent["output_summary"] = args.summary
                    found = True
                    break
            # Auto-derive wave status from agents
            statuses = {a["status"] for a in wave["agents"]}
            if "active" in statuses:
                wave["status"] = "active"
            elif statuses == {"completed"}:
                wave["status"] = "completed"
            elif "failed" in statuses and "active" not in statuses and "pending" not in statuses:
                wave["status"] = "failed"
            elif "pending" not in statuses:
                wave["status"] = "completed"
            break

    if not found:
        _warn(f"Agent '{args.agent}' not found in wave '{args.wave}'")
        sys.exit(1)

    _save_state(args.skill, state)
    json.dump(state, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_metric(args: argparse.Namespace) -> None:
    """Update a metric value."""
    state = _read_state(args.skill)
    metrics = state["metrics"]

    key = args.key
    value = args.value

    if key not in metrics:
        _warn(f"Unknown metric key: {key}. Valid: {', '.join(sorted(metrics.keys()))}")
        sys.exit(1)

    # Handle incremental values (e.g., "+1")
    if isinstance(metrics[key], (int, float)) and value.startswith("+"):
        try:
            delta = int(value[1:]) if "." not in value else float(value[1:])
            metrics[key] = metrics[key] + delta
        except ValueError:
            _warn(f"Invalid incremental value: {value}")
            sys.exit(1)
    elif isinstance(metrics[key], list):
        # Append to list metrics (e.g., patterns_applied)
        metrics[key].append(value)
    elif isinstance(metrics[key], int):
        try:
            metrics[key] = int(value)
        except ValueError:
            _warn(f"Expected integer for {key}, got: {value}")
            sys.exit(1)
    elif isinstance(metrics[key], float) or (isinstance(metrics[key], (int, type(None))) and "." in value):
        try:
            metrics[key] = float(value)
        except ValueError:
            _warn(f"Expected number for {key}, got: {value}")
            sys.exit(1)
    else:
        # String or None — direct assignment
        metrics[key] = value

    _save_state(args.skill, state)
    json.dump(state, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_audit(args: argparse.Namespace) -> None:
    """Inject audit results into the progress session."""
    state = _read_state(args.skill)

    # Find and run audit.py
    script_dir = Path(__file__).resolve().parent
    audit_script = script_dir / "audit.py"
    if not audit_script.is_file():
        _warn(f"audit.py not found at {audit_script}")
        sys.exit(1)

    # Locate the skill directory
    skills_dir = script_dir.parent.parent
    skill_dir = skills_dir / args.skill
    if not skill_dir.is_dir():
        _warn(f"Skill directory not found: {skill_dir}")
        sys.exit(1)

    # Import and run audit
    import importlib.util
    spec = importlib.util.spec_from_file_location("audit", str(audit_script))
    audit_mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(audit_mod)  # type: ignore[union-attr]

    result = audit_mod.audit_skill(str(skill_dir))
    state["audit"] = result
    state["metrics"]["current_score"] = result.get("score")
    state["metrics"]["current_grade"] = result.get("grade")

    _save_state(args.skill, state)
    json.dump(state, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_read(args: argparse.Namespace) -> None:
    """Read and print current session state."""
    state = _read_state(args.skill)
    json.dump(state, sys.stdout, indent=2)
    sys.stdout.write("\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Skill creation progress tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Initialize a new progress session")
    p_init.add_argument("--skill", required=True, help="Skill name")
    p_init.add_argument("--mode", required=True, choices=["create", "improve"])
    p_init.add_argument("--session-id", help="Custom session ID")

    # phase
    p_phase = sub.add_parser("phase", help="Update a phase status")
    p_phase.add_argument("--skill", required=True, help="Skill name")
    p_phase.add_argument("--phase", required=True, help="Phase ID")
    p_phase.add_argument("--status", required=True, help="New status")
    p_phase.add_argument("--notes", help="Phase notes")

    # agent
    p_agent = sub.add_parser("agent", help="Update an agent status within a wave")
    p_agent.add_argument("--skill", required=True, help="Skill name")
    p_agent.add_argument("--wave", required=True, help="Wave ID")
    p_agent.add_argument("--agent", required=True, help="Agent ID")
    p_agent.add_argument("--status", required=True, help="New status")
    p_agent.add_argument("--summary", help="Agent output summary")

    # metric
    p_metric = sub.add_parser("metric", help="Update a metric value")
    p_metric.add_argument("--skill", required=True, help="Skill name")
    p_metric.add_argument("--key", required=True, help="Metric key")
    p_metric.add_argument("--value", required=True, help="Metric value (prefix with + for increment)")

    # audit
    p_audit = sub.add_parser("audit", help="Inject audit results into session")
    p_audit.add_argument("--skill", required=True, help="Skill name")
    p_audit.add_argument("--inject", action="store_true", required=True)

    # read
    p_read = sub.add_parser("read", help="Read current session state")
    p_read.add_argument("--skill", required=True, help="Skill name")

    args = parser.parse_args()
    cmd = {
        "init": cmd_init,
        "phase": cmd_phase,
        "agent": cmd_agent,
        "metric": cmd_metric,
        "audit": cmd_audit,
        "read": cmd_read,
    }
    cmd[args.command](args)


if __name__ == "__main__":
    main()
