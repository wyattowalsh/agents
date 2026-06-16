#!/usr/bin/env python3
"""Emit config/external-skills.md as a legacy projection from authoring MDX (W6 compat)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import wagents  # noqa: E402
from wagents.skill_index import load_authoring_entries  # noqa: E402

STATUS_TO_HEADING = {
    "install-now-after-trust-gate": "Install Now After Trust Gate",
    "inspect-then-install": "Inspect Then Install",
    "global-only-or-avoid": "Keep Global Only Or Avoid",
}

HEADER = """# External Skills Install Set

> GENERATED from docs/src/authoring/skills/*.mdx — edit authoring MDX, then re-emit or run docs generate.

Approved external Agent Skill sources for this repo. Treat these as
trust-bearing assets: inspect source-list output, hooks, scripts, commands,
network access, credential handling, and dedupe before repo promotion.

Target agents for installs in this environment:

- `antigravity`
- `claude-code`
- `codex`
- `crush`
- `cursor`
- `gemini-cli`
- `github-copilot`
- `grok`
- `opencode`

Use this exact target suffix unless a user asks for a different target set:

```bash
-a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode
```

"""


def _group_entries(entries):
    groups: dict[str, list] = {k: [] for k in STATUS_TO_HEADING}
    for e in entries:
        if e.source_kind == "custom":
            continue
        status = e.status or "inspect-then-install"
        heading_key = status if status in STATUS_TO_HEADING else "inspect-then-install"
        groups.setdefault(heading_key, []).append(e)
    return groups


def emit_projection(*, out_path: Path | None = None, dry_run: bool = False) -> Path:
    entries = load_authoring_entries()
    groups = _group_entries(entries)
    lines = [HEADER.rstrip(), ""]
    for status, heading in STATUS_TO_HEADING.items():
        rows = sorted(groups.get(status, []), key=lambda e: e.name)
        if not rows:
            continue
        lines.append(f"## {heading}")
        lines.append("")
        for e in rows:
            if e.install_command:
                lines.append("```bash")
                lines.append(e.install_command)
                lines.append("```")
                lines.append("")
            note = (e.notes or e.body or "").strip()
            if note:
                for note_line in note.splitlines():
                    lines.append(note_line)
                lines.append("")
            elif e.status == "global-only-or-avoid":
                lines.append(f"- `{e.install_source or e.source}`: {e.unresolved_reason or e.notes or 'avoid'}")
                lines.append("")
    text = "\n".join(lines).rstrip() + "\n"
    target = out_path or wagents.ROOT / "config" / "external-skills.md"
    if dry_run:
        print(text[:2000])
        if len(text) > 2000:
            print(f"... ({len(text)} chars total, dry-run)")
        return target
    target.write_text(text, encoding="utf-8")
    print(f"Wrote {target}")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    emit_projection(out_path=args.out, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
