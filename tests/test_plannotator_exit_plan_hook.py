"""Tests for the Plannotator Grok exit-plan hook shim."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.parse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_SCRIPT = REPO_ROOT / "scripts" / "grok" / "plannotator-exit-plan-hook.py"

UUID_A = "019f5054-82f4-7f90-ad0b-09e419ee9883"
UUID_B = "019f5054-82f4-7f90-ad0b-09e419ee9884"


def _run_hook(
    *,
    stdin: str,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, **env},
    )


def _fake_plannotator(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "plannotator"
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o111)
    return path


def test_exit_plan_hook_maps_claude_permission_request_deny(tmp_path: Path) -> None:
    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "event = json.load(sys.stdin)\n"
        "assert event['tool_input']['plan'] == '# Plan'\n"
        "json.dump(\n"
        "  {'hookSpecificOutput': {'hookEventName': 'PermissionRequest',\n"
        "   'decision': {'behavior': 'deny', 'message': 'needs work'}}},\n"
        "  sys.stdout,\n"
        ")\n",
    )
    result = _run_hook(
        stdin=json.dumps(
            {
                "toolName": "exit_plan_mode",
                "toolInput": {"plan": "# Plan"},
                "sessionId": UUID_A,
            }
        ),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["decision"] == "deny"
    assert payload["reason"] == "needs work"


def test_exit_plan_hook_maps_block_to_deny(tmp_path: Path) -> None:
    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        'json.dump({"decision": "block", "reason": "needs work"}, sys.stdout)\n',
    )
    result = _run_hook(
        stdin=json.dumps({"toolName": "exit_plan_mode", "toolInput": {"plan": "# Plan"}}),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["decision"] == "deny"
    assert payload["reason"] == "needs work"


def test_exit_plan_hook_maps_allow(tmp_path: Path) -> None:
    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "json.dump(\n"
        "  {'hookSpecificOutput': {'decision': {'behavior': 'allow',\n"
        "   'updatedInput': {'plan': '# Plan'}}}},\n"
        "  sys.stdout,\n"
        ")\n",
    )
    result = _run_hook(
        stdin=json.dumps({"toolName": "exit_plan_mode", "toolInput": {"plan": "# Plan"}}),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["decision"] == "allow"


def test_exit_plan_hook_loads_plan_md_from_session_dir(tmp_path: Path) -> None:
    sessions = tmp_path / "sessions"
    cwd = "/Users/ww/dev/projects/agents"
    plan_path = sessions / urllib.parse.quote(cwd, safe="") / UUID_A / "plan.md"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text("# Session plan\n\nDo the thing.\n", encoding="utf-8")

    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "event = json.load(sys.stdin)\n"
        "assert 'Session plan' in event['tool_input']['plan']\n"
        "assert event['tool_name'] == 'ExitPlanMode'\n"
        "json.dump({'hookSpecificOutput': {'decision': {'behavior': 'allow'}}}, sys.stdout)\n",
    )
    result = _run_hook(
        stdin=json.dumps(
            {
                "hookEventName": "pre_tool_use",
                "toolName": "exit_plan_mode",
                "toolInput": {},
                "sessionId": UUID_A,
                "cwd": cwd,
            }
        ),
        env={
            "PLANNOTATOR_BIN": str(fake),
            "GROK_SESSIONS_DIR": str(sessions),
        },
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["decision"] == "allow"


def test_exit_plan_hook_allows_when_plan_missing(tmp_path: Path) -> None:
    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "sys.stderr.write('should not run')\n"
        "sys.exit(1)\n",
    )
    result = _run_hook(
        stdin=json.dumps(
            {
                "toolName": "exit_plan_mode",
                "toolInput": {},
                "sessionId": UUID_A,
                "cwd": str(tmp_path / "no-workspace"),
            }
        ),
        env={
            "PLANNOTATOR_BIN": str(fake),
            "GROK_SESSIONS_DIR": str(tmp_path / "empty-sessions"),
        },
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert "no plan content" in result.stderr


def test_exit_plan_hook_skips_non_exit_plan_tools(tmp_path: Path) -> None:
    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\nimport sys\nsys.exit(1)\n",
    )
    result = _run_hook(
        stdin=json.dumps({"toolName": "run_terminal_command", "toolInput": {"command": "ls"}}),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_plannotator_crash_empty_stdout_allows(tmp_path: Path) -> None:
    """RV-S-001: exit 2 + empty stdout must not deny (Grok treats exit 2 as deny)."""
    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\nimport sys\nsys.exit(2)\n",
    )
    result = _run_hook(
        stdin=json.dumps({"toolName": "exit_plan_mode", "toolInput": {"plan": "# Plan"}}),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert "empty stdout" in result.stderr


def test_no_global_plan_fallback_across_projects(tmp_path: Path) -> None:
    """RV-S-002: without session/cwd, never load another project's plan.md."""
    sessions = tmp_path / "sessions"
    foreign = sessions / urllib.parse.quote("/tmp/other-project", safe="") / UUID_B / "plan.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("# FOREIGN SECRET PLAN\n", encoding="utf-8")

    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "event = json.load(sys.stdin)\n"
        "sys.stderr.write('ran with plan')\n"
        "print(json.dumps({'decision': 'allow'}))\n",
    )
    result = _run_hook(
        stdin=json.dumps({"toolName": "exit_plan_mode", "toolInput": {}}),
        env={
            "PLANNOTATOR_BIN": str(fake),
            "GROK_SESSIONS_DIR": str(sessions),
        },
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert "no plan content" in result.stderr
    assert "ran with plan" not in result.stderr
    assert "FOREIGN" not in result.stdout


def test_cwd_scoped_newest_plan_ok(tmp_path: Path) -> None:
    """Same-cwd newest plan is allowed when session id is missing."""
    sessions = tmp_path / "sessions"
    cwd = "/Users/ww/dev/projects/agents"
    slug = sessions / urllib.parse.quote(cwd, safe="")
    old_plan = slug / UUID_A / "plan.md"
    new_plan = slug / UUID_B / "plan.md"
    old_plan.parent.mkdir(parents=True)
    new_plan.parent.mkdir(parents=True)
    old_plan.write_text("# OLD\n", encoding="utf-8")
    new_plan.write_text("# NEW cwd plan\n", encoding="utf-8")
    os.utime(old_plan, (1_000_000, 1_000_000))
    os.utime(new_plan, (2_000_000, 2_000_000))

    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "event = json.load(sys.stdin)\n"
        "assert 'NEW cwd plan' in event['tool_input']['plan']\n"
        "assert 'OLD' not in event['tool_input']['plan']\n"
        "print(json.dumps({'decision': 'allow'}))\n",
    )
    result = _run_hook(
        stdin=json.dumps(
            {
                "toolName": "exit_plan_mode",
                "toolInput": {},
                "cwd": cwd,
            }
        ),
        env={
            "PLANNOTATOR_BIN": str(fake),
            "GROK_SESSIONS_DIR": str(sessions),
        },
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["decision"] == "allow"


def test_unmapped_json_allows(tmp_path: Path) -> None:
    """RV-S-003: unmapped decision shape fail-opens (no raw passthrough)."""
    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\nimport json, sys\nprint(json.dumps({'foo': 1}))\n",
    )
    result = _run_hook(
        stdin=json.dumps({"toolName": "exit_plan_mode", "toolInput": {"plan": "# Plan"}}),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert "unmapped" in result.stderr


def test_non_json_stdout_allows(tmp_path: Path) -> None:
    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\nprint('not-json-output')\n",
    )
    result = _run_hook(
        stdin=json.dumps({"toolName": "exit_plan_mode", "toolInput": {"plan": "# Plan"}}),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert "non-JSON" in result.stderr


def test_unsafe_session_id_ignored(tmp_path: Path) -> None:
    """RV-S-004: path-like session ids must not be used for globs."""
    sessions = tmp_path / "sessions"
    # Would-be escape target if unsanitized
    trap = sessions / "trap" / "plan.md"
    trap.parent.mkdir(parents=True)
    trap.write_text("# TRAP\n", encoding="utf-8")

    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "sys.stderr.write('should not run')\n"
        "sys.exit(1)\n",
    )
    result = _run_hook(
        stdin=json.dumps(
            {
                "toolName": "exit_plan_mode",
                "toolInput": {},
                "sessionId": "../../trap",
                "cwd": str(tmp_path / "workspace"),
            }
        ),
        env={
            "PLANNOTATOR_BIN": str(fake),
            "GROK_SESSIONS_DIR": str(sessions),
        },
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert "unsafe session id" in result.stderr
    assert "should not run" not in result.stderr


def test_uuid_session_id_still_resolves(tmp_path: Path) -> None:
    sessions = tmp_path / "sessions"
    cwd = "/tmp/proj"
    plan_path = sessions / urllib.parse.quote(cwd, safe="") / UUID_A / "plan.md"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text("# uuid plan\n", encoding="utf-8")

    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "event = json.load(sys.stdin)\n"
        "assert 'uuid plan' in event['tool_input']['plan']\n"
        "print(json.dumps({'decision': 'allow'}))\n",
    )
    result = _run_hook(
        stdin=json.dumps(
            {
                "toolName": "exit_plan_mode",
                "toolInput": {},
                "sessionId": UUID_A,
                "cwd": cwd,
            }
        ),
        env={
            "PLANNOTATOR_BIN": str(fake),
            "GROK_SESSIONS_DIR": str(sessions),
        },
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["decision"] == "allow"
