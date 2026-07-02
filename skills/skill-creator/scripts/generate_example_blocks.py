#!/usr/bin/env python3
"""Generate Empty/Help Gallery example blocks for a skill dispatch table."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _extract_dispatch_examples(skill_md: Path) -> list[str]:
    text = skill_md.read_text(encoding="utf-8")
    skill_name = skill_md.parent.name
    examples: list[str] = []

    for match in re.finditer(r"`(/" + re.escape(skill_name) + r"[^`]*)`", text):
        examples.append(match.group(1))

    for match in re.finditer(r"`\$\{?ARGUMENTS\}?[^`]*`", text):
        _ = match
        continue

    # table rows with slash examples
    for match in re.finditer(r"\|\s*`?(/" + re.escape(skill_name) + r"[^|`\n]*)`?\s*\|", text):
        candidate = match.group(1).strip().strip("`")
        if candidate and candidate not in examples:
            examples.append(candidate)

    if not examples:
        examples = [f"/{skill_name}", f"/{skill_name} help"]
    return examples[:6]


def render_block(skill_name: str, examples: list[str]) -> str:
    lines = ["## Example Blocks", "", "When `$ARGUMENTS` is empty, show:"]
    for example in examples:
        lines.append(f"- `{example}`")
    lines.extend(
        [
            "",
            "State the write boundary and validation command for the skill.",
            "",
            "```bash",
            f"uv run python skills/{skill_name}/scripts/check.py",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate example blocks for a skill")
    parser.add_argument("name", help="kebab-case skill name")
    parser.add_argument("--apply", action="store_true", help="Append block to SKILL.md when missing")
    args = parser.parse_args(argv)

    skill_dir = REPO_ROOT / "skills" / args.name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        print(f"Missing {skill_md}", file=sys.stderr)
        return 1

    block = render_block(args.name, _extract_dispatch_examples(skill_md))
    print(block)

    if args.apply:
        text = skill_md.read_text(encoding="utf-8")
        if "## Example Blocks" in text:
            print("Example Blocks section already present; not modifying.", file=sys.stderr)
            return 0
        skill_md.write_text(text.rstrip() + "\n\n" + block, encoding="utf-8")
        print(f"Appended Example Blocks to {skill_md}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
