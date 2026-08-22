"""Tests for the Cursor Plannotator CreatePlan / SwitchMode hook shim."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_SCRIPT = REPO_ROOT / "scripts" / "cursor" / "plannotator-plan-hook.py"


def _run_hook(
    *,
    mode: str,
    stdin: str,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT), mode],
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


def test_create_plan_maps_claude_deny_to_cursor_permission(tmp_path: Path) -> None:
    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "event = json.load(sys.stdin)\n"
        "assert event['tool_name'] == 'ExitPlanMode'\n"
        "assert event['tool_input']['plan'] == '# Plan'\n"
        "json.dump(\n"
        "  {'hookSpecificOutput': {'hookEventName': 'PermissionRequest',\n"
        "   'decision': {'behavior': 'deny', 'message': 'needs work'}}},\n"
        "  sys.stdout,\n"
        ")\n",
    )
    result = _run_hook(
        mode="exit",
        stdin=json.dumps({"toolName": "CreatePlan", "toolInput": {"plan": "# Plan"}}),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["permission"] == "deny"
    assert payload["agent_message"] == "needs work"
    assert payload["user_message"] == "needs work"


def test_create_plan_maps_block_and_explicit_allow(tmp_path: Path) -> None:
    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        'json.dump({"decision": "block", "reason": "needs work"}, sys.stdout)\n',
    )
    denied = _run_hook(
        mode="exit",
        stdin=json.dumps({"tool_name": "create_plan", "tool_input": {"plan": "# Plan"}}),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert denied.returncode == 0
    assert json.loads(denied.stdout)["permission"] == "deny"

    fake = _fake_plannotator(
        tmp_path,
        '#!/usr/bin/env python3\nimport json, sys\njson.dump({"decision": "allow"}, sys.stdout)\n',
    )
    allowed = _run_hook(
        mode="exit",
        stdin=json.dumps({"toolName": "CreatePlan", "toolInput": {"overview": "# Overview only"}}),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert allowed.returncode == 0
    assert json.loads(allowed.stdout) == {"permission": "allow"}


def test_create_plan_missing_binary_and_empty_plan_fail_open(tmp_path: Path) -> None:
    missing = _run_hook(
        mode="exit",
        stdin=json.dumps({"toolName": "CreatePlan", "toolInput": {"plan": "# Plan"}}),
        env={"PLANNOTATOR_BIN": str(tmp_path / "missing-plannotator")},
    )
    assert missing.returncode == 0
    assert missing.stdout.strip() == ""

    fake = _fake_plannotator(tmp_path, "#!/usr/bin/env python3\nimport sys\nsys.exit(1)\n")
    empty = _run_hook(
        mode="exit",
        stdin=json.dumps({"toolName": "CreatePlan", "toolInput": {}}),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert empty.returncode == 0
    assert empty.stdout.strip() == ""


def test_create_plan_does_not_scan_other_plan_files(tmp_path: Path) -> None:
    decoy = tmp_path / "other-project" / "plan.md"
    decoy.parent.mkdir(parents=True)
    decoy.write_text("# Secret plan from another project\n", encoding="utf-8")
    called = tmp_path / "called"
    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\n"
        f"from pathlib import Path\n"
        f"Path({str(called)!r}).write_text('called', encoding='utf-8')\n"
        "raise SystemExit(1)\n",
    )
    result = _run_hook(
        mode="exit",
        stdin=json.dumps({
            "toolName": "CreatePlan",
            "toolInput": {},
            "cwd": str(decoy.parent),
        }),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert not called.exists()


def test_create_plan_crash_and_unmapped_json_fail_open_never_exit_2(tmp_path: Path) -> None:
    fake = _fake_plannotator(tmp_path, "#!/usr/bin/env python3\nimport sys\nsys.exit(1)\n")
    crashed = _run_hook(
        mode="exit",
        stdin=json.dumps({"toolName": "CreatePlan", "toolInput": {"plan": "# Plan"}}),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert crashed.returncode == 0
    assert crashed.stdout.strip() == ""

    fake = _fake_plannotator(
        tmp_path,
        '#!/usr/bin/env python3\nimport json, sys\njson.dump({"unexpected": true}, sys.stdout)\n',
    )
    unmapped = _run_hook(
        mode="exit",
        stdin=json.dumps({"toolName": "CreatePlan", "toolInput": {"plan": "# Plan"}}),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert unmapped.returncode == 0
    assert unmapped.stdout.strip() == ""


def test_switch_mode_enter_only_when_target_is_plan(tmp_path: Path) -> None:
    log = tmp_path / "argv.txt"
    fake = _fake_plannotator(
        tmp_path,
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"from pathlib import Path\n"
        f"Path({str(log)!r}).write_text(' '.join(sys.argv[1:]), encoding='utf-8')\n",
    )
    skipped = _run_hook(
        mode="enter",
        stdin=json.dumps({
            "toolName": "SwitchMode",
            "toolInput": {"target_mode_id": "agent"},
        }),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert skipped.returncode == 0
    assert skipped.stdout.strip() == ""
    assert not log.exists()

    entered = _run_hook(
        mode="enter",
        stdin=json.dumps({
            "tool_name": "SwitchMode",
            "tool_input": {"targetModeId": "plan"},
        }),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert entered.returncode == 0
    assert entered.stdout.strip() == ""
    assert log.read_text(encoding="utf-8") == "improve-context"


def test_unknown_mode_and_non_create_plan_tool_fail_open(tmp_path: Path) -> None:
    fake = _fake_plannotator(tmp_path, "#!/usr/bin/env python3\nimport sys\nsys.exit(1)\n")
    unknown = _run_hook(
        mode="review",
        stdin=json.dumps({"toolName": "CreatePlan", "toolInput": {"plan": "# Plan"}}),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert unknown.returncode == 0
    assert unknown.stdout.strip() == ""

    other = _run_hook(
        mode="exit",
        stdin=json.dumps({"toolName": "Shell", "toolInput": {"plan": "# Plan"}}),
        env={"PLANNOTATOR_BIN": str(fake)},
    )
    assert other.returncode == 0
    assert other.stdout.strip() == ""
