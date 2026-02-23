#!/usr/bin/env python3
"""Progress tracking for skill creation/improvement sessions.

Manages session state at ~/.claude/skill-progress/{name}.json (portable,
user-scoped). Override with --state-dir for custom locations.
Subcommands: init, phase, agent, metric, status, audit, read, serve.
JSON to stdout, warnings to stderr. Atomic writes via temp+rename.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table as RichTable

    _RICH = True
except ImportError:
    _RICH = False

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

_DEFAULT_STATE_DIR = Path.home() / ".claude" / "skill-progress"


def _warn(msg: str) -> None:
    print(f"[progress] {msg}", file=sys.stderr)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _state_path(skill_name: str, state_dir: Path | None = None) -> Path:
    base = state_dir or _DEFAULT_STATE_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{skill_name}.json"


def _atomic_write(path: Path, data: dict) -> None:
    """Write JSON atomically via temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.rename(tmp, str(path))
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def _read_state(skill_name: str, state_dir: Path | None = None) -> dict:
    """Read existing session state or exit with error."""
    path = _state_path(skill_name, state_dir)
    if not path.is_file():
        _warn(f"No active session for '{skill_name}' at {path}")
        _warn(f"Initialize with: progress.py init --skill {skill_name} --mode create")
        sys.exit(1)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _warn(f"Corrupted state file at {path}: {exc}")
        _warn(f"To recover: delete {path} and reinitialize")
        sys.exit(1)
    except OSError as exc:
        _warn(f"Cannot read state: {exc}")
        sys.exit(1)


def _save_state(
    skill_name: str, state: dict, state_dir: Path | None = None
) -> None:
    """Save session state with updated timestamp."""
    state["updated_at"] = _now()
    _atomic_write(_state_path(skill_name, state_dir), state)


def _get_state_dir(args: argparse.Namespace) -> Path | None:
    """Extract state_dir from parsed args, if present."""
    return getattr(args, "state_dir", None)


# ---------------------------------------------------------------------------
# Rich output helpers
# ---------------------------------------------------------------------------

_STATUS_ICONS = {
    "completed": "[green]OK[/green]",
    "active": "[yellow]>>[/yellow]",
    "pending": "[dim]..[/dim]",
    "skipped": "[dim]--[/dim]",
    "failed": "[red]!![/red]",
}

_PLAIN_ICONS = {
    "completed": "[OK]",
    "active": "[>>]",
    "pending": "[..]",
    "skipped": "[--]",
    "failed": "[!!]",
}


def _render_rich_status(state: dict) -> None:
    """Render a rich panel with phase pipeline, wave status, and metrics."""
    console = Console()

    # Phase pipeline
    phase_lines = []
    for p in state.get("phases", []):
        icon = _STATUS_ICONS.get(p["status"], "[dim]??[/dim]")
        phase_lines.append(f"  {icon}  {p['label']} ({p['status']})")
    phase_text = "\n".join(phase_lines)

    # Wave status
    wave_lines = []
    for w in state.get("waves", []):
        icon = _STATUS_ICONS.get(w["status"], "[dim]??[/dim]")
        agent_summary = ", ".join(
            f"{a['id']}={a['status']}" for a in w.get("agents", [])
        )
        wave_lines.append(f"  {icon}  {w['label']} ({w['status']})")
        if agent_summary:
            wave_lines.append(f"       {agent_summary}")
    wave_text = "\n".join(wave_lines)

    # Metrics
    metrics = state.get("metrics", {})
    metric_table = RichTable(show_header=False, box=None, padding=(0, 2))
    metric_table.add_column("Key", style="bold")
    metric_table.add_column("Value")
    for k, v in metrics.items():
        if v is not None:
            metric_table.add_row(k, str(v))

    body = f"[bold]Phases[/bold]\n{phase_text}\n\n[bold]Waves[/bold]\n{wave_text}"
    console.print(
        Panel(
            body,
            title=f"[bold]{state.get('skill_name', '?')}[/bold] ({state.get('mode', '?')})",
            subtitle=f"status={state.get('status', '?')}",
        )
    )
    if any(v is not None for v in metrics.values()):
        console.print(metric_table)


