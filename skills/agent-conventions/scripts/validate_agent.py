#!/usr/bin/env python3
"""Validate agent frontmatter and optional README index coverage."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

KEBAB_CASE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def find_repo_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for path in [current, *current.parents]:
        if (path / "skills").is_dir():
            return path
    return None


def parse_frontmatter(content: str) -> tuple[dict, str]:
    if not content.startswith("---"):
        return {}, content
    match = re.search(r"\n---\s*\n", content[3:])
    if match is None:
        return {}, content
    end = 3 + match.start() + 1
    if yaml is None:
        raise RuntimeError("PyYAML is required: pip install pyyaml")
    try:
        frontmatter = yaml.safe_load(content[3:end].strip())
        if not isinstance(frontmatter, dict):
            frontmatter = {}
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML parse error: {exc}") from exc
    return frontmatter, content[end + 3 :].strip()


def validate_agent_file(agent_file: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    def add_error(message: str) -> None:
        errors.append({"source": str(agent_file), "message": message})

    try:
        content = agent_file.read_text(encoding="utf-8")
        frontmatter, _body = parse_frontmatter(content)

        if "name" not in frontmatter:
            add_error("missing required field 'name'")
        else:
            name = str(frontmatter["name"])
            if not KEBAB_CASE_PATTERN.match(name):
                add_error("name must be kebab-case")
            if name != agent_file.stem:
                add_error(f"name '{name}' doesn't match filename '{agent_file.stem}'")

        if "description" not in frontmatter:
            add_error("missing required field 'description'")
        elif not str(frontmatter["description"]).strip():
            add_error("description cannot be empty")
    except Exception as exc:
        add_error(str(exc))

    return errors


def find_readme_entries(agents_dir: Path) -> list[str]:
    readme = agents_dir / "README.md"
    if not readme.is_file():
        return []
    content = readme.read_text(encoding="utf-8", errors="replace")
    entries: list[str] = []
    for line in content.splitlines():
        match = re.match(r"^\|\s*`?([a-z0-9][a-z0-9-]*)`?\s*\|", line)
        if match:
            name = match.group(1).strip()
            if name and name != "name" and not re.match(r"^[-:]+$", name):
                entries.append(name)
    return sorted(entries)


def validate_index(agents_dir: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    agents = sorted(
        p.stem
        for p in agents_dir.glob("*.md")
        if p.stem.lower() != "readme" and not p.name.startswith(".")
    )
    entries = find_readme_entries(agents_dir)
    for name in agents:
        if name not in entries:
            errors.append(
                {
                    "source": str(agents_dir / "README.md"),
                    "message": f"agent '{name}' missing from README index table",
                }
            )
    for entry in entries:
        if entry not in agents:
            errors.append(
                {
                    "source": str(agents_dir / "README.md"),
                    "message": f"orphan README entry '{entry}' has no agent file",
                }
            )
    return errors


def validate_agents_dir(agents_dir: Path, *, check_index: bool) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if not agents_dir.is_dir():
        return [{"source": str(agents_dir), "message": "agents directory not found"}]

    for agent_file in sorted(agents_dir.glob("*.md")):
        if agent_file.stem.lower() == "readme":
            continue
        errors.extend(validate_agent_file(agent_file))

    if check_index:
        errors.extend(validate_index(agents_dir))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate agent definitions")
    parser.add_argument(
        "path",
        nargs="?",
        default="",
        help="Agent file or agents/ directory (default: repo agents/)",
    )
    parser.add_argument("--check-index", action="store_true", help="Also validate README.md index coverage")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    if args.path:
        target = Path(args.path).resolve()
    else:
        repo_root = find_repo_root()
        if repo_root is None:
            print("Could not find repo root", file=sys.stderr)
            return 1
        target = repo_root / "agents"

    if target.is_file():
        errors = validate_agent_file(target)
    else:
        errors = validate_agents_dir(target, check_index=args.check_index)

    if args.format == "json":
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    else:
        for error in errors:
            print(f"{error['source']}: {error['message']}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())