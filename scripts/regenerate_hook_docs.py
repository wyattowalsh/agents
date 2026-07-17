#!/usr/bin/env python3
"""Regenerate docs/src/content/docs/hooks/*.mdx from config/hook-registry.json.

Removes HAND-MAINTAINED freeze drift for fleet/research hook pages.
Does not rewrite hooks/index.mdx (hand-oriented hub).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "hook-registry.json"
HOOKS_DIR = ROOT / "docs" / "src" / "content" / "docs" / "hooks"


def _json_block(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False)


def render_hook_page(hook: dict) -> str:
    hook_id = str(hook.get("id") or "").strip()
    description = str(hook.get("description") or "").strip() or hook_id
    logical_event = str(hook.get("logical_event") or "").strip() or "unknown"
    matcher = hook.get("matcher")
    command = str(hook.get("command") or "").strip()
    timeout = hook.get("timeout")
    harnesses = hook.get("harnesses") or []
    mode = str(hook.get("mode") or "").strip()
    status_message = str(hook.get("status_message") or "").strip()
    bundle_group = str(hook.get("bundle_group") or "").strip()
    bundle_mode = str(hook.get("bundle_mode") or "").strip()
    logical_policy = str(hook.get("logical_policy") or "").strip()
    degraded = str(hook.get("degraded_behavior") or "").strip()

    harness_badges = " ".join(
        f'<Badge text="{h}" variant="default" />' for h in harnesses
    )
    event_badge = f'<Badge text="{logical_event}" variant="caution" />'
    mode_badge = f'<Badge text="{mode}" variant="tip" />' if mode else ""

    disclosure = {
        "id": hook_id,
        "description": description,
        "logical_event": logical_event,
        "logical_policy": logical_policy or None,
        "mode": mode or None,
        "status_message": status_message or None,
        "matcher": matcher,
        "command": command or None,
        "timeout": timeout,
        "bundle_group": bundle_group or None,
        "bundle_mode": bundle_mode or None,
        "degraded_behavior": degraded or None,
        "harnesses": harnesses,
    }
    disclosure = {k: v for k, v in disclosure.items() if v is not None and v != ""}

    table_rows = [
        ("id", f"`{hook_id}`"),
        ("logical_event", f"`{logical_event}`"),
        ("matcher", f"`{matcher}`" if matcher else "—"),
        ("command", f"`{command}`" if command else "—"),
        ("timeout", f"`{timeout}`" if timeout is not None else "—"),
        ("mode", f"`{mode}`" if mode else "—"),
        ("harnesses", f"`{_json_block(harnesses)}`" if harnesses else "—"),
    ]
    if bundle_group:
        table_rows.append(("bundle_group", f"`{bundle_group}`"))
    if bundle_mode:
        table_rows.append(("bundle_mode", f"`{bundle_mode}`"))
    if status_message:
        table_rows.append(("status_message", status_message))
    if degraded:
        table_rows.append(("degraded_behavior", degraded))

    table = "\n".join(f"| {k} | {v} |" for k, v in table_rows)

    return "\n".join(
        [
            "---",
            f'title: "{hook_id}"',
            f'description: "{description.replace(chr(34), chr(39))}"',
            'page_kind: "hook"',
            'source_kind: "registry"',
            f'asset_id: "{hook_id}"',
            "composed: true",
            'composed_at: "2026-07-10"',
            'composed_by: "regenerate-hook-docs-rv-006"',
            "docs_density: standard",
            "---",
            "",
            "{/* GENERATED from config/hook-registry.json — do not hand-edit */}",
            "",
            "import { Badge, CardGrid, LinkCard } from '@astrojs/starlight/components';",
            "",
            f"{event_badge} {mode_badge} {harness_badges}".strip(),
            "",
            f"> {description}",
            "",
            "## Registry Entry",
            "",
            "| Field | Value |",
            "|-------|-------|",
            table,
            "",
            '<details class="source-disclosure">',
            "<summary>Full hook config (registry SSOT)</summary>",
            "",
            '```json title="config/hook-registry.json (entry)"',
            _json_block(disclosure),
            "```",
            "",
            "Command placeholders:",
            "",
            "- `{hook_runner}` resolves to the fleet dispatcher (`hooks/wagents-hook.py` or harness projection).",
            "- `{harness}` is the target harness id at render/install time.",
            "",
            "</details>",
            "",
            "## Related",
            "",
            "<CardGrid>",
            '  <LinkCard title="Hooks hub" href="/hooks/" description="Registry overview and harness matrix." />',
            '  <LinkCard title="CLI hooks" href="/cli/" description="`wagents hooks list|validate`." />',
            "</CardGrid>",
            "",
        ]
    )


def main() -> int:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    hooks = data.get("hooks") or []
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for hook in hooks:
        hook_id = str(hook.get("id") or "").strip()
        if not hook_id or not re.fullmatch(r"[a-z0-9-]+", hook_id):
            continue
        path = HOOKS_DIR / f"{hook_id}.mdx"
        path.write_text(render_hook_page(hook), encoding="utf-8")
        written += 1
    print(f"Wrote {written} hook pages under {HOOKS_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