def _render_plain_status(state: dict) -> None:
    """Render a plain-text status summary to stdout."""
    name = state.get("skill_name", "?")
    mode = state.get("mode", "?")
    status = state.get("status", "?")
    print(f"=== {name} ({mode}) | status={status} ===")

    print("\nPhases:")
    for p in state.get("phases", []):
        icon = _PLAIN_ICONS.get(p["status"], "[??]")
        print(f"  {icon} {p['label']} ({p['status']})")

    print("\nWaves:")
    for w in state.get("waves", []):
        icon = _PLAIN_ICONS.get(w["status"], "[??]")
        print(f"  {icon} {w['label']} ({w['status']})")
        for a in w.get("agents", []):
            a_icon = _PLAIN_ICONS.get(a["status"], "[??]")
            print(f"       {a_icon} {a['id']} ({a['status']})")

    metrics = state.get("metrics", {})
    non_null = {k: v for k, v in metrics.items() if v is not None}
    if non_null:
        print("\nMetrics:")
        for k, v in non_null.items():
            print(f"  {k}: {v}")


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> None:
    """Initialize a new progress session."""
    now = _now()
    session_id = args.session_id or f"{args.skill}-{now.replace(':', '-')}"
    sd = _get_state_dir(args)

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

    _atomic_write(_state_path(args.skill, sd), state)
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

    sd = _get_state_dir(args)
    state = _read_state(args.skill, sd)
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

    _save_state(args.skill, state, sd)
    json.dump(state, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_agent(args: argparse.Namespace) -> None:
    """Update an agent's status within a wave."""
    if args.status not in VALID_AGENT_STATUSES:
        _warn(f"Invalid status: {args.status}. Valid: {', '.join(sorted(VALID_AGENT_STATUSES))}")
        sys.exit(1)

    sd = _get_state_dir(args)
    state = _read_state(args.skill, sd)
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
            if not statuses:
                wave["status"] = "pending"
            elif "active" in statuses:
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

    _save_state(args.skill, state, sd)
    json.dump(state, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_metric(args: argparse.Namespace) -> None:
    """Update a metric value."""
    sd = _get_state_dir(args)
    state = _read_state(args.skill, sd)
    metrics = state["metrics"]

    key = args.key
    value = args.value

    if key not in metrics:
        _warn(f"Unknown metric key: {key}. Valid: {', '.join(sorted(metrics.keys()))}")
        sys.exit(1)

    # Handle incremental values (e.g., "+1")
    if value.startswith("+") and isinstance(metrics[key], (int, float, type(None))):
        try:
            delta = int(value[1:]) if "." not in value else float(value[1:])
            metrics[key] = (metrics[key] or 0) + delta
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
    elif isinstance(metrics[key], float):
        try:
            metrics[key] = float(value)
        except ValueError:
            _warn(f"Expected number for {key}, got: {value}")
            sys.exit(1)
    elif metrics[key] is None:
        # None — try numeric first, fall back to string
        try:
            metrics[key] = int(value) if "." not in value else float(value)
        except ValueError:
            metrics[key] = value
    else:
        # String — direct assignment
        metrics[key] = value

    _save_state(args.skill, state, sd)
    json.dump(state, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_audit(args: argparse.Namespace) -> None:
    """Inject audit results into the progress session."""
    sd = _get_state_dir(args)
    state = _read_state(args.skill, sd)

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

    _save_state(args.skill, state, sd)
    json.dump(state, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_status(args: argparse.Namespace) -> None:
    """Update session-level status."""
    if args.status not in VALID_SESSION_STATUSES:
        _warn(f"Invalid status: {args.status}. Valid: {', '.join(sorted(VALID_SESSION_STATUSES))}")
        sys.exit(1)

    sd = _get_state_dir(args)
    state = _read_state(args.skill, sd)
    state["status"] = args.status
    _save_state(args.skill, state, sd)
    json.dump(state, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_read(args: argparse.Namespace) -> None:
    """Read and print current session state."""
    sd = _get_state_dir(args)
    state = _read_state(args.skill, sd)

    fmt = getattr(args, "format", "json")
    if fmt == "status":
        if _RICH and sys.stdout.isatty():
            _render_rich_status(state)
        else:
            _render_plain_status(state)
    else:
        json.dump(state, sys.stdout, indent=2)
        sys.stdout.write("\n")


def cmd_serve(args: argparse.Namespace) -> None:
    """Serve the dashboard in a browser with current state."""
    import webbrowser

    sd = _get_state_dir(args)
    state = _read_state(args.skill, sd)

    # Find dashboard template
    script_dir = Path(__file__).resolve().parent
    template = script_dir.parent / "templates" / "dashboard.html"
    if not template.is_file():
        _warn(f"Dashboard template not found at {template}")
        sys.exit(1)

    # Create temp HTML with injected state
    html = template.read_text(encoding="utf-8")
    inject_script = (
        f"<script>window.__SKILL_DATA__ = {json.dumps(state)};</script>"
    )
    html = html.replace("</head>", f"{inject_script}\n</head>")

    # Write to temp file and open
    out_dir = Path(tempfile.mkdtemp(prefix="skill-dashboard-"))
    out_file = out_dir / "dashboard.html"
    out_file.write_text(html, encoding="utf-8")

    url = f"file://{out_file}"
    if not args.no_open:
        webbrowser.open(url)

    result = {
        "url": url,
        "state_file": str(_state_path(args.skill, sd)),
    }
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _add_state_dir(parser: argparse.ArgumentParser) -> None:
    """Add the --state-dir option to a subcommand parser."""
    parser.add_argument(
        "--state-dir", type=Path, default=None, help="Custom state directory"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Skill creation progress tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Initialize a new progress session")
    p_init.add_argument("--skill", required=True, help="Skill name")
    p_init.add_argument("--mode", required=True, choices=["create", "improve"])
    p_init.add_argument("--session-id", help="Custom session ID")
    _add_state_dir(p_init)

    # phase
    p_phase = sub.add_parser("phase", help="Update a phase status")
    p_phase.add_argument("--skill", required=True, help="Skill name")
    p_phase.add_argument("--phase", required=True, help="Phase ID")
    p_phase.add_argument("--status", required=True, help="New status")
    p_phase.add_argument("--notes", help="Phase notes")
    _add_state_dir(p_phase)

    # agent
    p_agent = sub.add_parser("agent", help="Update an agent status within a wave")
    p_agent.add_argument("--skill", required=True, help="Skill name")
    p_agent.add_argument("--wave", required=True, help="Wave ID")
    p_agent.add_argument("--agent", required=True, help="Agent ID")
    p_agent.add_argument("--status", required=True, help="New status")
    p_agent.add_argument("--summary", help="Agent output summary")
    _add_state_dir(p_agent)

    # metric
    p_metric = sub.add_parser("metric", help="Update a metric value")
    p_metric.add_argument("--skill", required=True, help="Skill name")
    p_metric.add_argument("--key", required=True, help="Metric key")
    p_metric.add_argument("--value", required=True, help="Metric value (prefix with + for increment)")
    _add_state_dir(p_metric)

    # status
    p_status = sub.add_parser("status", help="Update session-level status")
    p_status.add_argument("--skill", required=True, help="Skill name")
    p_status.add_argument("--status", required=True, help="New session status")
    _add_state_dir(p_status)

    # audit
    p_audit = sub.add_parser("audit", help="Inject audit results into session")
    p_audit.add_argument("--skill", required=True, help="Skill name")
    _add_state_dir(p_audit)

    # read
    p_read = sub.add_parser("read", help="Read current session state")
    p_read.add_argument("--skill", required=True, help="Skill name")
    p_read.add_argument(
        "--format",
        choices=["json", "status"],
        default="json",
        help="Output format (default: json)",
    )
    _add_state_dir(p_read)

    # serve
    p_serve = sub.add_parser("serve", help="Open dashboard in browser")
    p_serve.add_argument("--skill", required=True, help="Skill name")
    p_serve.add_argument("--no-open", action="store_true", help="Don't auto-open browser")
    _add_state_dir(p_serve)

    args = parser.parse_args()
    cmd = {
        "init": cmd_init,
        "phase": cmd_phase,
        "agent": cmd_agent,
        "metric": cmd_metric,
        "status": cmd_status,
        "audit": cmd_audit,
        "read": cmd_read,
        "serve": cmd_serve,
    }
    cmd[args.command](args)


if __name__ == "__main__":
    main()
