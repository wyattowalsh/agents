#!/usr/bin/env python3
"""Regenerate skills-plugins-review-shards.json for W0 scaffold."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wagents.docs_compose_upgrade_external import batch_composed_external_ids  # noqa: E402

OUT_PATH = ROOT / "planning" / "manifests" / "skills-plugins-review-shards.json"

W1_SHARD_SIZES = [8, 8, 7, 7, 7, 7, 7]
W3_CHUNK = 25

W1_VALIDATION_COMMANDS = [
    "uv run python scripts/check.py",
    "uv run python ../../skill-creator/scripts/audit.py . --format json",
    "uv run python ../../skill-creator/scripts/audit.py . --security --format json",
    "uv run wagents eval adequacy <name>",
    "uv run python ../../skill-creator/scripts/package.py . --dry-run",
]

W3_VALIDATION_COMMANDS = [
    "uv run wagents validate",
    "uv run python skills/review/scripts/source-audit.py --format json <source>",
    "npx skills add <install_source> --list",
]


def _repo_skill_ids() -> list[str]:
    skills_dir = ROOT / "skills"
    return sorted(p.name for p in skills_dir.iterdir() if p.is_dir())


def _build_w1_shards(skill_ids: list[str]) -> list[dict]:
    shards: list[dict] = []
    index = 0
    for shard_num, size in enumerate(W1_SHARD_SIZES, start=1):
        chunk = skill_ids[index : index + size]
        index += size
        shard_id = f"W1-skills-{shard_num:02d}"
        shards.append({
            "lane_id": "W1-skills",
            "shard_id": shard_id,
            "owner": f"subagent-w1-{shard_num:02d}",
            "skill_ids": chunk,
            "scope": [f"skills/{skill_id}/" for skill_id in chunk],
            "lens": ["skill-assets", "agentic"],
            "coverage": {"skills": len(chunk)},
            "validation_commands": W1_VALIDATION_COMMANDS,
            "status": "pending",
        })
    if index != len(skill_ids):
        msg = f"W1 split mismatch: assigned {index}, expected {len(skill_ids)}"
        raise ValueError(msg)
    return shards


def _build_w2_shards() -> list[dict]:
    return [
        {
            "lane_id": "W2-plugins",
            "shard_id": "L-plugin-manifests",
            "owner": "subagent-w2-manifests",
            "scope": [
                "agent-bundle.json",
                ".claude-plugin/plugin.json",
                ".claude-plugin/marketplace.json",
                ".codex-plugin/plugin.json",
                ".agents/plugins/marketplace.json",
                "docs/src/content/docs/harness-config/plugin-skill-ownership.mdx",
            ],
            "lens": ["supply-chain", "agentic", "docs"],
            "coverage": {"manifest_surfaces": 6},
            "validation_commands": [
                "uv run wagents validate",
                "uv run python scripts/sync_agent_stack.py --dry-run --targets repo",
            ],
            "status": "pending",
        },
        {
            "lane_id": "W2-plugins",
            "shard_id": "L-exposure-dedupe",
            "owner": "subagent-w2-exposure",
            "scope": [
                "wagents/installed_inventory.py",
                "planning/manifests/harness-reconciliation.json",
                "config/sync-manifest.json",
            ],
            "lens": ["agentic", "supply-chain", "docs"],
            "coverage": {"harnesses": "all"},
            "validation_commands": [
                "uv run wagents skills sync --dry-run --format json",
                "uv run wagents skills cleanup --dry-run --format json",
                "uv run python scripts/generate_harness_reconciliation.py",
            ],
            "status": "pending",
        },
        {
            "lane_id": "W2-plugins",
            "shard_id": "L-hook-projection",
            "owner": "subagent-w2-hooks",
            "scope": [
                "config/hook-registry.json",
                "hooks/wagents-hook.py",
                "wagents/hooks/render.py",
                "wagents/hooks/bundle.py",
                ".cursor/hooks.json",
            ],
            "lens": ["security", "agentic", "ci"],
            "coverage": {"harnesses": "all"},
            "validation_commands": [
                "uv run wagents hooks validate --harness all",
                "uv run python scripts/check_hook_discovery_parity.py",
            ],
            "status": "pending",
        },
    ]


def _build_w3_shards(catalog_ids: list[str]) -> list[dict]:
    shards: list[dict] = []
    for shard_num, start in enumerate(range(0, len(catalog_ids), W3_CHUNK), start=1):
        chunk = catalog_ids[start : start + W3_CHUNK]
        shard_id = f"W3-ext-{shard_num:02d}"
        shards.append({
            "lane_id": "W3-catalog-external",
            "shard_id": shard_id,
            "owner": f"subagent-w3-{shard_num:02d}",
            "catalog_ids": chunk,
            "scope": [f"docs/src/authoring/skills/{entry_id}.mdx" for entry_id in chunk],
            "lens": ["source/provenance", "supply-chain", "agentic"],
            "coverage": {"catalog_entries": len(chunk)},
            "validation_commands": W3_VALIDATION_COMMANDS,
            "status": "pending",
        })
    return shards


def build_manifest() -> dict:
    skill_ids = _repo_skill_ids()
    catalog_ids = batch_composed_external_ids()
    w1_shards = _build_w1_shards(skill_ids)
    w2_shards = _build_w2_shards()
    w3_shards = _build_w3_shards(catalog_ids)
    total_shards = len(w1_shards) + len(w2_shards) + len(w3_shards)
    return {
        "version": 1,
        "plan": "skills-plugins-review-swarm",
        "wave": "W0",
        "generated_at": date.today().isoformat(),
        "summary": {
            "w1_repo_skill_shards": len(w1_shards),
            "w1_repo_skills": len(skill_ids),
            "w2_plugin_lanes": len(w2_shards),
            "w3_external_shards": len(w3_shards),
            "w3_external_catalog_entries": len(catalog_ids),
            "total_shards": total_shards,
        },
        "shards": w1_shards + w2_shards + w3_shards,
    }


def main() -> int:
    manifest = build_manifest()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    summary = manifest["summary"]
    print(f"Wrote {OUT_PATH.relative_to(ROOT)}")
    print(
        f"W1={summary['w1_repo_skill_shards']} "
        f"W2={summary['w2_plugin_lanes']} "
        f"W3={summary['w3_external_shards']} "
        f"total={summary['total_shards']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
