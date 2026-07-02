"""Guardrails for config-driven Python tooling (Ruff + ty SSOT)."""

from __future__ import annotations

import re
from pathlib import Path

from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]

# Legacy path-list invocations on ruff/ty commands (not other Python tooling).
FORBIDDEN_RUFF_TY_PATTERNS = [
    r"ruff check\s+wagents/",
    r"ruff format(?:\s+--check)?\s+wagents/",
    r"ruff check\s+tests/",
    r"ruff format(?:\s+--check)?\s+tests/",
    r"ty check\s+wagents/",
    r"ty check\s+tests/",
]


def _tooling_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if "ruff" in line or "ty check" in line]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_justfile_uses_config_driven_ruff_and_ty() -> None:
    justfile = _read(ROOT / "justfile")
    assert "uv run ruff check" in justfile
    assert "uv run ty check" in justfile
    for line in _tooling_lines(justfile):
        for pattern in FORBIDDEN_RUFF_TY_PATTERNS:
            assert not re.search(pattern, line), f"justfile hard-codes paths: {line.strip()}"


def test_ci_workflows_install_just_at_least_1_52() -> None:
    text = _read(ROOT / ".github" / "workflows" / "ci.yml")
    match = re.search(r"JUST_VERSION:\s*([0-9.]+)", text)
    assert match is not None, "ci.yml must pin JUST_VERSION for workflows job"
    assert Version(match.group(1)) >= Version("1.52.0")


def test_justfile_has_safe_default() -> None:
    justfile = _read(ROOT / "justfile")
    assert "set default-list := true" in justfile
    assert "minimum 1.52.0" in justfile
    default_idx = justfile.find("[default]")
    install_idx = justfile.find("\ninstall:")
    assert default_idx != -1, "justfile must declare a [default] recipe"
    assert install_idx != -1, "justfile must declare an install recipe"
    assert default_idx < install_idx, "[default] recipe must precede install recipe"


def test_ci_workflows_use_config_driven_ruff() -> None:
    for workflow in ("ci.yml", "release-skills.yml"):
        text = _read(ROOT / ".github" / "workflows" / workflow)
        assert "uv run ruff check" in text or "ruff check" in text
        for line in _tooling_lines(text):
            for pattern in FORBIDDEN_RUFF_TY_PATTERNS:
                assert not re.search(pattern, line), f"{workflow} hard-codes paths: {line.strip()}"


def test_precommit_ruff_hooks_have_no_path_args() -> None:
    text = _read(ROOT / ".pre-commit-config.yaml")
    assert "args: [check, wagents/" not in text
    assert "args: [wagents/" not in text
    assert "entry: uv run ruff check" in text
    assert "entry: uv run ruff format --check" in text
    assert "pass_filenames: false" in text


def test_pyproject_declares_ruff_and_ty_scope() -> None:
    text = _read(ROOT / "pyproject.toml")
    assert "[tool.ruff]" in text
    assert "include = [" in text
    assert "skills/**/scripts/**/*.py" in text
    assert "[tool.ty.src]" in text
    assert '"tests"' in text or "'tests'" in text


def test_doctor_reports_python_tooling_checks() -> None:
    from typer.testing import CliRunner

    from wagents.cli import app

    result = CliRunner().invoke(app, ["doctor", "--format", "json"])
    assert result.exit_code == 0, result.output
    import json

    payload = json.loads(result.output)
    names = {check["name"] for check in payload["checks"]}
    assert "python-tooling-config" in names
    assert "ruff-tooling" in names
    assert "ty-tooling" in names
