#!/usr/bin/env python3
"""Run the bundled structural/package gates and optional behavioral regressions."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PORTABLE_KEYS = frozenset({"name", "description", "license", "compatibility", "allowed-tools", "metadata"})


def portable_frontmatter() -> list[str]:
    """Enforce this skill's portable source contract, independent of its host."""
    import yaml

    raw = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    if not raw.startswith("---\n") or "\n---" not in raw[4:]:
        return ["SKILL.md requires YAML frontmatter"]
    try:
        metadata = yaml.safe_load(raw.split("---", 2)[1])
    except yaml.YAMLError as exc:
        return [f"Invalid YAML frontmatter: {exc}"]
    if not isinstance(metadata, dict):
        return ["Skill frontmatter must be a mapping"]
    return [f"Nonportable frontmatter key: {key}" for key in metadata if key not in PORTABLE_KEYS]


def run_check(name: str, command: list[str], *, timeout: int = 120) -> dict[str, object]:
    """Capture a check's exit status without obscuring a failed gate."""
    try:
        result = subprocess.run(command, cwd=SKILL_DIR, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"name": name, "passed": False, "error": str(exc)}
    return {
        "name": name,
        "passed": result.returncode == 0,
        "exit_code": result.returncode,
        "stdout": result.stdout[-16000:],
        "stderr": result.stderr[-4000:],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", action="store_true", help="Also run the packaged pytest behavioral suite")
    args = parser.parse_args(argv)
    if sys.version_info < (3, 13):  # noqa: UP036 - direct portable invocation may bypass project metadata
        print(json.dumps({"valid": False, "error": "Python 3.13+ required; run uv sync --locked"}))
        return 1
    dependencies = ["yaml", "pytest", "jsonschema"] if args.tests else ["yaml"]
    missing = [name for name in dependencies if importlib.util.find_spec(name) is None]
    if missing:
        print(
            json.dumps(
                {
                    "valid": False,
                    "error": f"Missing declared dependencies: {', '.join(missing)}",
                    "remedy": "Run uv sync --locked in the skill directory, then uv run python scripts/check.py --tests",
                }
            )
        )
        return 1

    checks: list[dict[str, object]] = []
    try:
        errors = portable_frontmatter()
        checks.append({"name": "portable-frontmatter", "passed": not errors, "errors": errors})
    except (OSError, UnicodeError) as exc:
        checks.append({"name": "portable-frontmatter", "passed": False, "error": str(exc)})

    toolkit = SKILL_DIR / "scripts" / "asset_toolkit"
    # The bundled gate is mandatory. A sibling checkout must not conceal a broken package.
    gates = [
        ("skill", toolkit / "validate_skill.py", []),
        ("evals", toolkit / "validate_evals.py", []),
        ("package", toolkit / "package.py", ["--dry-run"]),
    ]
    for name, script, flags in gates:
        if not script.is_file():
            checks.append({"name": name, "passed": False, "error": f"Missing bundled gate: {script.name}"})
        else:
            checks.append(run_check(name, [sys.executable, str(script), str(SKILL_DIR), *flags]))

    audit = SKILL_DIR.parent / "skill-creator" / "scripts" / "audit.py"
    if audit.is_file():
        checks.append(run_check("repository-audit", [sys.executable, str(audit), str(SKILL_DIR)]))
    if args.tests:
        checks.append(run_check("behavior", [sys.executable, "-m", "pytest", "tests", "-q"], timeout=300))
    valid = all(check["passed"] for check in checks)
    print(json.dumps({"valid": valid, "checks": checks}, indent=2))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
