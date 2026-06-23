#!/usr/bin/env python3
"""Emit compose-post-review shard manifest from composed_by frontmatter."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wagents.docs_compose_upgrade import RICH_HAND_CUSTOM, _wave_for_skill, batch_composed_custom_ids  # noqa: E402
from wagents.docs_compose_upgrade_external import _external_wave_for_skill, batch_composed_external_ids  # noqa: E402

COMPOSED_BY_RE = re.compile(r'^composed_by:\s*"?([^"\n]+)"?', re.M)
CUSTOM_DIR = ROOT / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "custom"
EXTERNAL_DIR = ROOT / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "external"
OUT_PATH = ROOT / "planning" / "manifests" / "compose-post-review-shards.json"


def _ids_by_wave(ids: list[str], wave_fn, batch_size: int) -> dict[str, list[str]]:
    waves: dict[str, list[str]] = {}
    for skill_id in ids:
        wave = wave_fn(skill_id, ids, batch_size)
        waves.setdefault(wave, []).append(skill_id)
    return waves


def _split_wave(wave_id: str, ids: list[str], *, chunk: int = 25) -> list[dict]:
    if len(ids) <= chunk:
        return [{"shard_id": wave_id, "skill_ids": ids, "count": len(ids)}]
    shards = []
    for index, start in enumerate(range(0, len(ids), chunk)):
        part = ids[start : start + chunk]
        suffix = chr(ord("a") + index)
        shards.append({
            "shard_id": f"{wave_id}-{suffix}",
            "skill_ids": part,
            "count": len(part),
        })
    return shards


def build_manifest() -> dict:
    custom_ids = batch_composed_custom_ids()
    external_ids = batch_composed_external_ids()
    custom_waves = _ids_by_wave(custom_ids, _wave_for_skill, 7)
    external_waves = _ids_by_wave(external_ids, _external_wave_for_skill, 25)

    custom_shards = []
    for wave in sorted(custom_waves):
        custom_shards.append({"shard_id": wave, "skill_ids": custom_waves[wave], "count": len(custom_waves[wave])})

    external_shards: list[dict] = []
    for wave in sorted(external_waves):
        ids = external_waves[wave]
        if wave in {"compose-external-wave-7", "compose-external-wave-8"} and len(ids) > 25:
            external_shards.extend(_split_wave(wave.replace("compose-external-wave-", "C-ext-"), ids))
        else:
            short = wave.replace("compose-external-wave-", "C-ext-")
            external_shards.append({"shard_id": short, "skill_ids": ids, "count": len(ids)})

    return {
        "generated_at": date.today().isoformat(),
        "ownership": {
            "integrator": ["wagents/docs.py"],
            "render": ["wagents/rendering.py"],
            "frontmatter": ["wagents/page_frontmatter.py"],
            "content_only": ["docs/src/content/docs/**"],
        },
        "custom": {"total": len(custom_ids), "shards": custom_shards},
        "external": {"total": len(external_ids), "shards": external_shards},
        "misc": {
            "agents": {"command": "docs compose --upgrade-agents", "count": 8},
            "mcp": {"command": "docs compose --upgrade-mcp", "ids": ["mcphub"]},
            "configs": {
                "command": "docs compose --regen-configs",
                "stems": ["mcp-registry", "sync-manifest", "tooling-policy"],
            },
            "rich_hand": {
                "command": "docs compose --enrich-rich-hand",
                "ids": sorted(RICH_HAND_CUSTOM),
                "count": len(RICH_HAND_CUSTOM),
            },
        },
    }


def main() -> int:
    manifest = build_manifest()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
