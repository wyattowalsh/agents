#!/usr/bin/env python3
"""Generate scripts/check.py for a skill directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TEMPLATE = '''#!/usr/bin/env python3
"""Validate this skill's SKILL.md and eval manifests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent


def _toolkit_path() -> Path:
    bundled = SKILL_DIR / "scripts" / "asset_toolkit" / "validate_skill.py"
    if bundled.is_file():
        return SKILL_DIR / "scripts" / "asset_toolkit"
    repo_toolkit = SKILL_DIR.parent / "skill-creator" / "scripts" / "asset_toolkit"
    return repo_toolkit


def _run(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def main() -> int:
    toolkit = _toolkit_path()
    commands: list[list[str]] = [
        [sys.executable, str(toolkit / "validate_skill.py"), str(SKILL_DIR)],
    ]
    if (SKILL_DIR / "evals").is_dir():
        commands.append([sys.executable, str(toolkit / "validate_evals.py"), str(SKILL_DIR)])

    package_script = SKILL_DIR / "scripts" / "package.py"
    if not package_script.is_file():
        package_script = SKILL_DIR.parent / "skill-creator" / "scripts" / "package.py"
    if package_script.is_file():
        commands.append([sys.executable, str(package_script), str(SKILL_DIR), "--dry-run"])

    audit_script = SKILL_DIR.parent / "skill-creator" / "scripts" / "audit.py"
    if audit_script.is_file():
        commands.append([sys.executable, str(audit_script), str(SKILL_DIR)])

    exit_code = 0
    for command in commands:
        exit_code = _run(command) or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
'''

VALIDATION_CONTRACT = """
## Validation Contract

Run from this skill directory before declaring changes complete:

```bash
uv run python scripts/check.py
```

Completion criteria:

1. `uv run python scripts/check.py` exits 0.
2. No portable-CLI violations remain under this skill directory.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate scripts/check.py for a skill")
    parser.add_argument("--skill", required=True, help="Skill name under skills/")
    parser.add_argument("--apply", action="store_true", help="Write scripts/check.py")
    parser.add_argument("--dry-run", action="store_true", help="Print generated file")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[3]
    skill_dir = repo_root / "skills" / args.skill
    if not skill_dir.is_dir():
        print(f"Skill not found: {skill_dir}", file=sys.stderr)
        return 1

    output = skill_dir / "scripts" / "check.py"
    if args.dry_run or not args.apply:
        print(TEMPLATE)
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(TEMPLATE.strip() + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
