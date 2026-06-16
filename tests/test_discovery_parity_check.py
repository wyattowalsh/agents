"""Tests for discover-skills parity_check.py wrapper."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "discover-skills" / "scripts"


def _load():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    path = SCRIPTS / "parity_check.py"
    spec = importlib.util.spec_from_file_location("parity_check", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_parity_check_delegates_to_repo_script() -> None:
    mod = _load()
    proc = MagicMock()
    proc.returncode = 0

    with patch.object(mod.subprocess, "run", return_value=proc) as run:
        code = mod.main(["--repo-root", str(ROOT)])

    assert code == 0
    run.assert_called_once()
    cmd = run.call_args.args[0]
    assert str(ROOT / "scripts" / "check_discovery_parity.py") in cmd[1]


def test_parity_check_missing_script_returns_one(tmp_path: Path) -> None:
    mod = _load()
    code = mod.main(["--repo-root", str(tmp_path)])
    assert code == 1