"""Tests for the Plannotator Grok exit-plan hook shim."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_SCRIPT = REPO_ROOT / "scripts" / "grok" / "plannotator-exit-plan-hook.py"


def test_exit_plan_hook_maps_block_to_deny(tmp_path):
    fake_plannotator = tmp_path / "plannotator"
    fake_plannotator.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        'json.dump({"decision": "block", "reason": "needs work"}, sys.stdout)\n',
        encoding="utf-8",
    )
    fake_plannotator.chmod(fake_plannotator.stat().st_mode | 0o111)

    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PLANNOTATOR_BIN": str(fake_plannotator)},
    )
    payload = json.loads(result.stdout)
    assert payload["decision"] == "deny"
    assert payload["reason"] == "needs work"


def test_exit_plan_hook_passes_through_non_block(tmp_path):
    fake_plannotator = tmp_path / "plannotator"
    fake_plannotator.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        'json.dump({"decision": "approve"}, sys.stdout)\n',
        encoding="utf-8",
    )
    fake_plannotator.chmod(fake_plannotator.stat().st_mode | 0o111)

    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PLANNOTATOR_BIN": str(fake_plannotator)},
    )
    payload = json.loads(result.stdout)
    assert payload["decision"] == "approve"